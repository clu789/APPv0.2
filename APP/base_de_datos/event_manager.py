import random
from PyQt6.QtCore import QTimer, QDateTime, QObject, pyqtSignal

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
            print("Evento encontrado:", event)
            event_id, event_type, event_time = event
            now = QDateTime.currentDateTime()
            ms_to_event = now.msecsTo(event_time)

            if ms_to_event > 0:
                print(f"Programando evento: {event_type} (ID: {event_id}) para las {event_time.toString('yyyy-MM-dd HH:mm:ss')}")
                self.next_event_time = event_time
                self.next_event_id = event_id
                self.next_event_type = event_type

                if self.current_timer:
                    self.current_timer.stop()
                    self.current_timer = None

                self.current_timer = QTimer.singleShot(
                    ms_to_event,
                    lambda: self.handle_event(event_id, event_type)
                )
            else:
                print(f"El evento {event_type} ya está en el pasado. Procesando ahora...")
                self.handle_event(event_id, event_type)
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
        """Encuentra el próximo evento pendiente más cercano"""
        query = """
        WITH eventos AS (
        SELECT 
            ID_HORARIO,
            'SALIDA' AS TIPO,
            HORA_SALIDA_PROGRAMADA AS HORA_EVENTO,
            HORA_SALIDA_REAL
        FROM HORARIO
        WHERE HORA_SALIDA_REAL IS NULL
        AND HORA_SALIDA_PROGRAMADA > SYSDATE

        UNION ALL

        SELECT 
            ID_HORARIO,
            'LLEGADA' AS TIPO,
            HORA_LLEGADA_PROGRAMADA AS HORA_EVENTO,
            HORA_LLEGADA_REAL
        FROM HORARIO
        WHERE HORA_LLEGADA_REAL IS NULL
        AND HORA_LLEGADA_PROGRAMADA > SYSDATE
        -- Asegurar que ya exista una salida real
        AND HORA_SALIDA_REAL IS NOT NULL
        )
        SELECT 
            ID_HORARIO,
            TIPO,
            TO_CHAR(HORA_EVENTO, 'YYYY-MM-DD HH24:MI:SS') AS HORA_EVENTO
        FROM eventos
        WHERE HORA_EVENTO > SYSDATE
        ORDER BY HORA_EVENTO ASC
        FETCH FIRST 1 ROWS ONLY
        """

        if not self.db.connection:
            print("Error: No hay conexión a la base de datos.")
            return None

        result = self.db.fetch_one(query)
        if result:
            event_id = result[0]
            event_type = result[1]
            event_time_str = result[2]
            event_time = QDateTime.fromString(event_time_str, "yyyy-MM-dd HH:mm:ss")
            if not event_time.isValid():
                print(f"Error: Tiempo de evento inválido recibido: {event_time_str}")
                return None
            return (event_id, event_type, event_time)
        return None

    def handle_event(self, event_id, event_type):
        """Actualiza la base de datos cuando ocurre un evento"""
        print(f"Procesando evento: {event_type} para horario {event_id}")
        
        now = QDateTime.currentDateTime()
        
        if event_type == "SALIDA":
            # Asegurar que el tiempo real no sea anterior al programado
            scheduled_time = self.next_event_time
            if now < scheduled_time:
                print("¡Error! Intento de registrar salida antes de la hora programada")
                # Reprogramar para el momento correcto
                delay = scheduled_time.msecsTo(now)
                QTimer.singleShot(abs(delay), lambda: self.handle_event(event_id, event_type))
                return
                
            departure_real = self._get_varied_time(now)
            query = """
            UPDATE HORARIO
            SET HORA_SALIDA_REAL = TO_DATE(:time, 'YYYY-MM-DD HH24:MI:SS')
            WHERE ID_HORARIO = :id
            """
            params = {'id': event_id, 'time': departure_real.toString("yyyy-MM-dd HH:mm:ss")}
        
        else:  # LLEGADA
            # Obtener datos necesarios
            query_data = """
            SELECT 
                TO_CHAR(HORA_SALIDA_PROGRAMADA, 'YYYY-MM-DD HH24:MI:SS'),
                TO_CHAR(HORA_SALIDA_REAL, 'YYYY-MM-DD HH24:MI:SS'),
                TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'YYYY-MM-DD HH24:MI:SS')
            FROM HORARIO
            WHERE ID_HORARIO = :id
            """
            result = self.db.fetch_one(query_data, {'id': event_id})
            
            if not result:
                print("Error: No se encontró el horario")
                return
                
            scheduled_departure = QDateTime.fromString(result[0], "yyyy-MM-dd HH:mm:ss")
            actual_departure = QDateTime.fromString(result[1], "yyyy-MM-dd HH:mm:ss") if result[1] else None
            scheduled_arrival = QDateTime.fromString(result[2], "yyyy-MM-dd HH:mm:ss")
            
            # Validaciones
            if not actual_departure:
                print("Error: No hay hora de salida real registrada")
                return
                
            if now < scheduled_arrival.addSecs(-60):  # Máximo 1 minuto antes
                print("¡Advertencia! Llegada real registrada demasiado temprano")
                
            arrival_real = self._get_arrival_time(actual_departure, scheduled_arrival)
            
            query = """
            UPDATE HORARIO
            SET HORA_LLEGADA_REAL = TO_DATE(:time, 'YYYY-MM-DD HH24:MI:SS')
            WHERE ID_HORARIO = :id
            """
            params = {'id': event_id, 'time': arrival_real.toString("yyyy-MM-dd HH:mm:ss")}
        
        # Ejecutar la actualización
        try:
            self.db.execute_query(query, params)
            print(f"✓ Evento {event_type} registrado para horario {event_id}")

            # Emitir señal para actualizar las interfaces
            self.update_triggered.emit()
             # Programar el siguiente evento
            self.schedule_next_event()
        except Exception as e:
            print(f"Error al registrar evento: {e}")
            QTimer.singleShot(60000, lambda: self.handle_event(event_id, event_type))


    def verify_events(self):
        """Verificación periódica de nuevos eventos más cercanos"""
        print("Verificando si hay eventos más próximos...")
        new_event = self.find_next_pending_event()

        if new_event:
            new_event_id, new_event_type, new_event_time = new_event
            # Verifica si el nuevo evento es más próximo que el actual
            if (self.next_event_time is None) or (new_event_time.msecsTo(self.next_event_time) > 0):
                print("Se encontró un evento más próximo. Reprogramando...")

                # Detiene el temporizador actual si existe
                if self.current_timer:
                    self.current_timer.stop()
                    self.current_timer = None

                # Actualiza el próximo evento
                self.next_event_time = new_event_time
                self.next_event_id = new_event_id
                self.next_event_type = new_event_type

                # Reprograma el siguiente evento
                self.schedule_next_event()
            else:
                print("No se encontraron nuevos eventos más próximos. Manteniendo el estado actual.")
        else:
            print("No hay eventos próximos en la base de datos.")
        
    def _get_varied_time(self, base_time, max_delay_minutes=6):
        """Genera un tiempo con variabilidad aleatoria (solo retrasos)"""
        # 40% de probabilidad de ser exactamente a tiempo
        if random.random() < 0.4:
            return base_time
            
        # 60% de probabilidad de retraso (1-6 minutos)
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
