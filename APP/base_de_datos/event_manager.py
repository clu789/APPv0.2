import random
from PyQt6.QtCore import QTimer, QDateTime, QObject, pyqtSignal,QTime

class EventManager(QObject):
    update_triggered = pyqtSignal()

    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.current_timer = None
        self.next_event_time = None
        self.next_event_id = None
        self.next_event_type = None

        # Timer para verificación periódica de nuevos eventos
        self.verification_timer = QTimer()
        self.verification_timer.timeout.connect(self.verify_events)
        self.verification_timer.setInterval(60000)  # 1 minuto
        self.verification_timer.start()

        # Iniciar el proceso
        self.schedule_next_event()

    def schedule_next_event(self):
        """Busca el próximo evento y programa el timer"""
        print("Buscando el próximo evento...")
        event = self.find_next_pending_event()

        if event:
            print(f"Evento encontrado: {event}")
            asignacion_id, event_id, event_type, event_time_str = event  # Ahora 4 variables
            
            # Convertir el string de hora a QTime
            try:
                event_time = QTime.fromString(event_time_str, "HH:mm:ss")
                if not event_time.isValid():
                    print(f"Error: Hora de evento inválida: {event_time_str}")
                    QTimer.singleShot(60000, self.schedule_next_event)
                    return
                    
                now = QTime.currentTime()
                ms_to_event = now.msecsTo(event_time)

                if ms_to_event > 0:
                    print(f"Programando evento: {event_type} (ID: {event_id}) para las {event_time.toString('HH:mm:ss')}")
                    self.next_event_time = event_time
                    self.next_event_id = event_id
                    self.next_event_type = event_type
                    self.next_asignacion_id = asignacion_id

                    if self.current_timer:
                        self.current_timer.stop()
                        self.current_timer = None

                    self.current_timer = QTimer.singleShot(
                        ms_to_event,
                        lambda: self.handle_event(asignacion_id, event_id, event_type)
                    )
                else:
                    print(f"El evento {event_type} ya está en el pasado. Procesando ahora...")
                    self.handle_event(asignacion_id, event_id, event_type)
            except Exception as e:
                print(f"Error al programar evento: {e}")
                QTimer.singleShot(60000, self.schedule_next_event)
        else:
            print("No hay eventos próximos. Revisando en 1 minuto...")
            QTimer.singleShot(60000, self.schedule_next_event)

    def check_time_to_event(self):
        """Revisar el tiempo restante al evento y actuar cuando llegue"""
        now = QDateTime.currentDateTime()
        ms_to_event = now.msecsTo(self.next_event_time)
        seconds_left = ms_to_event / 1000

        if seconds_left > 0:
            print(f"Faltan {seconds_left:.2f} segundos para el evento {self.next_event_type}.")
        else:
            print("\u00a1Es momento de ejecutar el evento!")
            if self.current_timer:
                self.current_timer.stop()
                self.current_timer = None
            self.handle_event(self.next_event_id, self.next_event_type)

    def find_next_pending_event(self):
        """Encuentra el próximo evento pendiente más cercano (sólo por hora)"""
        print("\n[DEBUG] Iniciando búsqueda de próximo evento...")
        
        query = """
        WITH eventos AS (
            -- Eventos de SALIDA (sin hora_salida_real)
            SELECT 
                a.ID_ASIGNACION,
                a.ID_HORARIO,
                'SALIDA' AS TIPO,
                TO_CHAR(h.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS HORA_EVENTO
            FROM ASIGNACION_TREN a
            JOIN HORARIO h ON a.ID_HORARIO = h.ID_HORARIO
            WHERE a.HORA_SALIDA_REAL IS NULL
            AND TO_CHAR(h.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') > TO_CHAR(SYSDATE, 'HH24:MI:SS')

            UNION ALL

            -- Eventos de LLEGADA (con salida real pero sin llegada_real)
            SELECT 
                a.ID_ASIGNACION,
                a.ID_HORARIO,
                'LLEGADA' AS TIPO,
                TO_CHAR(h.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS HORA_EVENTO
            FROM ASIGNACION_TREN a
            JOIN HORARIO h ON a.ID_HORARIO = h.ID_HORARIO
            WHERE a.HORA_LLEGADA_REAL IS NULL
            AND TO_CHAR(h.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') > TO_CHAR(SYSDATE, 'HH24:MI:SS')
            AND a.HORA_SALIDA_REAL IS NOT NULL
        )
        SELECT 
            ID_ASIGNACION,
            ID_HORARIO,
            TIPO,
            HORA_EVENTO
        FROM eventos
        ORDER BY HORA_EVENTO ASC
        FETCH FIRST 1 ROWS ONLY
        """
        
        print("[DEBUG] Consulta SQL preparada:")
        print(query)
        
        # Verificar conexión a la base de datos
        if not self.db.connection:
            print("[ERROR] No hay conexión a la base de datos")
            return None
        
        try:
            print("[DEBUG] Ejecutando consulta en la base de datos...")
            result = self.db.fetch_one(query)
            
            if result:
                asignacion_id = result[0]
                event_id = result[1]
                event_type = result[2]
                hora_evento = result[3]
                
                print(f"[DEBUG] Evento encontrado - ID_ASIGNACION: {asignacion_id}")
                print(f"[DEBUG] ID_HORARIO: {event_id}")
                print(f"[DEBUG] TIPO: {event_type}")
                print(f"[DEBUG] HORA_EVENTO: {hora_evento}")
                
                # Validar formato de hora
                if not isinstance(hora_evento, str) or len(hora_evento) != 8 or hora_evento.count(':') != 2:
                    print(f"[ERROR] Formato de hora inválido: {hora_evento}")
                    return None
                    
                try:
                    # Convertir a QTime para validación
                    hora_qt = QTime.fromString(hora_evento, "HH:mm:ss")
                    if not hora_qt.isValid():
                        print(f"[ERROR] Hora no válida: {hora_evento}")
                        return None
                        
                    print("[DEBUG] Hora validada correctamente")
                    return (asignacion_id, event_id, event_type, hora_evento)
                    
                except Exception as e:
                    print(f"[ERROR] Error al convertir hora: {str(e)}")
                    return None
                    
            else:
                print("[DEBUG] No se encontraron eventos pendientes")
                return None
                
        except Exception as e:
            print(f"[ERROR] Excepción al ejecutar consulta: {str(e)}")
            return None

    def handle_event(self, asignacion_id, event_id, event_type):
        """Maneja eventos usando sólo horas (sin fechas)"""
        now = QDateTime.currentDateTime()
        hora_actual = now.toString("HH:mm:ss")
        
        try:
            if event_type == "SALIDA":
                # Obtener hora programada
                query_programada = """
                SELECT TO_CHAR(h.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS')
                FROM HORARIO h
                JOIN ASIGNACION_TREN a ON h.ID_HORARIO = a.ID_HORARIO
                WHERE a.ID_ASIGNACION = :asignacion_id
                """
                result = self.db.fetch_one(query_programada, {'asignacion_id': asignacion_id})
                
                if not result:
                    print("Error: No se encontró la asignación")
                    return
                    
                hora_programada = result[0]
                
                # Validar que no se registre antes de tiempo (comparando sólo horas)
                if hora_actual < hora_programada:
                    print("¡Error! Intento de registrar salida antes de la hora programada")
                    # Calcular diferencia en milisegundos
                    hora_prog_qt = QTime.fromString(hora_programada, "HH:mm:ss")
                    hora_actual_qt = QTime.fromString(hora_actual, "HH:mm:ss")
                    delay = hora_actual_qt.msecsTo(hora_prog_qt)
                    QTimer.singleShot(abs(delay), lambda: self.handle_event(asignacion_id, event_id, event_type))
                    return
                    
                # Generar hora real con posible retraso (sólo hora)
                departure_real = self._get_varied_time(now).toString("HH:mm:ss")
                
                # Actualizar BD (sólo hora)
                query = """
                UPDATE ASIGNACION_TREN
                SET HORA_SALIDA_REAL = TO_DATE(:time, 'HH24:MI:SS')
                WHERE ID_ASIGNACION = :asignacion_id
                """
                params = {
                    'asignacion_id': asignacion_id,
                    'time': departure_real
                }
                
            else:  # LLEGADA
                # Obtener datos necesarios (sólo horas)
                query_data = """
                SELECT 
                    TO_CHAR(a.HORA_SALIDA_REAL, 'HH24:MI:SS'),
                    TO_CHAR(h.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'),
                    r.DURACION_ESTIMADA
                FROM ASIGNACION_TREN a
                JOIN HORARIO h ON a.ID_HORARIO = h.ID_HORARIO
                JOIN RUTA r ON a.ID_RUTA = r.ID_RUTA
                WHERE a.ID_ASIGNACION = :asignacion_id
                """
                result = self.db.fetch_one(query_data, {'asignacion_id': asignacion_id})
                
                if not result or not result[0]:
                    print("Error: No hay hora de salida real registrada")
                    return
                    
                # Calcular llegada real basada sólo en horas
                hora_salida_real = result[0]
                hora_llegada_programada = result[1]
                duracion_estimada = result[2]  # en minutos
                
                # Convertir a QTime para cálculos
                salida_qt = QTime.fromString(hora_salida_real, "HH:mm:ss")
                llegada_real_qt = salida_qt.addSecs(int(duracion_estimada * 60 * random.uniform(0.95, 1.10)))
                llegada_real = llegada_real_qt.toString("HH:mm:ss")
                
                # Actualizar BD (sólo hora)
                query = """
                UPDATE ASIGNACION_TREN
                SET HORA_LLEGADA_REAL = TO_DATE(:time, 'HH24:MI:SS')
                WHERE ID_ASIGNACION = :asignacion_id
                """
                params = {
                    'asignacion_id': asignacion_id,
                    'time': llegada_real
                }
            
            # Ejecutar la actualización
            success = self.db.execute_query(query, params)
            if success:
                self.db.connection.commit()
                print(f"✓ Evento {event_type} registrado: {params['time']}")
                self.update_triggered.emit()
            else:
                print("Error al ejecutar la consulta")
                
            self.schedule_next_event()
            
        except Exception as e:
            print(f"Error al manejar evento: {e}")
            if self.db.connection:
                self.db.connection.rollback()


    def verify_events(self):
        """Verificación periódica de nuevos eventos más cercanos"""
        print("Verificando si hay eventos más próximos...")
        new_event = self.find_next_pending_event()

        if new_event:
            # Desempaquetar los 4 valores correctamente
            new_asignacion_id, new_event_id, new_event_type, new_event_time_str = new_event
            
            print(f"[DEBUG] Nuevo evento encontrado: ID_ASIGNACION={new_asignacion_id}, "
                f"ID_HORARIO={new_event_id}, TIPO={new_event_type}, HORA={new_event_time_str}")

            # Convertir el string de hora a QTime
            try:
                new_event_time = QTime.fromString(new_event_time_str, "HH:mm:ss")
                if not new_event_time.isValid():
                    print(f"[ERROR] Hora de evento inválida: {new_event_time_str}")
                    return
                    
                # Verificar si el nuevo evento es más próximo que el actual
                if self.next_event_time is None:
                    print("[DEBUG] No hay evento actual, usando nuevo evento")
                    self._update_scheduled_event(new_asignacion_id, new_event_id, 
                                            new_event_type, new_event_time)
                    return

                # Comparar horas (solo la parte de tiempo)
                now = QTime.currentTime()
                ms_to_new = now.msecsTo(new_event_time)
                ms_to_current = now.msecsTo(self.next_event_time)

                if ms_to_new < ms_to_current:
                    print("[DEBUG] Se encontró un evento más próximo. Reprogramando...")
                    self._update_scheduled_event(new_asignacion_id, new_event_id, 
                                            new_event_type, new_event_time)
                else:
                    print("[DEBUG] El evento actual sigue siendo el más próximo")
                    
            except Exception as e:
                print(f"[ERROR] Error al procesar hora del evento: {e}")
                
        else:
            print("[DEBUG] No hay eventos próximos en la base de datos.")

    def _update_scheduled_event(self, asignacion_id, event_id, event_type, event_time):
        """Actualiza el evento programado internamente"""
        # Detener el temporizador actual si existe
        if self.current_timer:
            self.current_timer.stop()
            self.current_timer = None

        # Actualizar el próximo evento
        self.next_asignacion_id = asignacion_id
        self.next_event_id = event_id
        self.next_event_type = event_type
        self.next_event_time = event_time

        # Reprogramar el siguiente evento
        self.schedule_next_event()

    def _get_varied_time(self, base_time, max_delay_minutes=6):
        """Genera una hora con variabilidad (sólo hora, sin fecha)"""
        if random.random() < 0.4:  # 40% puntual
            return base_time
            
        # 60% con retraso (1-6 minutos)
        delay_minutes = random.randint(1, max_delay_minutes)
        return base_time.addSecs(delay_minutes * 60)

    def _get_arrival_time(self, departure_real, scheduled_arrival):
        """Calcula tiempo de llegada real basado en salida real y llegada programada"""
        scheduled_departure = self.next_event_time  # Hora de salida programada
        scheduled_duration = scheduled_departure.msecsTo(scheduled_arrival) / 1000  # duración en segundos
        
        # Añadir algo de variabilidad al tiempo de viaje (entre -5% y +10% del tiempo programado)
        variation_factor = 1 + (random.random() * 0.15 - 0.05)  # entre 0.95 y 1.10
        actual_duration = scheduled_duration * variation_factor
        
        arrival_real = departure_real.addSecs(int(actual_duration))
        return arrival_real
