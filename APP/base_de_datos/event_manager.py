from PyQt6.QtCore import QTimer, QTime, QObject, pyqtSignal
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
    
    def __init__(self, db_connection, usuario_id=1):
        super().__init__()
        self.db = db_connection
        self.usuario_id = usuario_id  # ID del usuario actual
        self.eventos_pendientes = []  # Lista ordenada de eventos futuros
        self.current_timer = None
        
        # Configurar timer de verificación periódica
        self.verification_timer = QTimer()
        self.verification_timer.timeout.connect(self.verificar_eventos)
        self.verification_timer.start(60000)  # 1 minuto
        
        # Cargar eventos iniciales
        self.cargar_eventos_futuros()

    def cargar_eventos_futuros(self):
        """Carga todos los eventos futuros de la base de datos"""
        print("\n[Cargando eventos futuros...]")
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
            AND TO_CHAR(h.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') > TO_CHAR(SYSDATE, 'HH24:MI:SS')
            
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
            AND TO_CHAR(h.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') > TO_CHAR(SYSDATE, 'HH24:MI:SS')
        )
        SELECT * FROM eventos
        ORDER BY HORA_EVENTO ASC
        """
        
        resultados = self.db.fetch_all(query)
        self.eventos_pendientes = []
        
        for res in resultados:
            hora_evento = QTime.fromString(res[3], "HH:mm:ss")
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
            print(f" - Evento cargado: {evento.tipo} para ASIGNACION {evento.asignacion_id} a las {hora_evento.toString('HH:mm:ss')}")
        
        self.programar_proximo_evento()

    def programar_proximo_evento(self):
        """Programa el temporizador para el próximo evento con verificación de lista vacía"""
        if self.current_timer:
            self.current_timer.stop()
            self.current_timer = None
        
        if not self.eventos_pendientes:
            print("\n[No hay eventos pendientes. Revisando en 1 minuto...]")
            QTimer.singleShot(60000, self.verificar_eventos)
            return
        
        evento = self.eventos_pendientes[0]
        ahora = QTime.currentTime()
        ms_hasta_evento = ahora.msecsTo(evento.hora_programada)
        
        if ms_hasta_evento <= 0:
            # El evento debería haber ocurrido ya
            self.ejecutar_evento(evento)
        else:
            print(f"\n[Programando próximo evento: {evento.tipo} para {evento.hora_programada.toString('HH:mm:ss')}]")
            self.current_timer = QTimer()
            self.current_timer.setSingleShot(True)
            self.current_timer.timeout.connect(lambda: self.ejecutar_evento(evento))
            self.current_timer.start(ms_hasta_evento)

    def ejecutar_evento(self, evento):
        """Ejecuta el evento (salida o llegada) con manejo seguro de lista vacía"""
        try:
            print(f"\n[Ejecutando evento {evento.tipo} para ASIGNACION {evento.asignacion_id}]")
            
            if evento.tipo == 'SALIDA':
                self.manejar_salida(evento)
            else:
                self.manejar_llegada(evento)
            
            # Eliminar el evento completado solo si hay elementos
            if self.eventos_pendientes:
                self.eventos_pendientes.pop(0)
            else:
                print("[Advertencia] No hay eventos pendientes para eliminar")
            
            # Programar próximo evento
            self.programar_proximo_evento()
            
        except Exception as e:
            print(f"[Error Crítico] en ejecutar_evento: {str(e)}")
            # Intentar recuperación
            self.cargar_eventos_futuros()

    def manejar_salida(self, evento):
        """Registra la salida real del tren"""
        try:
            hora_actual = QTime.currentTime()
            print(f"[DEBUG] Intentando registrar salida para asignación {evento.asignacion_id} a las {hora_actual.toString('HH:mm:ss')}")
            
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
                print("[ERROR] Falló el execute_query para salida")
                return False
            
            print(f"[✓] Salida registrada exitosamente para asignación {evento.asignacion_id}")
            
            # Registrar incidencia si hay retraso > 5 minutos
            retraso_minutos = max(0, evento.hora_programada.msecsTo(hora_actual) / 60000)
            if retraso_minutos > 5:
                self.registrar_incidencia_retraso(evento, retraso_minutos)
            
            # Registrar en historial
            self.registrar_historial(evento, hora_actual)
            
            self.db.connection.commit()
            self.update_triggered.emit()
            return True
            
        except Exception as e:
            print(f"[ERROR CRÍTICO] en manejar_salida: {str(e)}")
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
            print("[Error] No se pudo registrar la llegada")
            self.db.connection.rollback()
            return
        
        print(f"[✓] Llegada registrada: {hora_llegada.toString('HH:mm:ss')} (Duración: {duracion_segundos/60:.1f} min)")
        
        # Registrar en historial
        self.registrar_historial(evento, hora_llegada)
        
        self.db.connection.commit()
        self.update_triggered.emit()

    def registrar_incidencia_retraso(self, evento, retraso_minutos):
        """Registra incidencia por retraso en salida"""
        id_incidencia = self.db.fetch_one("SELECT NVL(MAX(ID_INCIDENCIA), 0) + 1 FROM INCIDENCIA")[0]
        
        query = """
        INSERT INTO INCIDENCIA (
            ID_INCIDENCIA, ID_ASIGNACION, TIPO, 
            DESCRIPCION, FECHA_HORA, ESTADO
        ) VALUES (
            :id_incidencia, :asignacion_id, 'RETRASO',
            :descripcion, SYSDATE, 'NO RESUELTO'
        )
        """
        
        descripcion = f"Retraso de {int(retraso_minutos)} minutos en salida del Tren {evento.tren_id} (Ruta {evento.ruta_id})"
        
        if self.db.execute_query(query, {
            'id_incidencia': id_incidencia,
            'asignacion_id': evento.asignacion_id,
            'descripcion': descripcion
        }):
            print(f"[✓] Incidencia registrada: {descripcion}")
        else:
            print("[Error] No se pudo registrar incidencia")


    def registrar_historial(self, evento, hora_real):
        """Registra el evento en el historial"""
        try:
            # Obtener próximo ID de historial
            resultado = self.db.fetch_one("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
            if not resultado:
                print("[Error] No se pudo obtener el ID_HISTORIAL")
                return False
                
            id_historial = resultado[0]
            
            # Obtener hora de salida y llegada real
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
                :id_historial, SYSDATE, :id_asignacion,
                :id_usuario, :informacion, :hora_real
            )
            """
            params = {
                'id_historial': id_historial,
                'id_asignacion': evento.asignacion_id,
                'id_usuario': self.usuario_id,
                'informacion': f"Llegada: {hora_llegada_real}",
                'hora_real': hora_real_str
            }

            # Verificación adicional de parámetros
            required_params = ['id_historial', 'id_usuario', 'informacion', 'id_asignacion', 'hora_real']
            
            for param in required_params:
                if param not in params:
                    print(f"[Error] Falta parámetro requerido: {param}")
                    return False

            if not self.db.execute_query(query, params):
                print("[Error] No se pudo registrar en historial")
                return False
                
            print(f"[Éxito] Registro en historial para {evento.tipo} de ASIGNACION {evento.asignacion_id}")
            return True
            
        except Exception as e:
            print(f"[Error] Excepción en registrar_historial: {str(e)}")
            return False

    def verificar_eventos(self):
        """Verificación periódica con manejo de errores mejorado"""
        try:
            print("\n[Verificando nuevos eventos...]")
            eventos_previos = len(self.eventos_pendientes)
            self.cargar_eventos_futuros()
            
            if not self.eventos_pendientes and eventos_previos == 0:
                print("[Info] Aún no hay eventos pendientes después de verificación")
            elif not self.eventos_pendientes:
                print("[Advertencia] Se perdieron los eventos pendientes durante la verificación")
                self.cargar_eventos_futuros()  # Reintento
        except Exception as e:
            print(f"[Error] en verificar_eventos: {str(e)}")

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
        print(f"[DEBUG] Estado actual de asignación {asignacion_id}: {resultado}")
        return resultado
    

