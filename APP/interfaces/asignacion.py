from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                            QPushButton, QMessageBox, QSizePolicy, 
                            QSpacerItem, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QDateTime, QTime, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap
import oracledb
from datetime import datetime, timedelta

class InterfazAsignacion(QWidget):
    asignacion_exitosa = pyqtSignal()  # Señal para indicar que se realizó una asignación exitosa

    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(500, 600)  # Tamaño fijo inicial

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)  # Márgenes uniformes
        main_layout.setSpacing(15)

        # Panel izquierdo (controles)
        panel_controles = QFrame()
        panel_controles.setFixedWidth(300)  # Ancho fijo
        controles_layout = QVBoxLayout(panel_controles)
        controles_layout.setSpacing(12)  # Espaciado vertical entre elementos

        # Configuración común para los controles
        control_style = """
            QComboBox, QLabel {
                margin-bottom: 8px;
                min-height: 25px;
            }
        """

        # Mensaje de estado
        self.label_mensaje = QLabel("Seleccione una ruta para comenzar")
        self.label_mensaje.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.label_mensaje.setStyleSheet("font-size: 12px; color: black;")
        controles_layout.addWidget(self.label_mensaje)

        # Sección de Ruta
        ruta_layout = QHBoxLayout()
        ruta_layout.setSpacing(10)
        ruta_layout.addWidget(QLabel("Ruta:"))
        self.combo_ruta = QComboBox()
        self.combo_ruta.setStyleSheet(control_style)
        self.combo_ruta.addItem("Seleccionar")
        self.cargar_rutas()
        self.combo_ruta.currentIndexChanged.connect(self.on_ruta_selected)
        ruta_layout.addWidget(self.combo_ruta)
        controles_layout.addLayout(ruta_layout)

        # Sección de Horario
        horario_layout = QHBoxLayout()
        horario_layout.setSpacing(10)
        horario_layout.addWidget(QLabel("Horario:"))
        self.combo_horario = QComboBox()
        self.combo_horario.setStyleSheet(control_style)
        self.combo_horario.addItem("Seleccione una ruta primero")
        self.combo_horario.currentIndexChanged.connect(self.on_horario_selected)    
        horario_layout.addWidget(self.combo_horario)
        controles_layout.addLayout(horario_layout)

        # Tren
        tren_layout = QHBoxLayout()
        tren_layout.setSpacing(10)
        tren_layout.addWidget(QLabel("Unidad:"))
        self.combo_tren = QComboBox()
        self.combo_tren.setStyleSheet(control_style)
        self.combo_tren.addItem("Seleccione un horario primero")
        tren_layout.addWidget(self.combo_tren)
        controles_layout.addLayout(tren_layout)

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        #self.btn_cancelar.clicked.connect(self.regresar_home)
        botones_layout.addWidget(self.btn_cancelar)
    
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.clicked.connect(self.validar_asignacion)
        botones_layout.addWidget(self.btn_consultar)

        self.btn_confirmar = QPushButton("Asignar")
        self.btn_confirmar.clicked.connect(self.confirmar_asignacion)
        botones_layout.addWidget(self.btn_confirmar)

        controles_layout.addLayout(botones_layout)

        # Panel derecho (imagen)
        self.panel_imagen = QScrollArea()
        self.panel_imagen.setWidgetResizable(True)
        self.panel_imagen.setMinimumWidth(200)
        self.panel_imagen.hide()  # Oculto inicialmente

        self.img_container = QWidget()
        self.img_layout = QVBoxLayout(self.img_container)
        self.img_ruta = QLabel()
        self.img_ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_ruta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.img_layout.addWidget(self.img_ruta)
        self.panel_imagen.setWidget(self.img_container)

        main_layout.addWidget(panel_controles)
        main_layout.addSpacing(20)  # Espacio adicional para mover la imagen a la derecha
        main_layout.addWidget(self.panel_imagen)

    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de InterfazAsignacion")
        self.cargar_rutas()
        self.combo_horario.clear()
        self.combo_horario.addItem("Seleccione una ruta primero")
        self.combo_tren.clear()
        self.combo_tren.addItem("Seleccione un horario primero")
        self.label_mensaje.setText("Seleccione una ruta para comenzar")

    def on_ruta_selected(self):
        if self.combo_ruta.currentIndex() > 0:
            id_ruta = self.combo_ruta.currentData()
            self.panel_imagen.show()
            self.setFixedSize(900, 600)
            self.load_route_image(id_ruta)
            self.cargar_horarios_disponibles(id_ruta)
        else:
            self.panel_imagen.hide()
            self.setFixedSize(500, 600)
            self.combo_horario.clear()
            self.combo_horario.addItem("Seleccione una ruta primero")
            self.combo_tren.clear()
            self.combo_tren.addItem("Seleccione un horario primero")

    def on_horario_selected(self, index):
        """Se ejecuta cuando se selecciona un horario"""
        if index > 0:  # Si se seleccionó un horario válido (no el primer item)
            id_horario = self.combo_horario.currentData()
            self.combo_tren.clear()
            self.combo_tren.addItem("Cargando trenes...")
            self.cargar_trenes_disponibles(id_horario)
        else:
            self.combo_tren.clear()
            self.combo_tren.addItem("Seleccione un horario primero")

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
            max_height = self.panel_imagen.height() - 50
            
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

    def cargar_horarios_disponibles(self, id_ruta):
        """Carga los horarios disponibles para la ruta seleccionada"""
        self.combo_horario.clear()
        self.combo_horario.addItem("Seleccionar")  # Asegura que el primer item esté presente
        self.label_mensaje.setText("Cargando horarios...")
        
        try:
            # Obtener duración estimada de la ruta
            duracion = self.obtener_duracion_ruta(id_ruta)
            if not duracion:
                self.combo_horario.addItem("No hay horarios disponibles")
                self.label_mensaje.setText("No se pudo obtener duración de la ruta")
                return

            # Consultar horarios disponibles que no estén asignados
            query = """
                SELECT H.ID_HORARIO, 
                       TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS SALIDA,
                       TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS LLEGADA
                FROM HORARIO H
                WHERE NOT EXISTS (
                    SELECT 1 FROM ASIGNACION_TREN A 
                    WHERE A.ID_HORARIO = H.ID_HORARIO
                )
                ORDER BY H.HORA_SALIDA_PROGRAMADA
            """
            
            horarios = self.db.fetch_all(query)
            
            if horarios:
                for id_horario, salida, llegada in horarios:
                    self.combo_horario.addItem(f"{salida} - {llegada}", id_horario)
                    # Calcular duración del horario en minutos
                    salida_dt = datetime.strptime(salida, '%H:%M:%S')
                    llegada_dt = datetime.strptime(llegada, '%H:%M:%S')
                    duracion_horario = (llegada_dt - salida_dt).total_seconds() / 60
                    self.combo_horario.currentIndexChanged.connect(self.on_horario_selected)
                    
                    # Solo mostrar horarios cuya duración sea >= a la duración estimada de la ruta
                    if duracion_horario >= duracion:
                        self.combo_horario.addItem(f"{salida} - {llegada}", id_horario)
                
                if self.combo_horario.count() > 1:  # Si hay más de la opción "Seleccionar"
                    self.label_mensaje.setText(f"{self.combo_horario.count()-1} horarios disponibles")
                else:
                    self.combo_horario.addItem("No hay horarios que cumplan con la duración")
                    self.label_mensaje.setText("No hay horarios que cumplan con la duración")
            else:
                self.combo_horario.addItem("No hay horarios disponibles")
                self.label_mensaje.setText("No hay horarios sin asignar")
                
        except Exception as e:
            print(f"Error al cargar horarios: {str(e)}")
            self.combo_horario.addItem("Error al cargar horarios")
            self.label_mensaje.setText("Error al cargar horarios")

    def cargar_trenes_disponibles(self, id_horario):
        """Carga todos los trenes activos, la validación se hará al asignar"""
        self.combo_tren.clear()
        self.label_mensaje.setText("Cargando todos los trenes activos...")
        
        try:
            # Consulta simple para obtener todos los trenes ACTIVOS
            query = """
                SELECT ID_TREN, NOMBRE 
                FROM TREN 
                WHERE ESTADO = 'ACTIVO'
                ORDER BY ID_TREN
            """
            trenes = self.db.fetch_all(query)
            
            if trenes:
                self.combo_tren.addItem("Seleccionar")
                for id_tren, nombre in trenes:
                    self.combo_tren.addItem(f"{id_tren} - {nombre}", id_tren)
                
                self.label_mensaje.setText(f"{len(trenes)} trenes activos cargados")
            else:
                self.combo_tren.addItem("No hay trenes activos")
                self.label_mensaje.setText("No hay trenes en estado ACTIVO")
                
        except Exception as e:
            print(f"Error al cargar trenes: {str(e)}")
            self.combo_tren.addItem("Error al cargar trenes")
            self.label_mensaje.setText("Error al cargar lista de trenes")
            

    def validar_asignacion(self):
        """Valida la asignación mostrando mensajes claros"""
        # Validación básica de campos
        if self.combo_ruta.currentIndex() <= 0:
            self.mostrar_mensaje("Error: Seleccione una ruta válida", False)
            return False
            
        if self.combo_horario.currentIndex() <= 0:
            self.mostrar_mensaje("Error: Seleccione un horario válido", False)
            return False
            
        if self.combo_tren.currentIndex() <= 0:
            self.mostrar_mensaje("Error: Seleccione un tren válido", False)
            return False
            
        id_tren = self.combo_tren.currentData()
        id_horario = self.combo_horario.currentData()
        
        # Verificar si el tren ya está asignado a este horario
        query = """
            SELECT COUNT(*) 
            FROM ASIGNACION_TREN 
            WHERE ID_TREN = :id_tren 
            AND ID_HORARIO = :id_horario
        """
        resultado = self.db.fetch_one(query, {
            "id_tren": id_tren,
            "id_horario": id_horario
        })
        
        if resultado and resultado[0] > 0:
            # Obtener info del tren para el mensaje
            query_tren = "SELECT NOMBRE FROM TREN WHERE ID_TREN = :id_tren"
            nombre_tren = self.db.fetch_one(query_tren, {"id_tren": id_tren})
            nombre = nombre_tren[0] if nombre_tren else f"ID {id_tren}"
            
            # Obtener info del horario para el mensaje
            query_horario = """
                SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS')
                FROM HORARIO WHERE ID_HORARIO = :id_horario
            """
            horario = self.db.fetch_one(query_horario, {"id_horario": id_horario})
            hora = horario[0] if horario else "horario desconocido"
            
            self.mostrar_mensaje(
                f"Error: El tren {nombre} ya está asignado a las {hora}",
                False
            )
            return False
            
        # Si todo está bien
        self.mostrar_mensaje("✓ Validación correcta. Puede confirmar la asignación", True)
        return True

    def confirmar_asignacion(self):
        try:
            # Obtener parámetros del formulario
            id_tren = self.combo_tren.currentData()
            id_ruta = self.combo_ruta.currentData()
            id_horario = self.combo_horario.currentData()

            # Mensajes de depuración
            print(f"\n[DEBUG] Parámetros para asignación:")
            print(f"Tren ID: {id_tren}, Ruta ID: {id_ruta}, Horario ID: {id_horario}")

            # Iniciar transacción
            cursor = self.db.connection.cursor()

            # Insertar en ASIGNACION_TREN (versión corregida)
            id_asignacion_var = cursor.var(oracledb.NUMBER)
            cursor.execute("""
                BEGIN
                    INSERT INTO ASIGNACION_TREN (
                        ID_ASIGNACION, 
                        ID_TREN, 
                        ID_RUTA, 
                        ID_HORARIO
                    )
                    VALUES (
                        (SELECT NVL(MAX(ID_ASIGNACION), 0) + 1 FROM ASIGNACION_TREN),
                        :id_tren, 
                        :id_ruta, 
                        :id_horario
                    )
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

            # Confirmar la inserción
            self.db.connection.commit()
            print("[DEBUG] ¡Inserción exitosa!")

            # Emitir señal para actualizar la interfaz de home
            self.asignacion_exitosa.emit()

            # Mostrar mensaje de éxito al usuario
            QMessageBox.information(
                self, 
                "Asignación Exitosa",
                f"Se asignó el tren {id_tren} a la ruta {id_ruta}"
            )

            # Actualizar interfaz
            self.actualizar_datos()
            self.db.event_manager.update_triggered.emit()
            print('se manda la señar acutalizar') 

        except oracledb.DatabaseError as e:
            error_obj = e.args[0]
            print(f"[ERROR ORACLE] Código: {error_obj.code}, Mensaje: {error_obj.message}")
            self.db.rollback()
            QMessageBox.critical(
                self, 
                "Error en Base de Datos",
                f"Error al guardar:\n{error_obj.message}"
            )

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
            "font-size: 12px; color: green;" if es_exito else 
            "font-size: 12px; color: red;")

    def obtener_duracion_ruta(self, id_ruta):
        """Obtiene la duración estimada de una ruta específica"""
        query = "SELECT DURACION_ESTIMADA FROM RUTA WHERE ID_RUTA = :id_ruta"
        resultado = self.db.fetch_one(query, {"id_ruta": id_ruta})
        
        if not resultado:
            raise ValueError(f"No se encontró la duración para la ruta ID {id_ruta}")
        
        return int(resultado[0])  # Asegurarnos que devuelve un entero