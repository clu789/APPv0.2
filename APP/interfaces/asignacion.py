from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                            QDateEdit, QPushButton, QMessageBox, QSizePolicy, 
                            QSpacerItem, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QDate, QDateTime, QTime, QSize
from PyQt6.QtGui import QPixmap
import oracledb
from datetime import datetime, timedelta

class InterfazAsignacion(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.TIEMPO_ABORDAJE = 5  # minutos entre viajes
        self.TIEMPO_TRANSFERENCIA = 30  # minutos para cambiar de ruta
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(500, 600)  # Tamaño fijo inicial

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)  # Márgenes uniformes
        main_layout.setSpacing(15)

        # Título del panel
        self.label_titulo = QLabel("Asignar ruta:")
        self.label_titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.label_titulo)

        # Mensaje de estado
        self.label_mensaje = QLabel("")
        self.label_mensaje.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label_mensaje.setStyleSheet("font-size: 20px; color: green; font-weight: bold;")
        main_layout.addWidget(self.label_mensaje)

        # Panel izquierdo (controles)
        panel_controles = QFrame()
        panel_controles.setFixedWidth(300)  # Ancho fijo
        controles_layout = QVBoxLayout(panel_controles)
        controles_layout.setSpacing(12)  # Espaciado vertical entre elementos

        # Configuración común para los controles
        control_style = """
            QComboBox, QDateEdit, QLabel {
                margin-bottom: 8px;
                min-height: 25px;
            }
        """

        # Sección de fecha
        fecha_layout = QHBoxLayout()
        fecha_layout.setSpacing(10)
        fecha_layout.addWidget(QLabel("Fecha:"))
        self.calendario = QDateEdit()
        self.calendario.setStyleSheet(control_style)
        self.calendario.setDisplayFormat("dd/MM/yyyy")
        self.calendario.setDate(QDate.currentDate())
        self.calendario.setCalendarPopup(True)
        self.calendario.setMinimumDate(QDate.currentDate())
        self.calendario.dateChanged.connect(self.actualizar_horas_disponibles)
        fecha_layout.addWidget(self.calendario)
        controles_layout.addLayout(fecha_layout)

        # Sección de hora
        hora_layout = QHBoxLayout()
        hora_layout.setSpacing(10)
        hora_layout.addWidget(QLabel("Hora:"))
        self.combo_hora = QComboBox()
        self.combo_hora.setStyleSheet(control_style)
        self.combo_hora.setEditable(True)
        self.actualizar_horas_disponibles()
        hora_layout.addWidget(self.combo_hora)

        hora_layout.addWidget(QLabel(":"))

        self.combo_minutos = QComboBox()
        self.combo_minutos.setStyleSheet(control_style)
        self.combo_minutos.setEditable(True)
        for m in range(0, 60, 5):  # Cada 5 minutos
            self.combo_minutos.addItem(f"{m:02d}")
        hora_layout.addWidget(self.combo_minutos)
        controles_layout.addLayout(hora_layout)

        # Tren
        tren_layout = QHBoxLayout()
        tren_layout.setSpacing(10)
        tren_layout.addWidget(QLabel("Unidad:"))
        self.combo_tren = QComboBox()
        self.combo_tren.setStyleSheet(control_style)
        self.combo_tren.addItem("Seleccionar")
        self.cargar_trenes_disponibles()
        tren_layout.addWidget(self.combo_tren)
        controles_layout.addLayout(tren_layout)

        # Ruta
        ruta_layout = QHBoxLayout()
        ruta_layout.setSpacing(10)
        ruta_layout.addWidget(QLabel("Ruta:"))
        self.combo_ruta = QComboBox()
        self.combo_ruta.setStyleSheet(control_style)
        self.combo_ruta.addItem("Seleccionar")
        self.cargar_rutas()
        self.combo_ruta.currentIndexChanged.connect(self.ajustar_tamano_ventana)
        ruta_layout.addWidget(self.combo_ruta)
        controles_layout.addLayout(ruta_layout)

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        #self.btn_cancelar.clicked.connect(self.regresar_home)
        botones_layout.addWidget(self.btn_cancelar)
    
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.clicked.connect(self.validar_asignacion)
        botones_layout.addWidget(self.btn_consultar)

        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.clicked.connect(self.confirmar_asignacion)
        botones_layout.addWidget(self.btn_confirmar)

        controles_layout.addLayout(botones_layout)

        # Panel derecho (imagen)
        self.panel_imagen = QScrollArea()
        self.panel_imagen.setWidgetResizable(True)
        self.panel_imagen.setMinimumWidth(200)  # Ancho mínimo cuando no hay imagen
        self.panel_imagen.hide()  # Oculto inicialmente

                # Agregar un QLabel 
        self.label_mensaje = QLabel("")
        self.label_mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_mensaje.setStyleSheet("font-size: 18px;color: green; font-weight: bold;")
        controles_layout.addWidget(self.label_mensaje)

        self.img_container = QWidget()
        self.img_layout = QVBoxLayout(self.img_container)
        self.img_ruta = QLabel()
        self.img_ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_ruta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.img_layout.addWidget(self.img_ruta)
        self.panel_imagen.setWidget(self.img_container)

        main_layout.addWidget(panel_controles)
        main_layout.addWidget(self.panel_imagen)

        # Conexión para redimensionamiento
        self.combo_ruta.currentIndexChanged.connect(self.ajustar_tamano_ventana)

    #Recargar los datos de la interfaz
    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de InterfazAsignacion")
        self.cargar_trenes_disponibles()
        self.cargar_rutas()

    def ajustar_tamano_ventana(self, index):
        if index > 0:  # Si se seleccionó una ruta válida
            id_ruta = self.combo_ruta.currentData()
            self.load_route_image(id_ruta)
            self.panel_imagen.show()
            self.setFixedSize(900, 600)
        else:
            self.panel_imagen.hide()
            self.setFixedSize(500, 600)

    def actualizar_horas_disponibles(self):
        """Actualiza las horas disponibles según la fecha seleccionada"""
        self.combo_hora.clear()
        
        hora_actual = QTime.currentTime().hour()
        minuto_actual = QTime.currentTime().minute()
        
        # Si es hoy, mostramos horas desde la actual
        if self.calendario.date() == QDate.currentDate():
            hora_inicio = hora_actual
        else:
            hora_inicio = 0  # Si es otro día, mostramos todas las horas
            
        for h in range(hora_inicio, 24):
            self.combo_hora.addItem(f"{h:02d}")

    def load_route_image(self, id_ruta):
        """Versión robusta para cargar imágenes desde Oracle"""
        try:
            self.img_ruta.clear()
            
            # 1. Obtener el BLOB desde Oracle
            query = "SELECT IMAGEN FROM RUTA WHERE ID_RUTA = :id_ruta"
            result = self.db.fetch_one(query, {"id_ruta": id_ruta})
            
            if not result or not result[0]:
                self.img_ruta.setText("No hay imagen disponible")
                return

            # 2. Leer el BLOB
            blob = result[0]
            image_data = blob.read()
            
            # 3. Crear QPixmap
            pixmap = QPixmap()
            if not pixmap.loadFromData(image_data):
                self.img_ruta.setText("Formato no soportado")
                return

            # 4. Escalar adecuadamente
            max_width = self.panel_imagen.width() - 20
            max_height = self.panel_imagen.height() - 50  # Reducir más el eje Y
            
            scaled_pix = pixmap.scaled(
                max_width, 
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.img_ruta.setPixmap(scaled_pix)
            
        except oracledb.DatabaseError as e:
            print(f"Error Oracle: {e}")
            self.img_ruta.setText("Error de base de datos")
        except Exception as e:
            print(f"Error general: {str(e)}")
            self.img_ruta.setText("Error al cargar imagen")
            
    def on_ruta_selected(self):
        if self.combo_ruta.currentIndex() > 0:
            id_ruta = self.combo_ruta.currentData()
            self.panel_imagen.show()  # Mostrar panel solo cuando se selecciona ruta
            self.load_route_image(id_ruta)
        else:
            self.panel_imagen.hide()

    def cargar_trenes_disponibles(self):
            """Carga los trenes disponibles, indicando su último horario y filtrando por fecha/hora."""
            self.combo_tren.clear()
            self.combo_tren.addItem("Seleccionar")

            fecha = self.calendario.date().toString("yyyy-MM-dd")
            hora = self.combo_hora.currentText() if self.combo_hora.currentIndex() >= 0 else "00"
            minutos = self.combo_minutos.currentText() if self.combo_minutos.currentIndex() >= 0 else "00"

            hora_seleccionada = f"{hora}:{minutos}:00"

            query = """
                SELECT T.ID_TREN, T.NOMBRE
                FROM TREN T
                WHERE T.ESTADO = 'ACTIVO'
                AND NOT EXISTS (
                    SELECT 1
                    FROM ASIGNACION_TREN A
                    JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                    WHERE A.ID_TREN = T.ID_TREN
                    AND TRUNC(H.HORA_SALIDA_PROGRAMADA) = TO_DATE(:fecha, 'YYYY-MM-DD')
                    AND TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') = :hora
                )
                ORDER BY T.ID_TREN
            """

            trenes = self.db.fetch_all(query, {"fecha": fecha, "hora": hora_seleccionada})

            if trenes:
                for id_tren, nombre in trenes:
                    # Obtener último horario asignado para los trenes filtrados
                    query_ultimo = """
                        SELECT MAX(H.HORA_LLEGADA_PROGRAMADA)
                        FROM ASIGNACION_TREN A
                        JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                        WHERE A.ID_TREN = :id_tren
                    """
                    ultimo_horario = self.db.fetch_one(query_ultimo, {"id_tren": id_tren})

                    texto = f"{id_tren} - {nombre}"
                    if ultimo_horario and ultimo_horario[0]:
                        from datetime import datetime  # Aseguramos que datetime esté importado
                        if isinstance(ultimo_horario[0], datetime):
                            texto += f" (Último: {ultimo_horario[0].strftime('%H:%M')})"
                        else:
                            texto += f" (Último: {str(ultimo_horario[0])})"

                    self.combo_tren.addItem(texto, id_tren)

    def cargar_rutas(self):
        """Carga las rutas disponibles con información básica"""
        self.combo_ruta.clear()
        self.combo_ruta.addItem("Seleccionar")
        
        query = """
            SELECT R.ID_RUTA, 
                   LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ESTACIONES
            FROM RUTA R
            JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
            JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
            GROUP BY R.ID_RUTA
            ORDER BY R.ID_RUTA
        """
        rutas = self.db.fetch_all(query)
        
        if rutas:
            for id_ruta, estaciones in rutas:
                self.combo_ruta.addItem(f"Ruta {id_ruta} - {estaciones.split('→')[0].strip()}...", id_ruta)

    def validar_asignacion(self):
        """Valida la asignación con todas las reglas de negocio"""
        # Validación básica de campos
        if self.combo_tren.currentIndex() <= 0:
            self.mostrar_mensaje("Seleccione un tren válido", False)
            return False
            
        if self.combo_ruta.currentIndex() <= 0:
            self.mostrar_mensaje("Seleccione una ruta válida", False)
            return False
            
        try:
            hora = int(self.combo_hora.currentText())
            minutos = int(self.combo_minutos.currentText())
            if not (0 <= hora < 24 and 0 <= minutos < 60):
                raise ValueError
        except ValueError:
            self.mostrar_mensaje("La hora seleccionada no es válida", False)
            return False
            
        fecha = self.calendario.date()
        fecha_hora_seleccionada = QDateTime(fecha, QTime(hora, minutos))
        
        if fecha_hora_seleccionada < QDateTime.currentDateTime():
            self.mostrar_mensaje("No se puede asignar un horario en el pasado", False)
            return False
            
        id_tren = self.combo_tren.currentData()
        id_ruta = self.combo_ruta.currentData()
        
        # Obtener duración de la nueva ruta
        duracion = self.obtener_duracion_ruta(id_ruta)
        if not duracion:
            self.mostrar_mensaje("No se pudo obtener la duración de la ruta", False)
            return False

        nueva_salida = fecha_hora_seleccionada.toPyDateTime()
        nueva_llegada = nueva_salida + timedelta(minutes=duracion)
        
        # 1. Verificar que el tren no tenga viajes solapados en la misma fecha
        query_viajes = """
            SELECT H.HORA_SALIDA_PROGRAMADA, H.HORA_LLEGADA_PROGRAMADA,
                   R.DURACION_ESTIMADA, R.ID_RUTA
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            WHERE A.ID_TREN = :id_tren
            AND TRUNC(H.HORA_SALIDA_PROGRAMADA) = TO_DATE(:fecha, 'YYYY-MM-DD')
            ORDER BY H.HORA_SALIDA_PROGRAMADA
        """
        
        try:
            viajes = self.db.fetch_all(query_viajes, {
                "id_tren": id_tren,
                "fecha": fecha.toString("yyyy-MM-dd")
            })
        except Exception as e:
            print(f"Error en consulta de viajes: {str(e)}")
            self.mostrar_mensaje("Error al verificar horarios existentes", False)
            return False
            
        if viajes:
            for viaje in viajes:
                salida_existente = viaje[0] if isinstance(viaje[0], datetime) else datetime.strptime(str(viaje[0]), '%Y-%m-%d %H:%M:%S')
                llegada_existente = viaje[1] if isinstance(viaje[1], datetime) else datetime.strptime(str(viaje[1]), '%Y-%m-%d %H:%M:%S')
                
                # Verificar solapamiento
                if (nueva_salida < llegada_existente and nueva_llegada > salida_existente):
                    self.mostrar_mensaje(
                        f"El tren ya tiene un viaje asignado de {salida_existente.strftime('%H:%M')} "
                        f"a {llegada_existente.strftime('%H:%M')}", False)
                    return False
                    
                # Verificar tiempo mínimo entre viajes
                tiempo_minimo = timedelta(minutes=self.TIEMPO_ABORDAJE)
                if abs(nueva_salida - llegada_existente) < tiempo_minimo or abs(salida_existente - nueva_llegada) < tiempo_minimo:
                    self.mostrar_mensaje(
                        f"Debe haber al menos {self.TIEMPO_ABORDAJE} minutos entre viajes "
                        f"(Viaje existente: {salida_existente.strftime('%H:%M')}-{llegada_existente.strftime('%H:%M')})", 
                        False)
                    return False
                    
                # Verificar cambio de ruta (si es diferente a la actual)
                if viaje[3] != id_ruta:
                    tiempo_transferencia = timedelta(minutes=self.TIEMPO_TRANSFERENCIA)
                    if abs(nueva_salida - llegada_existente) < tiempo_transferencia:
                        # Obtener estaciones de ambas rutas
                        estaciones_ruta_actual = self.obtener_estaciones_ruta(id_ruta)
                        estaciones_ruta_existente = self.obtener_estaciones_ruta(viaje[3])
                        
                        # Verificar si comparten estaciones
                        if not set(estaciones_ruta_actual).intersection(set(estaciones_ruta_existente)):
                            self.mostrar_mensaje(
                                f"El tren necesita al menos {self.TIEMPO_TRANSFERENCIA} minutos "
                                f"para cambiar de ruta (no comparten estaciones)", 
                                False)
                            return False
        
        # Si todo está bien
        self.mostrar_mensaje(
            f"Asignación válida. Viaje programado de {nueva_salida.strftime('%H:%M')} "
            f"a {nueva_llegada.strftime('%H:%M')}. Tiempo de abordaje: {self.TIEMPO_ABORDAJE} minutos.", 
            True)
        return True

    def obtener_estaciones_ruta(self, id_ruta):
        """Obtiene las estaciones de una ruta específica"""
        query = """
            SELECT E.ID_ESTACION 
            FROM RUTA_DETALLE RD
            JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
            WHERE RD.ID_RUTA = :id_ruta
            ORDER BY RD.ORDEN
        """
        resultados = self.db.fetch_all(query, {"id_ruta": id_ruta})
        return [r[0] for r in resultados] if resultados else []

    def confirmar_asignacion(self):
        try:
            # 1. Obtener parámetros del formulario
            hora = int(self.combo_hora.currentText())
            minutos = int(self.combo_minutos.currentText())
            fecha = self.calendario.date()
            id_tren = self.combo_tren.currentData()
            id_ruta = self.combo_ruta.currentData()

            # 2. Convertir fecha y hora a objetos datetime
            salida = QDateTime(fecha, QTime(hora, minutos)).toPyDateTime()
            duracion = self.obtener_duracion_ruta(id_ruta)
            llegada = salida + timedelta(minutes=duracion)

            # 3. Formatear como strings para Oracle
            salida_str = salida.strftime('%Y-%m-%d %H:%M:%S')
            llegada_str = llegada.strftime('%Y-%m-%d %H:%M:%S')

            # Mensajes de depuración
            print(f"\n[DEBUG] Parámetros para asignación:")
            print(f"Tren ID: {id_tren}, Ruta ID: {id_ruta}")
            print(f"Salida: {salida_str}, Llegada: {llegada_str}")
            print(f"Duración: {duracion} minutos")

            # 4. Iniciar transacción
            cursor = self.db.connection.cursor()

            # ========== PRIMERA INSERCIÓN: HORARIO ==========

            id_horario_var = cursor.var(oracledb.NUMBER)
            cursor.execute("""
                BEGIN
                    INSERT INTO HORARIO (ID_HORARIO, HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA)
                    VALUES ((SELECT NVL(MAX(ID_HORARIO), 0) + 1 FROM HORARIO),
                            TO_DATE(:salida, 'YYYY-MM-DD HH24:MI:SS'),
                            TO_DATE(:llegada, 'YYYY-MM-DD HH24:MI:SS'))
                    RETURNING ID_HORARIO INTO :id_horario;
                END;
            """, {"salida": salida_str, "llegada": llegada_str, "id_horario": id_horario_var})
            
            id_horario = id_horario_var.getvalue()
            print(f"[DEBUG] Horario insertado. ID: {id_horario}")

            # ========== SEGUNDA INSERCIÓN: ASIGNACION_TREN ==========

            id_asignacion_var = cursor.var(oracledb.NUMBER)
            cursor.execute("""
                BEGIN
                    INSERT INTO ASIGNACION_TREN (ID_ASIGNACION, ID_TREN, ID_RUTA, ID_HORARIO)
                    VALUES ((SELECT NVL(MAX(ID_ASIGNACION), 0) + 1 FROM ASIGNACION_TREN),
                            :id_tren, :id_ruta, :id_horario)
                    RETURNING ID_ASIGNACION INTO :id_asignacion;
                END;
            """, {
                "id_tren": id_tren,
                "id_ruta": id_ruta,
                "id_horario": id_horario,
                "id_asignacion": id_asignacion_var
            })
            
            id_asignacion = id_asignacion_var.getvalue()
            print(f"[DEBUG] Asignación insertada. ID: {id_asignacion}")

            # ========== TERCERA INSERCIÓN: HISTORIAL ==========

            # Asumimos que el usuario con ID 1 está realizando la acción
            cursor.execute("""
                INSERT INTO HISTORIAL (ID_HISTORIAL, FECHA_REGISTRO, ID_HORARIO, ID_USUARIO)
                VALUES ((SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL),
                        SYSDATE, :id_horario, 1)
            """, {"id_horario": id_horario})

            # Confirmar TODAS las inserciones
            self.db.connection.commit()
            print("[DEBUG] ¡Todas las inserciones fueron exitosas!")

            # Emitir señal para actualizar las interfaces
            self.db.event_manager.update_triggered.emit()

            # Mostrar mensaje de realizado al usuario
            QMessageBox.information(
                self, 
                "Asignación Exitosa",
                f"Se asignó el tren {id_tren} a la ruta {id_ruta}\n"
                f"Horario: {salida.time().strftime('%H:%M')} - {llegada.time().strftime('%H:%M')}"
            )

            # Actualizar interfaz
            self.cargar_trenes_disponibles()
            self.regresar_home()

        except oracledb.DatabaseError as e:
            error_obj = e.args[0]
            print(f"[ERROR ORACLE] Código: {error_obj.code}, Mensaje: {error_obj.message}")
            self.db.rollback()
            QMessageBox.critical(
                self, 
                "Error en Base de Datos",
                f"Error al guardar:\n{error_obj.message}"
            )

        except ValueError as e:
            print(f"[ERROR] Datos inválidos: {str(e)}")
            self.db.rollback()
            QMessageBox.warning(self, "Datos Inválidos", f"Error: {str(e)}")

        except Exception as e:
            print(f"[ERROR INESPERADO] {str(e)}")
            self.db.rollback()
            QMessageBox.critical(
                self,
                "Error Inesperado",
                f"Ocurrió un error inesperado:\n{str(e)}"
            )
        
    
    def mostrar_mensaje(self, texto, es_exito):
        """Muestra mensajes de estado"""
        self.label_mensaje.setText(texto)
        self.label_mensaje.setStyleSheet(
            "color: green; font-weight: bold;" if es_exito else 
            "color: red; font-weight: bold;")

    def obtener_duracion_ruta(self, id_ruta):
        """Obtiene la duración estimada de una ruta específica"""
        query = "SELECT DURACION_ESTIMADA FROM RUTA WHERE ID_RUTA = :id_ruta"
        resultado = self.db.fetch_one(query, {"id_ruta": id_ruta})
        
        if not resultado:
            raise ValueError(f"No se encontró la duración para la ruta ID {id_ruta}")
        
        return int(resultado[0])  # Asegurarnos que devuelve un entero

    #def regresar_home(self):
    #    """Regresa a la pantalla principal"""
    #    self.main_window.cambiar_interfaz(0)
