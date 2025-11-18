import os
import logging
from PyQt6.QtCore import QTimer, QTime, QObject, pyqtSignal, QThreadPool, QDate
from base_de_datos.db_worker import DbTask
import random

class Evento:
    """Clase para representar un evento de salida/llegada de tren"""
    def __init__(self, asignacion_id, horario_id, tipo, hora_programada, ruta_id=None, tren_id=None, duracion_estimada=None):
        self.asignacion_id = asignacion_id
        self.horario_id = horario_id
        self.tipo = tipo  # 'SALIDA' o 'LLEGADA'
        self.hora_programada = hora_programada  # QTime
        self.ruta_id = ruta_id
        self.tren_id = tren_id
        self.duracion_estimada = duracion_estimada  # Para eventos de llegada
        self.hora_ejecucion = None  # Se calcula al programar

class EventManager(QObject):
    """Gestor centralizado de eventos de trenes"""
    update_triggered = pyqtSignal()
    # Señal auxiliar con motivo textual; opcional para vistas que quieran diferenciar el origen.
    update_reason = pyqtSignal(str)
    
    def __init__(self, db_connection, usuario_id=1, auto_start: bool = True):
        super().__init__()
        self.log = logging.getLogger('APP.event_manager')
        self.db = db_connection
        self.usuario_id = usuario_id  # ID del usuario actual
        self.eventos_pendientes = []  # Lista ordenada de eventos futuros
        # Timer único para programar el próximo evento
        self._schedule_timer = None
        self._scheduled_key = None
        # Guardas de estado
        self._running_event = False
        self._current_date = QDate.currentDate()  # Para detectar cambio de día
        # Configuración avanzada de catch-up/backfill
        self._catchup_mode = os.getenv('APP_EVENTS_CATCHUP_MODE', 'none').lower()  # none|window|all|schedule-only
        try:
            self._catchup_mins = max(0, int(os.getenv('APP_EVENTS_CATCHUP_MINS', '0')))
        except Exception:
            self._catchup_mins = 0
        try:
            self._batch_size = max(1, int(os.getenv('APP_EVENTS_BATCH_SIZE', '5')))
        except Exception:
            self._batch_size = 5
        try:
            self._batch_delay_ms = max(0, int(os.getenv('APP_EVENTS_BATCH_DELAY_MS', '750')))
        except Exception:
            self._batch_delay_ms = 750
        self._batch_count = 0
        self._batch_delay_timer = None
        # Métricas básicas
        self._metrics = {
            'total': 0,
            'salidas': 0,
            'llegadas': 0,
            'resets': 0,
            'errores': 0,
            'last_event_at': None,
        }
        # Thread pool para ejecutar tareas de BD
        self.thread_pool = QThreadPool.globalInstance()
        try:
            max_threads = getattr(self.db, 'pool_max', 5)
            self.thread_pool.setMaxThreadCount(max_threads)
        except Exception:
            pass

        # Configuración de simulación de retrasos (salidas/llegadas)
        # APP_DELAY_ENABLED: '1'/'true' para activar (por defecto activado)
        # APP_DELAY_MODE: 'threshold' (por defecto) | 'prob'
        #   - threshold: randint(0..MAX) y si > THRESHOLD, se usa ese valor como retraso
        #   - prob: con PROB (0..1) hay retraso de randint(1..MAX), si no 0
        # APP_DELAY_MAX_MINUTES: máximo minutos de retraso (default 15)
        # APP_DELAY_THRESHOLD: umbral (default 5)
        # APP_DELAY_PROB: probabilidad (0..1) para modo 'prob' (default 0.35)
        try:
            self._delay_enabled = os.getenv('APP_DELAY_ENABLED', '1').lower() in ('1', 'true', 'yes')
            self._delay_mode = os.getenv('APP_DELAY_MODE', 'threshold').lower()
            self._delay_max = max(0, int(os.getenv('APP_DELAY_MAX_MINUTES', '15')))
            self._delay_threshold = max(0, int(os.getenv('APP_DELAY_THRESHOLD', '1')))
            self._delay_prob = min(1.0, max(0.0, float(os.getenv('APP_DELAY_PROB', '0.35'))))
        except Exception:
            self._delay_enabled = True
            self._delay_mode = 'threshold'
            self._delay_max = 15
            self._delay_threshold = 1
            self._delay_prob = 0.35
        
        # Configurar timer de verificación periódica
        self.verification_timer = QTimer()
        self.verification_timer.timeout.connect(self.verificar_eventos)
        if auto_start:
            self.verification_timer.start(60000)  # 1 minuto
        
        # Cargar eventos iniciales si aplica
        if auto_start:
            self.cargar_eventos_futuros()

        # Registrar referencia en db si es posible (coordinación con db)
        try:
            if not hasattr(self.db, 'event_manager') or getattr(self.db, 'event_manager') is None:
                setattr(self.db, 'event_manager', self)
        except Exception:
            pass

    def cargar_eventos_futuros(self):
        """Carga eventos del día a partir de una hora mínima configurable.
        Por defecto, solo futuros (min_time = ahora). Si APP_EVENTS_CATCHUP_MINS>0, incluye vencidos en esa ventana.
        """
        self.log.info("Cargando eventos del día...")

        # Calcular hora mínima a considerar según modo de catch-up
        ahora = QTime.currentTime()
        mode = self._catchup_mode
        if mode == 'none':
            min_time = ahora
        elif mode == 'window':
            min_time = ahora.addSecs(-60 * self._catchup_mins) if self._catchup_mins > 0 else ahora
            if not min_time.isValid():
                min_time = QTime(0, 0, 0)
        elif mode in ('all', 'schedule-only'):
            min_time = QTime(0, 0, 0)
        else:
            # fallback seguro
            min_time = ahora
        min_time_str = min_time.toString('HH:mm:ss')
        query = """
        WITH eventos AS (
            -- Eventos de SALIDA
            SELECT 
                a.ID_ASIGNACION,
                a.ID_HORARIO,
                'SALIDA' AS TIPO,
                TO_CHAR(h.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS HORA_EVENTO,
                a.ID_RUTA,
                a.ID_TREN,
                NULL AS DURACION
            FROM ASIGNACION_TREN a
            JOIN HORARIO h ON a.ID_HORARIO = h.ID_HORARIO
            WHERE a.HORA_SALIDA_REAL IS NULL
            AND TO_CHAR(h.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') >= :min_time
            
            UNION ALL
            
            -- Eventos de LLEGADA
            SELECT 
                a.ID_ASIGNACION,
                a.ID_HORARIO,
                'LLEGADA' AS TIPO,
                TO_CHAR(h.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS HORA_EVENTO,
                a.ID_RUTA,
                a.ID_TREN,
                r.DURACION_ESTIMADA AS DURACION
            FROM ASIGNACION_TREN a
            JOIN HORARIO h ON a.ID_HORARIO = h.ID_HORARIO
            JOIN RUTA r ON a.ID_RUTA = r.ID_RUTA
            WHERE a.HORA_LLEGADA_REAL IS NULL
            AND a.HORA_SALIDA_REAL IS NOT NULL
            AND TO_CHAR(h.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') >= :min_time
        )
        SELECT * FROM eventos
        ORDER BY HORA_EVENTO ASC
        """

        resultados = self.db.fetch_all(query, {'min_time': min_time_str})
        self.eventos_pendientes = []
        
        for res in resultados:
            hora_evento = QTime.fromString(res[3], "HH:mm:ss")
            if not hora_evento.isValid():
                continue
            evento = Evento(
                asignacion_id=res[0],
                horario_id=res[1],
                tipo=res[2],
                hora_programada=hora_evento,
                ruta_id=res[4],
                tren_id=res[5],
                duracion_estimada=res[6] if res[2] == 'LLEGADA' else None
            )
            self.eventos_pendientes.append(evento)
            self.log.debug(f"Evento cargado: {evento.tipo} asignación={evento.asignacion_id} hora={hora_evento.toString('HH:mm:ss')}")

        # Asegurar orden ascendente por hora
        self.eventos_pendientes.sort(key=lambda ev: ev.hora_programada)
        self.log.info(f"Total eventos pendientes: {len(self.eventos_pendientes)}")
        
        self.programar_proximo_evento()

    def programar_proximo_evento(self):
        """Programa el temporizador para el próximo evento con verificación de lista vacía"""
        # Si hay un evento ejecutándose, evitamos programar para no generar intentos redundantes
        if self._running_event:
            self.log.debug("Se omite programación: hay un evento en curso.")
            return
        # Si no hay eventos, no programamos nada específico; el verificador periódico se encargará.
        if not self.eventos_pendientes:
            self._scheduled_key = None
            self.log.info("No hay eventos pendientes. Esperando al verificador periódico...")
            return
        
        # Si el modo es 'schedule-only', descartamos vencidos y buscamos el primer futuro
        if self._catchup_mode == 'schedule-only':
            ahora = QTime.currentTime()
            dropped = 0
            while self.eventos_pendientes and ahora.msecsTo(self.eventos_pendientes[0].hora_programada) <= 0:
                self.eventos_pendientes.pop(0)
                dropped += 1
            if dropped:
                self.log.info(f"Modo schedule-only: se omitieron {dropped} eventos vencidos.")
            if not self.eventos_pendientes:
                self._scheduled_key = None
                return
        
        evento = self.eventos_pendientes[0]
        ahora = QTime.currentTime()
        ms_hasta_evento = ahora.msecsTo(evento.hora_programada)
        
        if ms_hasta_evento <= 0:
            # El evento debería haber ocurrido ya
            self.log.debug("Evento vencido detectado; ejecutando inmediatamente.")
            self.ejecutar_evento(evento)
        else:
            key = (evento.tipo, evento.asignacion_id, evento.hora_programada.toString('HH:mm:ss'))
            if self._schedule_timer is None:
                self._schedule_timer = QTimer()
                self._schedule_timer.setSingleShot(True)
                # Conectar a un wrapper que revalide el primer elemento al disparar
                self._schedule_timer.timeout.connect(self._on_schedule_timeout)
            # Si el evento programado no cambia, no recreamos el timer
            if self._scheduled_key == key and self._schedule_timer.isActive():
                self.log.debug("Timer ya programado para el mismo evento; no se reprograma.")
                return
            self._scheduled_key = key
            self.log.info(f"Programando próximo evento: {evento.tipo} a las {evento.hora_programada.toString('HH:mm:ss')} (en {ms_hasta_evento} ms)")
            self._schedule_timer.start(ms_hasta_evento)

    def _on_schedule_timeout(self):
        """Callback del timer de programación: toma el primer evento actual y lo ejecuta si aplica."""
        if not self.eventos_pendientes:
            self._scheduled_key = None
            return
        evento = self.eventos_pendientes[0]
        key = (evento.tipo, evento.asignacion_id, evento.hora_programada.toString('HH:mm:ss'))
        # Evitar disparos obsoletos si cambió el primer evento
        if self._scheduled_key is not None and key != self._scheduled_key:
            self.log.debug("El evento programado cambió; se reprogramará.")
            self.programar_proximo_evento()
            return
        self.ejecutar_evento(evento)

    def ejecutar_evento(self, evento):
        """Ejecuta el evento (salida o llegada) con manejo seguro de lista vacía"""
        try:
            if self._running_event:
                # Silenciar advertencia: este caso es esperado en ráfagas simultáneas, no es un error
                self.log.debug("Intento de ejecución mientras otra está en curso; se omite (ráfaga).")
                return
            self._running_event = True
            self.log.info(f"Ejecutando evento {evento.tipo} asignación={evento.asignacion_id}")
            
            if evento.tipo == 'SALIDA':
                task = DbTask(self.db, self._task_manejar_salida, evento)
                task.signals.result.connect(lambda res: self.log.debug(f"[Worker] Salida result: {res}"))
                task.signals.error.connect(lambda err: self._on_worker_error(err, 'SALIDA'))
                task.signals.result.connect(lambda res: self._on_salida_done(res))
                task.signals.result.connect(lambda res: self._on_event_done(res, 'SALIDA'))
                # Tras resultado de salida no reiniciamos; solo para llegada
                self.thread_pool.start(task)
            else:
                task = DbTask(self.db, self._task_manejar_llegada, evento)
                task.signals.result.connect(lambda res: self.log.debug(f"[Worker] Llegada result: {res}"))
                task.signals.error.connect(lambda err: self._on_worker_error(err, 'LLEGADA'))
                # Si fue llegada y ya no hay más eventos del día, reiniciar asignaciones
                task.signals.result.connect(lambda res, ev=evento: self._post_event_result(res, ev))
                task.signals.result.connect(lambda res: self._on_event_done(res, 'LLEGADA'))
                self.thread_pool.start(task)
            
            # Eliminar el evento completado solo si hay elementos
            if self.eventos_pendientes:
                self.eventos_pendientes.pop(0)
            else:
                self.log.debug("No hay eventos pendientes para eliminar tras ejecutar")
            
        except Exception as e:
            self.log.exception(f"Error Crítico en ejecutar_evento: {e}")
            self._running_event = False
            # Intentar recuperación
            self.cargar_eventos_futuros()

    def _on_worker_error(self, err, tipo):
        try:
            self._metrics['errores'] += 1
        except Exception:
            pass
        self.log.error(f"[Worker Error] tipo={tipo} detalle={err}")

    def _on_salida_done(self, res):
        """Tras una salida exitosa, recargar eventos para incluir llegadas elegibles u otras dependencias."""
        try:
            if res:
                self.cargar_eventos_futuros()
                self._emit_update('salida')
        except Exception as e:
            self.log.error(f"Error en _on_salida_done: {e}")

    def _on_event_done(self, ok, tipo):
        """Limpia guardas y reprograma el siguiente evento, contabilizando métricas."""
        self._running_event = False
        try:
            self._metrics['total'] += 1
            if tipo == 'SALIDA':
                self._metrics['salidas'] += 1
            elif tipo == 'LLEGADA':
                self._metrics['llegadas'] += 1
        except Exception:
            pass
        # Lógica de batch/cooldown para modo 'all' con muchos vencidos
        if self._catchup_mode == 'all' and self.eventos_pendientes:
            ahora = QTime.currentTime()
            ms = ahora.msecsTo(self.eventos_pendientes[0].hora_programada)
            if ms <= 0:
                self._batch_count += 1
                if self._batch_count >= self._batch_size:
                    # Pausar antes de seguir con backlog
                    self._batch_count = 0
                    if self._batch_delay_timer is None:
                        self._batch_delay_timer = QTimer()
                        self._batch_delay_timer.setSingleShot(True)
                        self._batch_delay_timer.timeout.connect(self.programar_proximo_evento)
                    self.log.info(f"Pausa de backfill por {self._batch_delay_ms} ms tras lote de {self._batch_size}.")
                    self._batch_delay_timer.start(self._batch_delay_ms)
                    return
            else:
                # Volvemos a futuro, reiniciar contador
                self._batch_count = 0
        # Reprogramar siguiendo el estado actual de la lista (se deduplica internamente)
        self.programar_proximo_evento()
        if ok:
            self._emit_update(tipo.lower())

    def _post_event_result(self, res, evento):
        """Hook post-resultado de worker para lógica adicional (reset al finalizar el día)."""
        try:
            if not res:
                return
            if evento.tipo == 'LLEGADA' and not self.eventos_pendientes:
                self.log.info("Última llegada del día registrada. Reiniciando asignaciones...")
                self._reset_asignaciones_async()
        except Exception as e:
            self.log.error(f"Error en _post_event_result: {e}")

    def manejar_salida(self, evento):
        """Registra la salida real del tren"""
        try:
            hora_actual = QTime.currentTime()
            # Simulación de retraso de salida
            delay_min = self._random_delay_minutes('SALIDA')
            if delay_min > 0:
                hora_actual = hora_actual.addSecs(delay_min * 60)
                self.log.info(f"Simulación: salida con retraso de {delay_min} min")
            self.log.debug(f"Intentando registrar salida asignación={evento.asignacion_id} hora={hora_actual.toString('HH:mm:ss')}")
            
            query = """
            UPDATE ASIGNACION_TREN
            SET HORA_SALIDA_REAL = TO_DATE(:hora_actual, 'HH24:MI:SS')
            WHERE ID_ASIGNACION = :asignacion_id
            """
            params = {
                'asignacion_id': evento.asignacion_id,
                'hora_actual': hora_actual.toString("HH:mm:ss")
            }
            
            if not self.db.execute_query(query, params):
                self.log.error("Falló el execute_query para salida")
                return False
            
            self.log.info(f"Salida registrada exitosamente para asignación {evento.asignacion_id}")
            
            # Registrar incidencia si hay retraso > 5 minutos
            retraso_minutos = max(0, evento.hora_programada.msecsTo(hora_actual) / 60000)
            if retraso_minutos > 5:
                self.registrar_incidencia_retraso(evento, retraso_minutos)
            
            # Registrar en historial
            self.registrar_historial(evento, hora_actual)
            
            self.db.connection.commit()
            self._emit_update('salida')
            return True
            
        except Exception as e:
            self.log.exception(f"ERROR CRÍTICO en manejar_salida: {e}")
            self.db.connection.rollback()
            return False

    def manejar_llegada(self, evento):
        """Registra la llegada real del tren"""
        # Calcular hora de llegada con variabilidad
        hora_salida_real = self.db.fetch_one("""
            SELECT TO_CHAR(HORA_SALIDA_REAL, 'HH24:MI:SS') 
            FROM ASIGNACION_TREN 
            WHERE ID_ASIGNACION = :asignacion_id
        """, {'asignacion_id': evento.asignacion_id})[0]
        
        hora_salida = QTime.fromString(hora_salida_real, "HH:mm:ss")
        variacion = random.uniform(0.95, 1.10)  # -5% a +10% de variación
        duracion_segundos = int(evento.duracion_estimada * 60 * variacion)
        hora_llegada = hora_salida.addSecs(duracion_segundos)
        # Simulación de retraso de llegada
        delay_min = self._random_delay_minutes('LLEGADA')
        if delay_min > 0:
            hora_llegada = hora_llegada.addSecs(delay_min * 60)
            self.log.info(f"Simulación: llegada con retraso de {delay_min} min")
        
        # Registrar llegada real
        query = """
        UPDATE ASIGNACION_TREN
        SET HORA_LLEGADA_REAL = TO_DATE(:hora_llegada, 'HH24:MI:SS')
        WHERE ID_ASIGNACION = :asignacion_id
        """
        params = {
            'asignacion_id': evento.asignacion_id,
            'hora_llegada': hora_llegada.toString("HH:mm:ss")
        }
        
        if not self.db.execute_query(query, params):
            self.log.error("No se pudo registrar la llegada")
            self.db.connection.rollback()
            return
        
        self.log.info(f"Llegada registrada: {hora_llegada.toString('HH:mm:ss')} (Duración: {duracion_segundos/60:.1f} min)")
        
        # Registrar en historial
        self.registrar_historial(evento, hora_llegada)

        self.db.connection.commit()
        self._emit_update('llegada')

    # Worker task implementations that receive a DB connection
    def _task_manejar_salida(self, conn, evento):
        try:
            hora_actual = QTime.currentTime()
            # Simulación de retraso de salida (worker)
            delay_min = self._random_delay_minutes('SALIDA')
            if delay_min > 0:
                hora_actual = hora_actual.addSecs(delay_min * 60)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ASIGNACION_TREN
                    SET HORA_SALIDA_REAL = TO_DATE(:hora_actual, 'HH24:MI:SS')
                    WHERE ID_ASIGNACION = :asignacion_id
                    """,
                    {'hora_actual': hora_actual.toString('HH:mm:ss'), 'asignacion_id': evento.asignacion_id}
                )

            # Registrar incidencia si es necesario (usar conn)
            retraso_minutos = max(0, evento.hora_programada.msecsTo(hora_actual) / 60000)
            if retraso_minutos > 5:
                self.registrar_incidencia_retraso(evento, retraso_minutos, conn=conn)

            # Registrar en historial usando la misma conexión
            self.registrar_historial(evento, hora_actual, conn=conn)

            try:
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

            # Notificar UI
            self._emit_update('salida')
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            self.log.error(f"[Error worker] manejar_salida: {e}")
            return False

    def _task_manejar_llegada(self, conn, evento):
        try:
            # Obtener hora de salida desde la misma conexión
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT TO_CHAR(HORA_SALIDA_REAL, 'HH24:MI:SS') FROM ASIGNACION_TREN WHERE ID_ASIGNACION = :id",
                    {'id': evento.asignacion_id}
                )
                row = cur.fetchone()

            if not row or not row[0]:
                print(f"[Error worker] HORA_SALIDA_REAL no encontrada para {evento.asignacion_id}")
                return False

            hora_salida = QTime.fromString(row[0], 'HH:mm:ss')
            variacion = random.uniform(0.95, 1.10)
            duracion_segundos = int(evento.duracion_estimada * 60 * variacion)
            hora_llegada = hora_salida.addSecs(duracion_segundos)
            # Simulación de retraso de llegada (worker)
            delay_min = self._random_delay_minutes('LLEGADA')
            if delay_min > 0:
                hora_llegada = hora_llegada.addSecs(delay_min * 60)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ASIGNACION_TREN
                    SET HORA_LLEGADA_REAL = TO_DATE(:hora_llegada, 'HH24:MI:SS')
                    WHERE ID_ASIGNACION = :asignacion_id
                    """,
                    {'hora_llegada': hora_llegada.toString('HH:mm:ss'), 'asignacion_id': evento.asignacion_id}
                )

            # Registrar en historial usando la misma conexión
            self.registrar_historial(evento, hora_llegada, conn=conn)

            try:
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

            self._emit_update('llegada')
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            self.log.error(f"[Error worker] manejar_llegada: {e}")
            return False

    # --- Simulación de retrasos ---
    def _random_delay_minutes(self, tipo: str) -> int:
        """Devuelve minutos de retraso simulados para SALIDA/LLEGADA.

        Modo por defecto ('threshold'): randint(0..MAX). Si valor > THRESHOLD => retraso = valor, si no 0.
        Modo 'prob': con PROB hay retraso randint(1..MAX), de lo contrario 0.
        """
        try:
            if not self._delay_enabled or self._delay_max <= 0:
                return 0
            if self._delay_mode == 'prob':
                return random.randint(1, self._delay_max) if random.random() < self._delay_prob else 0
            # threshold (por defecto)
            val = random.randint(0, self._delay_max)
            return val if val > self._delay_threshold else 0
        except Exception:
            return 0

    def registrar_incidencia_retraso(self, evento, retraso_minutos, conn=None):
        """Registra incidencia por retraso en salida"""
        descripcion = f"Retraso de {int(retraso_minutos)} minutos en salida del Tren {evento.tren_id} (Ruta {evento.ruta_id})"
        query = """
        INSERT INTO INCIDENCIA (
            ID_INCIDENCIA, ID_ASIGNACION, TIPO,
            DESCRIPCION, FECHA_HORA, ESTADO
        ) VALUES (
            INCIDENCIA_SEQ.NEXTVAL, :asignacion_id, 'RETRASO',
            :descripcion, SYSDATE, 'NO RESUELTO'
        )
        """

        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(query, {'asignacion_id': evento.asignacion_id, 'descripcion': descripcion})
                return True
            except Exception as e:
                self.log.error(f"[Error worker] registrar_incidencia_retraso: {e}")
                return False
        else:
            if self.db.execute_query(query, {'asignacion_id': evento.asignacion_id, 'descripcion': descripcion}):
                self.log.info(f"Incidencia registrada: {descripcion}")
            else:
                self.log.error("No se pudo registrar incidencia")


    def registrar_historial(self, evento, hora_real, conn=None):
        """Registra el evento en el historial"""
        try:
            # Obtener próximo ID de historial
            #resultado = self.db.fetch_one("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
            #if not resultado:
            #    print("[Error] No se pudo obtener el ID_HISTORIAL")
            #    return False
            #    
            #id_historial = resultado[0]
            
            # Obtener hora de salida y llegada real
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT TO_CHAR(HORA_SALIDA_REAL, 'HH24:MI:SS') FROM ASIGNACION_TREN WHERE ID_ASIGNACION = :asignacion_id", {'asignacion_id': evento.asignacion_id})
                    row = cur.fetchone()
                    hora_salida_real = row[0] if row else None
            else:
                hora_salida_real = self.db.fetch_one("""
                    SELECT TO_CHAR(HORA_SALIDA_REAL, 'HH24:MI:SS') 
                    FROM ASIGNACION_TREN 
                    WHERE ID_ASIGNACION = :asignacion_id
                """, {'asignacion_id': evento.asignacion_id})[0]
            
            hora_llegada_real = hora_real.toString("HH:mm:ss")
            hora_real_str = f"{hora_salida_real}-{hora_llegada_real}"
            
            query = """
            INSERT INTO HISTORIAL (
                ID_HISTORIAL, FECHA_REGISTRO, ID_ASIGNACION,
                ID_USUARIO, INFORMACION, HORA_REAL
            ) VALUES (
                HISTORIAL_SEQ.NEXTVAL, SYSDATE, :id_asignacion,
                :id_usuario, :informacion, :hora_real
            )
            """
            params = {
                'id_asignacion': evento.asignacion_id,
                'id_usuario': self.usuario_id,
                'informacion': f"Llegada: {hora_llegada_real}",
                'hora_real': hora_real_str
            }

            # Verificación adicional de parámetros
            required_params = ['id_usuario', 'informacion', 'id_asignacion', 'hora_real']
            
            for param in required_params:
                if param not in params:
                    print(f"[Error] Falta parámetro requerido: {param}")
                    return False

            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute(query, params)
                    return True
                except Exception as e:
                    self.log.error(f"[Error worker] registrar_historial: {e}")
                    return False
            else:
                if not self.db.execute_query(query, params):
                    self.log.error("No se pudo registrar en historial")
                    return False
                
            self.log.info(f"Registro en historial para {evento.tipo} de ASIGNACION {evento.asignacion_id}")
            return True
            
        except Exception as e:
            self.log.error(f"Excepción en registrar_historial: {str(e)}")
            return False

    def verificar_eventos(self):
        """Verificación periódica con manejo de errores mejorado"""
        try:
            # Detectar cambio de día y reiniciar si corresponde
            hoy = QDate.currentDate()
            if hoy != self._current_date:
                self.log.info("Cambio de día detectado. Reiniciando asignaciones del nuevo día...")
                self._current_date = hoy
                self._reset_asignaciones_async()
                # cargar eventos después del reset en el callback
                return

            if self._running_event:
                self.log.debug("Se omite verificación: hay un evento en ejecución.")
                return
            self.log.info("Verificando nuevos eventos...")
            eventos_previos = len(self.eventos_pendientes)
            self.cargar_eventos_futuros()
            
            if not self.eventos_pendientes and eventos_previos == 0:
                self.log.info("Aún no hay eventos pendientes después de verificación")
            elif not self.eventos_pendientes:
                self.log.info("Eventos pendientes cambiaron durante la verificación; recargando...")
                self.cargar_eventos_futuros()  # Reintento
        except Exception as e:
            self.log.error(f"Error en verificar_eventos: {str(e)}")

    # --- Reset diario de asignaciones ---
    def _reset_asignaciones_async(self):
        """Lanza un DbTask para poner en NULL las horas reales de todas las asignaciones y luego recargar eventos."""
        def on_done(res):
            if res:
                self.log.info("Asignaciones reiniciadas para el nuevo ciclo del día")
                try:
                    self._metrics['resets'] += 1
                except Exception:
                    pass
            else:
                self.log.error("Falló el reinicio de asignaciones")
            # Tras reiniciar, recargar lista de eventos del día
            self.cargar_eventos_futuros()
            self._emit_update('reset')

        task = DbTask(self.db, self._reset_asignaciones_worker)
        task.signals.result.connect(on_done)
        task.signals.error.connect(lambda err: self.log.error(f"[Worker Error] reset_asignaciones: {err}"))
        self.thread_pool.start(task)

    def _reset_asignaciones_worker(self, conn):
        """Worker: ejecuta el reset de asignaciones en la misma conexión y hace commit."""
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ASIGNACION_TREN
                    SET HORA_SALIDA_REAL = NULL,
                        HORA_LLEGADA_REAL = NULL
                    WHERE HORA_SALIDA_REAL IS NOT NULL OR HORA_LLEGADA_REAL IS NOT NULL
                    """
                )
            try:
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            self.log.error(f"[Error worker] _reset_asignaciones_worker: {e}")
            return False

    def obtener_progreso_tren(self, asignacion_id):
        """Calcula el porcentaje de avance de un tren (0-100)"""
        query = """
        SELECT 
            TO_CHAR(a.HORA_SALIDA_REAL, 'HH24:MI:SS'),
            r.DURACION_ESTIMADA
        FROM ASIGNACION_TREN a
        JOIN RUTA r ON a.ID_RUTA = r.ID_RUTA
        WHERE a.ID_ASIGNACION = :asignacion_id
        """
        
        resultado = self.db.fetch_one(query, {'asignacion_id': asignacion_id})
        
        if not resultado or not resultado[0]:
            return 0  # No ha salido aún
        
        hora_salida = QTime.fromString(resultado[0], "HH:mm:ss")
        duracion_minutos = resultado[1]
        ahora = QTime.currentTime()
        
        if hora_salida > ahora:
            return 0
        
        tiempo_transcurrido = hora_salida.msecsTo(ahora) / 60000  # en minutos
        porcentaje = min(100, (tiempo_transcurrido / duracion_minutos) * 100)
        
        return round(porcentaje, 1)
    
    def verificar_estado_asignacion(self, asignacion_id):
        """Método de debug para verificar el estado actual en BD"""
        query = """
        SELECT 
            TO_CHAR(HORA_SALIDA_REAL, 'HH24:MI:SS') as salida_real,
            TO_CHAR(HORA_LLEGADA_REAL, 'HH24:MI:SS') as llegada_real
        FROM ASIGNACION_TREN
        WHERE ID_ASIGNACION = :id
        """
        resultado = self.db.fetch_one(query, {'id': asignacion_id})
        self.log.debug(f"Estado actual de asignación {asignacion_id}: {resultado}")
        return resultado

    # --- Señales y utilidades ---
    def _emit_update(self, reason: str = "update"):
        """Emite señales de actualización compatibles y opcionalmente con motivo."""
        try:
            self.update_triggered.emit()
            self.update_reason.emit(reason)
        except Exception:
            # En caso de que alguna vista aún no esté conectada a update_reason
            try:
                self.update_triggered.emit()
            except Exception:
                pass

    def get_metrics(self):
        """Devuelve un snapshot de métricas básicas del EventManager."""
        return dict(self._metrics)

    def stop(self):
        """Detiene timers y limpia estado para apagado ordenado."""
        try:
            if self.verification_timer and self.verification_timer.isActive():
                self.verification_timer.stop()
        except Exception:
            pass
        try:
            if self._schedule_timer and self._schedule_timer.isActive():
                self._schedule_timer.stop()
        except Exception:
            pass
        try:
            if self._batch_delay_timer and self._batch_delay_timer.isActive():
                self._batch_delay_timer.stop()
        except Exception:
            pass
        self._scheduled_key = None
        self._running_event = False

    def start(self):
        """Inicia timers y carga de eventos si no están activos (para coordinación con db)."""
        try:
            if not self.verification_timer.isActive():
                self.verification_timer.start(60000)
        except Exception:
            pass
        self.cargar_eventos_futuros()

    # Coordinación con db: attach/detach
    def attach_to_db(self, db_connection):
        """Asocia el EventManager a un objeto db y registra la referencia si está libre."""
        self.db = db_connection
        try:
            if not hasattr(self.db, 'event_manager') or getattr(self.db, 'event_manager') is None:
                setattr(self.db, 'event_manager', self)
        except Exception:
            pass

    def detach_from_db(self):
        """Desasocia y limpia la referencia desde el objeto db, sin detener timers."""
        try:
            if hasattr(self.db, 'event_manager') and getattr(self.db, 'event_manager') is self:
                setattr(self.db, 'event_manager', None)
        except Exception:
            pass
    

