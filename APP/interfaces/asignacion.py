from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                            QPushButton, QMessageBox, QSizePolicy, 
                            QSpacerItem, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QDateTime, QTime, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap
import oracledb
from datetime import datetime, timedelta

class InterfazAsignacion(QWidget):
    asignacion_exitosa = pyqtSignal()  # Señal para recargar interfaces

    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.init_ui()
        self.validar_ventana_15min = False
        self.cargar_datos()
        
    def init_ui(self):
        self.setFixedSize(700, 400)  # Aumentamos el ancho total para mejor distribución

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)  # Reducimos el espacio entre paneles

        # Panel izquierdo (controles) - Ocupará aproximadamente el 60% del espacio
        panel_controles = QFrame()
        controles_layout = QVBoxLayout(panel_controles)
        controles_layout.setContentsMargins(15, 15, 15, 15)
        controles_layout.setSpacing(20)
    
        # Título del panel
        titulo = QLabel("Asignar Unidad a Ruta")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 10px;
                border-bottom: 2px solid #3498db;
                margin-bottom: 15px;
            }
        """)
        controles_layout.addWidget(titulo)
    
        # Mensaje de estado
        self.label_mensaje = QLabel("Seleccione una ruta para comenzar")
        self.label_mensaje.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.label_mensaje.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #7f8c8d;
                margin-bottom: 15px;
            }
        """)
        controles_layout.addWidget(self.label_mensaje)
    
        # Sección de Ruta
        ruta_layout = QVBoxLayout()
        ruta_layout.setSpacing(5)
        lbl_ruta = QLabel("Ruta:")
        lbl_ruta.setStyleSheet("font-weight: bold; font-size: 14px;")
        ruta_layout.addWidget(lbl_ruta)
        
        self.combo_ruta = QComboBox()
        self.combo_ruta.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        self.combo_ruta.addItem("Seleccionar")
        self.cargar_rutas()
        self.combo_ruta.currentIndexChanged.connect(self.on_ruta_selected)
        ruta_layout.addWidget(self.combo_ruta)
        controles_layout.addLayout(ruta_layout)
    
        # Separador
        separador1 = QFrame()
        separador1.setFrameShape(QFrame.Shape.HLine)
        separador1.setStyleSheet("color: #eee;")
        controles_layout.addWidget(separador1)
    
        # Sección de Horario
        horario_layout = QVBoxLayout()
        horario_layout.setSpacing(5)
        lbl_horario = QLabel("Horario:")
        lbl_horario.setStyleSheet("font-weight: bold; font-size: 14px;")
        horario_layout.addWidget(lbl_horario)
        
        self.combo_horario = QComboBox()
        self.combo_horario.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        self.combo_horario.addItem("Seleccione una ruta primero")
        self.combo_horario.currentIndexChanged.connect(self.on_horario_selected)
        horario_layout.addWidget(self.combo_horario)
        controles_layout.addLayout(horario_layout)
    
        # Separador
        separador2 = QFrame()
        separador2.setFrameShape(QFrame.Shape.HLine)
        separador2.setStyleSheet("color: #eee;")
        controles_layout.addWidget(separador2)
    
        # Sección de Tren
        tren_layout = QVBoxLayout()
        tren_layout.setSpacing(5)
        lbl_tren = QLabel("Unidad:")
        lbl_tren.setStyleSheet("font-weight: bold; font-size: 14px;")
        tren_layout.addWidget(lbl_tren)
        
        self.combo_tren = QComboBox()
        self.combo_tren.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        self.combo_tren.addItem("Seleccione un horario primero")
        tren_layout.addWidget(self.combo_tren)
        controles_layout.addLayout(tren_layout)
    
        controles_layout.addStretch()
    
        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)  # Más espacio entre botones
    
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        #self.btn_cancelar.clicked.connect(self.regresar_home)
        botones_layout.addWidget(self.btn_cancelar)
        
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_consultar.clicked.connect(self.validar_asignacion)
        botones_layout.addWidget(self.btn_consultar)
    
        self.btn_confirmar = QPushButton("Asignar")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_confirmar.clicked.connect(self.confirmar_asignacion)
        botones_layout.addWidget(self.btn_confirmar)
    
        controles_layout.addLayout(botones_layout)
        
        # Añadimos el panel de controles con stretch factor 1
        main_layout.addWidget(panel_controles, 6)  # 60% del espacio
    
        # Panel derecho (imagen) - Ocupará aproximadamente el 40% del espacio
        self.panel_imagen = QScrollArea()
        self.panel_imagen.setWidgetResizable(True)
        self.panel_imagen.setMinimumWidth(300)  # Ancho aumentado
        self.panel_imagen.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
        """)
        self.panel_imagen.hide()  # Oculto inicialmente
    
        self.img_container = QWidget()
        self.img_layout = QVBoxLayout(self.img_container)
        self.img_layout.setContentsMargins(10, 10, 10, 10)
        self.img_ruta = QLabel()
        self.img_ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_ruta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.img_layout.addWidget(self.img_ruta)
        self.panel_imagen.setWidget(self.img_container)
    
        main_layout.addWidget(self.panel_imagen, 4)  # Más espacio para la imagen
    
        self.setLayout(main_layout)

    def cargar_datos(self):
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
        self.combo_horario.addItem("Seleccionar")
        self.label_mensaje.setText("Cargando horarios...")
        
        try:
            duracion = self.obtener_duracion_ruta(id_ruta)
            if not duracion:
                self.combo_horario.addItem("No hay horarios disponibles")
                self.label_mensaje.setText("No se pudo obtener duración de la ruta")
                return

            # Obtener horarios asignados a esta ruta (solo si la validación está activa)
            horarios_asignados = []
            if self.validar_ventana_15min:
                query_horarios_asignados = """
                    SELECT H.HORA_SALIDA_PROGRAMADA, H.HORA_LLEGADA_PROGRAMADA
                    FROM ASIGNACION_TREN A
                    JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                    WHERE A.ID_RUTA = :id_ruta
                    ORDER BY H.HORA_SALIDA_PROGRAMADA
                """
                horarios_asignados = self.db.fetch_all(query_horarios_asignados, {"id_ruta": id_ruta})

            # Consultar todos los horarios
            query_horarios = """
                SELECT H.ID_HORARIO, 
                    H.HORA_SALIDA_PROGRAMADA,
                    H.HORA_LLEGADA_PROGRAMADA,
                    TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS SALIDA,
                    TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS LLEGADA
                FROM HORARIO H
                ORDER BY H.HORA_SALIDA_PROGRAMADA
            """
            todos_horarios = self.db.fetch_all(query_horarios)
            
            if todos_horarios:
                horarios_filtrados = []
                
                for id_horario, hora_salida, hora_llegada, salida_str, llegada_str in todos_horarios:
                    # Verificar duración
                    duracion_horario = (hora_llegada - hora_salida).total_seconds() / 60
                    if duracion_horario < duracion:
                        continue
                    
                    # Verificar si ya está asignado a esta ruta
                    query_asignado = """
                        SELECT COUNT(*) FROM ASIGNACION_TREN 
                        WHERE ID_HORARIO = :id_horario AND ID_RUTA = :id_ruta
                    """
                    asignado = self.db.fetch_one(query_asignado, {
                        "id_horario": id_horario,
                        "id_ruta": id_ruta
                    })
                    if asignado and asignado[0] > 0:
                        continue
                    
                    # Validación opcional de 15 minutos
                    if self.validar_ventana_15min:
                        valido = True
                        for asignado_salida, asignado_llegada in horarios_asignados:
                            if (abs((hora_salida - asignado_salida).total_seconds()) < 15 * 60 or
                                abs((hora_salida - asignado_llegada).total_seconds()) < 15 * 60 or
                                abs((hora_llegada - asignado_salida).total_seconds()) < 15 * 60 or
                                abs((hora_llegada - asignado_llegada).total_seconds()) < 15 * 60):
                                valido = False
                                break
                        if not valido:
                            continue
                    
                    horarios_filtrados.append((id_horario, salida_str, llegada_str))
                
                # Mostrar resultados
                if horarios_filtrados:
                    for id_horario, salida, llegada in horarios_filtrados:
                        self.combo_horario.addItem(f"{salida} - {llegada}", id_horario)
                    msg = f"{len(horarios_filtrados)} horarios disponibles"
                    if self.validar_ventana_15min:
                        msg += " (con ventana de 15 min)"
                    self.label_mensaje.setText(msg)
                else:
                    self.combo_horario.addItem("No hay horarios disponibles")
                    self.label_mensaje.setText("No hay horarios que cumplan los requisitos")
                    
        except Exception as e:
            print(f"Error al cargar horarios: {str(e)}")
            self.combo_horario.addItem("Error al cargar horarios")
            self.label_mensaje.setText("Error al cargar horarios")

    def validar_asignacion(self):
        """Valida la asignación con validaciones opcionales"""
        # Validaciones básicas (campos seleccionados)
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
        id_ruta = self.combo_ruta.currentData()
        
        # 1. Verificar si el tren ya está asignado a este horario
        query_tren_horario = """
            SELECT COUNT(*) FROM ASIGNACION_TREN 
            WHERE ID_TREN = :id_tren AND ID_HORARIO = :id_horario
        """
        resultado = self.db.fetch_one(query_tren_horario, {
            "id_tren": id_tren,
            "id_horario": id_horario
        })
        if resultado and resultado[0] > 0:
            self.mostrar_mensaje("Error: Este tren ya está asignado a este horario", False)
            return False
            
        # 2. Verificar si el horario ya está asignado a esta ruta
        query_ruta_horario = """
            SELECT COUNT(*) FROM ASIGNACION_TREN 
            WHERE ID_RUTA = :id_ruta AND ID_HORARIO = :id_horario
        """
        resultado_ruta = self.db.fetch_one(query_ruta_horario, {
            "id_ruta": id_ruta,
            "id_horario": id_horario
        })
        if resultado_ruta and resultado_ruta[0] > 0:
            self.mostrar_mensaje("Error: Este horario ya está asignado a esta ruta", False)
            return False
        
        # 3. Verificar solapamiento de tren
        query_horas = """
            SELECT HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA
            FROM HORARIO WHERE ID_HORARIO = :id_horario
        """
        horas = self.db.fetch_one(query_horas, {"id_horario": id_horario})
        if not horas:
            self.mostrar_mensaje("Error: No se pudo obtener información del horario", False)
            return False
            
        hora_salida, hora_llegada = horas
        
        query_solapamiento = """
            SELECT COUNT(*) FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            WHERE A.ID_TREN = :id_tren AND (
                (H.HORA_SALIDA_PROGRAMADA < :hora_llegada AND H.HORA_LLEGADA_PROGRAMADA > :hora_salida)
            )
        """
        resultado_solapamiento = self.db.fetch_one(query_solapamiento, {
            "id_tren": id_tren,
            "hora_salida": hora_salida,
            "hora_llegada": hora_llegada
        })
        if resultado_solapamiento and resultado_solapamiento[0] > 0:
            self.mostrar_mensaje("Error: El tren ya tiene una asignación que se solapa", False)
            return False
        
        # 4. Validación opcional de 15 minutos
        if self.validar_ventana_15min:
            query_ventana = """
                SELECT COUNT(*) FROM ASIGNACION_TREN A
                JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                WHERE A.ID_RUTA = :id_ruta AND (
                    ABS(H.HORA_SALIDA_PROGRAMADA - :hora_salida) < INTERVAL '15' MINUTE OR
                    ABS(H.HORA_LLEGADA_PROGRAMADA - :hora_salida) < INTERVAL '15' MINUTE OR
                    ABS(H.HORA_SALIDA_PROGRAMADA - :hora_llegada) < INTERVAL '15' MINUTE OR
                    ABS(H.HORA_LLEGADA_PROGRAMADA - :hora_llegada) < INTERVAL '15' MINUTE
                )
            """
            resultado_ventana = self.db.fetch_one(query_ventana, {
                "id_ruta": id_ruta,
                "hora_salida": hora_salida,
                "hora_llegada": hora_llegada
            })
            if resultado_ventana and resultado_ventana[0] > 0:
                self.mostrar_mensaje(
                    "Error: Debe haber al menos 15 minutos entre asignaciones en esta ruta", 
                    False
                )
                return False
        
        # 5. Verificar duración del horario
        duracion_ruta = self.obtener_duracion_ruta(id_ruta)
        duracion_horario = (hora_llegada - hora_salida).total_seconds() / 60
        if duracion_horario < duracion_ruta:
            self.mostrar_mensaje(
                f"Error: Duración del horario ({duracion_horario} min) < Ruta ({duracion_ruta} min)", 
                False
            )
            return False
        
        # Si pasa todas las validaciones
        self.mostrar_mensaje("✓ Validación correcta. Puede confirmar la asignación", True)
        return True

    def cargar_trenes_disponibles(self, id_horario):
        """Carga los trenes disponibles para el horario seleccionado que no tengan asignaciones solapadas"""
        self.combo_tren.clear()
        self.label_mensaje.setText("Cargando trenes...")
        
        try:
            # Primero obtener el rango de tiempo del horario seleccionado
            query_horario = """
                SELECT HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA
                FROM HORARIO
                WHERE ID_HORARIO = :id_horario
            """
            horario = self.db.fetch_one(query_horario, {"id_horario": id_horario})
            
            if not horario:
                self.combo_tren.addItem("Error: Horario no encontrado")
                return
                
            hora_salida, hora_llegada = horario
            
            # Consulta para obtener trenes disponibles que:
            # 1. Estén ACTIVOS
            # 2. No tengan asignaciones que se solapen con este horario
            query = """
                SELECT T.ID_TREN, T.NOMBRE
                FROM TREN T
                WHERE T.ESTADO = 'ACTIVO'
                AND NOT EXISTS (
                    SELECT 1
                    FROM ASIGNACION_TREN A
                    JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                    WHERE A.ID_TREN = T.ID_TREN
                    AND (
                        (H.HORA_SALIDA_PROGRAMADA < :hora_llegada AND H.HORA_LLEGADA_PROGRAMADA > :hora_salida)
                    )
                )
                ORDER BY T.ID_TREN
            """
            
            trenes = self.db.fetch_all(query, {
                "hora_salida": hora_salida,
                "hora_llegada": hora_llegada
            })
            
            if trenes:
                self.combo_tren.addItem("Seleccionar")
                for id_tren, nombre in trenes:
                    self.combo_tren.addItem(f"{id_tren} - {nombre}", id_tren)
                
                if self.combo_tren.count() > 1:
                    self.label_mensaje.setText(f"{len(trenes)} trenes disponibles")
                else:
                    self.combo_tren.clear()
                    self.combo_tren.addItem("No hay trenes disponibles")
                    self.label_mensaje.setText("No hay trenes para este horario")
            else:
                self.combo_tren.addItem("No hay trenes disponibles")
                self.label_mensaje.setText("No hay trenes disponibles")
                
        except Exception as e:
            print(f"Error al cargar trenes: {str(e)}")
            self.combo_tren.addItem("Error al cargar trenes")
            self.label_mensaje.setText("Error al cargar datos")

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
            self.cargar_datos()
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
    
    def configurar_validacion_15min(self, activar: bool):
        """Activa o desactiva la validación de ventana de 15 minutos"""
        self.validar_ventana_15min = activar
        if self.combo_ruta.currentIndex() > 0:
            # Recargar horarios si ya hay una ruta seleccionada
            self.cargar_horarios_disponibles(self.combo_ruta.currentData())

class InterfazModificarAsignacion(QWidget):
    modificacion_exitosa = pyqtSignal()  # Señal para recargar interfaces

    def __init__(self, main_window, db, username):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.username = username
        self.id_asignacion = None
        self.init_ui()
        self.validar_ventana_15min = False

    def init_ui(self):
        self.setFixedSize(700, 400)  # Mismo tamaño que el panel de agregar

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)  # Mismo espaciado

        # Panel izquierdo (controles) - 60% del espacio
        panel_controles = QFrame()
        controles_layout = QVBoxLayout(panel_controles)
        controles_layout.setContentsMargins(15, 15, 15, 15)
        controles_layout.setSpacing(20)  # Mismo espaciado vertical

        # Título del panel (cambiado a "Modificar Asignación")
        titulo = QLabel("Modificar Asignación")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 10px;
                border-bottom: 2px solid #3498db;
                margin-bottom: 15px;
            }
        """)
        controles_layout.addWidget(titulo)

        # Mensaje de estado
        self.label_mensaje = QLabel("Seleccione los nuevos valores")
        self.label_mensaje.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.label_mensaje.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #7f8c8d;
                margin-bottom: 15px;
            }
        """)
        controles_layout.addWidget(self.label_mensaje)

        # Sección de Ruta
        ruta_layout = QVBoxLayout()
        ruta_layout.setSpacing(5)
        lbl_ruta = QLabel("Ruta:")
        lbl_ruta.setStyleSheet("font-weight: bold; font-size: 14px;")
        ruta_layout.addWidget(lbl_ruta)

        self.combo_ruta = QComboBox()
        self.combo_ruta.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        self.combo_ruta.addItem("Cargando...")
        self.cargar_rutas()
        self.combo_ruta.currentIndexChanged.connect(self.on_ruta_selected)
        ruta_layout.addWidget(self.combo_ruta)
        controles_layout.addLayout(ruta_layout)

        # Separador
        separador1 = QFrame()
        separador1.setFrameShape(QFrame.Shape.HLine)
        separador1.setStyleSheet("color: #eee;")
        controles_layout.addWidget(separador1)

        # Sección de Horario
        horario_layout = QVBoxLayout()
        horario_layout.setSpacing(5)
        lbl_horario = QLabel("Horario:")
        lbl_horario.setStyleSheet("font-weight: bold; font-size: 14px;")
        horario_layout.addWidget(lbl_horario)

        self.combo_horario = QComboBox()
        self.combo_horario.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        self.combo_horario.addItem("Seleccione una ruta primero")
        self.combo_horario.currentIndexChanged.connect(self.on_horario_selected)
        horario_layout.addWidget(self.combo_horario)
        controles_layout.addLayout(horario_layout)

        # Separador
        separador2 = QFrame()
        separador2.setFrameShape(QFrame.Shape.HLine)
        separador2.setStyleSheet("color: #eee;")
        controles_layout.addWidget(separador2)

        # Sección de Tren
        tren_layout = QVBoxLayout()
        tren_layout.setSpacing(5)
        lbl_tren = QLabel("Unidad:")
        lbl_tren.setStyleSheet("font-weight: bold; font-size: 14px;")
        tren_layout.addWidget(lbl_tren)

        self.combo_tren = QComboBox()
        self.combo_tren.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        self.combo_tren.addItem("Seleccione un horario primero")
        tren_layout.addWidget(self.combo_tren)
        controles_layout.addLayout(tren_layout)

        controles_layout.addStretch()

        # Botones (mismo estilo pero con "Modificar" en naranja)
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        botones_layout.addWidget(self.btn_cancelar)

        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_consultar.clicked.connect(self.validar_modificacion)
        botones_layout.addWidget(self.btn_consultar)

        self.btn_confirmar = QPushButton("Modificar")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_confirmar.clicked.connect(self.confirmar_modificacion)
        botones_layout.addWidget(self.btn_confirmar)

        controles_layout.addLayout(botones_layout)

        # Panel derecho (imagen) - 40% del espacio
        self.panel_imagen = QScrollArea()
        self.panel_imagen.setWidgetResizable(True)
        self.panel_imagen.setMinimumWidth(300)
        self.panel_imagen.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
        """)
        self.panel_imagen.hide()

        self.img_container = QWidget()
        self.img_layout = QVBoxLayout(self.img_container)
        self.img_layout.setContentsMargins(10, 10, 10, 10)
        self.img_ruta = QLabel()
        self.img_ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_ruta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.img_layout.addWidget(self.img_ruta)
        self.panel_imagen.setWidget(self.img_container)

        main_layout.addWidget(panel_controles, 6)  # 60% del espacio
        main_layout.addWidget(self.panel_imagen, 4)  # 40% del espacio

        self.setLayout(main_layout)

    def set_asignacion(self, id_asignacion):
        """Carga los datos de la asignación basada en el ID de asignación"""
        self.id_asignacion = id_asignacion
        try:
            query = """
                SELECT A.ID_TREN, A.ID_RUTA, A.ID_HORARIO,
                    TO_CHAR(A.HORA_SALIDA_REAL, 'HH24:MI') AS SALIDA_REAL,
                    TO_CHAR(A.HORA_LLEGADA_REAL, 'HH24:MI') AS LLEGADA_REAL
                FROM ASIGNACION_TREN A
                WHERE A.ID_ASIGNACION = :id_asignacion
            """
            asignacion = self.db.fetch_one(query, {"id_asignacion": id_asignacion})

            if not asignacion:
                QMessageBox.warning(self, "Advertencia", "No se encontró la asignación")
                return False

            # Ahora los índices son correctos
            id_tren = asignacion[0]
            id_ruta = asignacion[1]
            id_horario = asignacion[2]
            hora_salida_real = asignacion[3]
            hora_llegada_real = asignacion[4]

            # Cargar datos en los combos
            self.cargar_rutas()
            self.combo_ruta.setCurrentIndex(self.combo_ruta.findData(id_ruta))

            self.cargar_horarios_disponibles(id_ruta)
            self.combo_horario.setCurrentIndex(self.combo_horario.findData(id_horario))

            self.cargar_trenes_disponibles(id_horario)
            self.combo_tren.setCurrentIndex(self.combo_tren.findData(id_tren))

            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos:\n{str(e)}")
            return False


    #def ocultar_panel_modificar(self):
    #    """Oculta el panel de modificación"""
    #    self.hide()

    def cargar_datos(self):
        """Recarga los datos de la interfaz"""
        self.cargar_rutas()
        self.combo_horario.clear()
        self.combo_horario.addItem("Seleccione una ruta primero")
        self.combo_tren.clear()
        self.combo_tren.addItem("Seleccione un horario primero")
        self.label_mensaje.setText("Seleccione los nuevos valores")

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
        self.combo_horario.addItem("Seleccionar")
        self.label_mensaje.setText("Cargando horarios...")
        
        try:
            duracion = self.obtener_duracion_ruta(id_ruta)
            if not duracion:
                self.combo_horario.addItem("No hay horarios disponibles")
                self.label_mensaje.setText("No se pudo obtener duración de la ruta")
                return

            # Obtener horarios asignados a esta ruta (excluyendo la asignación actual)
            horarios_asignados = []
            if self.validar_ventana_15min:
                query_horarios_asignados = """
                    SELECT H.HORA_SALIDA_PROGRAMADA, H.HORA_LLEGADA_PROGRAMADA
                    FROM ASIGNACION_TREN A
                    JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                    WHERE A.ID_RUTA = :id_ruta
                    AND A.ID_ASIGNACION != NVL(:id_asignacion, -1)
                    ORDER BY H.HORA_SALIDA_PROGRAMADA
                """
                horarios_asignados = self.db.fetch_all(query_horarios_asignados, {
                    "id_ruta": id_ruta,
                    "id_asignacion": self.id_asignacion
                })

            # Consultar todos los horarios
            query_horarios = """
                SELECT H.ID_HORARIO, 
                    H.HORA_SALIDA_PROGRAMADA,
                    H.HORA_LLEGADA_PROGRAMADA,
                    TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS SALIDA,
                    TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS LLEGADA
                FROM HORARIO H
                ORDER BY H.HORA_SALIDA_PROGRAMADA
            """
            todos_horarios = self.db.fetch_all(query_horarios)
            
            if todos_horarios:
                horarios_filtrados = []
                
                for id_horario, hora_salida, hora_llegada, salida_str, llegada_str in todos_horarios:
                    # Verificar duración
                    duracion_horario = (hora_llegada - hora_salida).total_seconds() / 60
                    if duracion_horario < duracion:
                        continue
                    
                    # Verificar si ya está asignado a esta ruta (excluyendo la asignación actual)
                    query_asignado = """
                        SELECT COUNT(*) FROM ASIGNACION_TREN 
                        WHERE ID_HORARIO = :id_horario 
                        AND ID_RUTA = :id_ruta
                        AND ID_ASIGNACION != NVL(:id_asignacion, -1)
                    """
                    asignado = self.db.fetch_one(query_asignado, {
                        "id_horario": id_horario,
                        "id_ruta": id_ruta,
                        "id_asignacion": self.id_asignacion
                    })
                    if asignado and asignado[0] > 0:
                        continue
                    
                    # Validación opcional de 15 minutos
                    if self.validar_ventana_15min:
                        valido = True
                        for asignado_salida, asignado_llegada in horarios_asignados:
                            if (abs((hora_salida - asignado_salida).total_seconds()) < 15 * 60 or
                                abs((hora_salida - asignado_llegada).total_seconds()) < 15 * 60 or
                                abs((hora_llegada - asignado_salida).total_seconds()) < 15 * 60 or
                                abs((hora_llegada - asignado_llegada).total_seconds()) < 15 * 60):
                                valido = False
                                break
                        if not valido:
                            continue
                    
                    horarios_filtrados.append((id_horario, salida_str, llegada_str))
                
                # Mostrar resultados
                if horarios_filtrados:
                    for id_horario, salida, llegada in horarios_filtrados:
                        self.combo_horario.addItem(f"{salida} - {llegada}", id_horario)
                    msg = f"{len(horarios_filtrados)} horarios disponibles"
                    if self.validar_ventana_15min:
                        msg += " (con ventana de 15 min)"
                    self.label_mensaje.setText(msg)
                else:
                    self.combo_horario.addItem("No hay horarios disponibles")
                    self.label_mensaje.setText("No hay horarios que cumplan los requisitos")
                    
        except Exception as e:
            print(f"Error al cargar horarios: {str(e)}")
            self.combo_horario.addItem("Error al cargar horarios")
            self.label_mensaje.setText("Error al cargar horarios")

    def validar_modificacion(self):
        """Valida la modificación con validaciones opcionales"""
        # Validaciones básicas (campos seleccionados)
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
        id_ruta = self.combo_ruta.currentData()
        
        # 1. Verificar si el tren ya está asignado a este horario (excluyendo la asignación actual)
        query_tren_horario = """
            SELECT COUNT(*) FROM ASIGNACION_TREN 
            WHERE ID_TREN = :id_tren 
            AND ID_HORARIO = :id_horario
            AND ID_ASIGNACION != :id_asignacion
        """
        resultado = self.db.fetch_one(query_tren_horario, {
            "id_tren": id_tren,
            "id_horario": id_horario,
            "id_asignacion": self.id_asignacion
        })
        if resultado and resultado[0] > 0:
            self.mostrar_mensaje("Error: Este tren ya está asignado a este horario", False)
            return False
            
        # 2. Verificar si el horario ya está asignado a esta ruta (excluyendo la asignación actual)
        query_ruta_horario = """
            SELECT COUNT(*) FROM ASIGNACION_TREN 
            WHERE ID_RUTA = :id_ruta 
            AND ID_HORARIO = :id_horario
            AND ID_ASIGNACION != :id_asignacion
        """
        resultado_ruta = self.db.fetch_one(query_ruta_horario, {
            "id_ruta": id_ruta,
            "id_horario": id_horario,
            "id_asignacion": self.id_asignacion
        })
        if resultado_ruta and resultado_ruta[0] > 0:
            self.mostrar_mensaje("Error: Este horario ya está asignado a esta ruta", False)
            return False
        
        # 3. Verificar solapamiento de tren (excluyendo la asignación actual)
        query_horas = """
            SELECT HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA
            FROM HORARIO WHERE ID_HORARIO = :id_horario
        """
        horas = self.db.fetch_one(query_horas, {"id_horario": id_horario})
        if not horas:
            self.mostrar_mensaje("Error: No se pudo obtener información del horario", False)
            return False
            
        hora_salida, hora_llegada = horas
        
        query_solapamiento = """
            SELECT COUNT(*) FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            WHERE A.ID_TREN = :id_tren 
            AND A.ID_ASIGNACION != :id_asignacion
            AND (
                (H.HORA_SALIDA_PROGRAMADA < :hora_llegada AND H.HORA_LLEGADA_PROGRAMADA > :hora_salida)
            )
        """
        resultado_solapamiento = self.db.fetch_one(query_solapamiento, {
            "id_tren": id_tren,
            "id_asignacion": self.id_asignacion,
            "hora_salida": hora_salida,
            "hora_llegada": hora_llegada
        })
        if resultado_solapamiento and resultado_solapamiento[0] > 0:
            self.mostrar_mensaje("Error: El tren ya tiene una asignación que se solapa", False)
            return False
        
        # 4. Validación opcional de 15 minutos
        if self.validar_ventana_15min:
            query_ventana = """
                SELECT COUNT(*) FROM ASIGNACION_TREN A
                JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                WHERE A.ID_RUTA = :id_ruta 
                AND A.ID_ASIGNACION != :id_asignacion
                AND (
                    ABS(H.HORA_SALIDA_PROGRAMADA - :hora_salida) < INTERVAL '15' MINUTE OR
                    ABS(H.HORA_LLEGADA_PROGRAMADA - :hora_salida) < INTERVAL '15' MINUTE OR
                    ABS(H.HORA_SALIDA_PROGRAMADA - :hora_llegada) < INTERVAL '15' MINUTE OR
                    ABS(H.HORA_LLEGADA_PROGRAMADA - :hora_llegada) < INTERVAL '15' MINUTE
                )
            """
            resultado_ventana = self.db.fetch_one(query_ventana, {
                "id_ruta": id_ruta,
                "id_asignacion": self.id_asignacion,
                "hora_salida": hora_salida,
                "hora_llegada": hora_llegada
            })
            if resultado_ventana and resultado_ventana[0] > 0:
                self.mostrar_mensaje(
                    "Error: Debe haber al menos 15 minutos entre asignaciones en esta ruta", 
                    False
                )
                return False
        
        # 5. Verificar duración del horario
        duracion_ruta = self.obtener_duracion_ruta(id_ruta)
        duracion_horario = (hora_llegada - hora_salida).total_seconds() / 60
        if duracion_horario < duracion_ruta:
            self.mostrar_mensaje(
                f"Error: Duración del horario ({duracion_horario} min) < Ruta ({duracion_ruta} min)", 
                False
            )
            return False
        
        # Si pasa todas las validaciones
        self.mostrar_mensaje("✓ Validación correcta. Puede confirmar la modificación", True)
        return True

    def cargar_trenes_disponibles(self, id_horario):
        """Carga los trenes disponibles para el horario seleccionado que no tengan asignaciones solapadas"""
        self.combo_tren.clear()
        self.label_mensaje.setText("Cargando trenes...")
        
        try:
            # Primero obtener el rango de tiempo del horario seleccionado
            query_horario = """
                SELECT HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA
                FROM HORARIO
                WHERE ID_HORARIO = :id_horario
            """
            horario = self.db.fetch_one(query_horario, {"id_horario": id_horario})
            
            if not horario:
                self.combo_tren.addItem("Error: Horario no encontrado")
                return
                
            hora_salida, hora_llegada = horario
            
            # Consulta para obtener trenes disponibles que:
            # 1. Estén ACTIVOS
            # 2. No tengan asignaciones que se solapen con este horario (excluyendo la asignación actual)
            query = """
                SELECT T.ID_TREN, T.NOMBRE
                FROM TREN T
                WHERE T.ESTADO = 'ACTIVO'
                AND (
                    T.ID_TREN = (
                        SELECT ID_TREN FROM ASIGNACION_TREN 
                        WHERE ID_ASIGNACION = :id_asignacion
                    ) OR
                    NOT EXISTS (
                        SELECT 1
                        FROM ASIGNACION_TREN A
                        JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                        WHERE A.ID_TREN = T.ID_TREN
                        AND A.ID_ASIGNACION != :id_asignacion
                        AND (
                            (H.HORA_SALIDA_PROGRAMADA < :hora_llegada AND H.HORA_LLEGADA_PROGRAMADA > :hora_salida)
                        )
                    )
                )
                ORDER BY T.ID_TREN
            """
            
            trenes = self.db.fetch_all(query, {
                "hora_salida": hora_salida,
                "hora_llegada": hora_llegada,
                "id_asignacion": self.id_asignacion
            })
            
            if trenes:
                self.combo_tren.addItem("Seleccionar")
                for id_tren, nombre in trenes:
                    self.combo_tren.addItem(f"{id_tren} - {nombre}", id_tren)
                
                if self.combo_tren.count() > 1:
                    self.label_mensaje.setText(f"{len(trenes)} trenes disponibles")
                else:
                    self.combo_tren.clear()
                    self.combo_tren.addItem("No hay trenes disponibles")
                    self.label_mensaje.setText("No hay trenes para este horario")
            else:
                self.combo_tren.addItem("No hay trenes disponibles")
                self.label_mensaje.setText("No hay trenes disponibles")
                
        except Exception as e:
            print(f"Error al cargar trenes: {str(e)}")
            self.combo_tren.addItem("Error al cargar trenes")
            self.label_mensaje.setText("Error al cargar datos")

    def confirmar_modificacion(self):
        try:
            # Validar antes de modificar
            if not self.validar_modificacion():
                return

            # Obtener parámetros del formulario
            id_tren = self.combo_tren.currentData()
            id_ruta = self.combo_ruta.currentData()
            id_horario = self.combo_horario.currentData()

            # Obtener datos actuales de la asignación para el historial
            query_asignacion_actual = """
                SELECT ID_TREN, ID_RUTA, ID_HORARIO,
                       TO_CHAR(HORA_SALIDA_REAL, 'HH24:MI') AS SALIDA_REAL,
                       TO_CHAR(HORA_LLEGADA_REAL, 'HH24:MI') AS LLEGADA_REAL
                FROM ASIGNACION_TREN
                WHERE ID_ASIGNACION = :id_asignacion
            """
            asignacion_actual = self.db.fetch_one(query_asignacion_actual, {
                "id_asignacion": self.id_asignacion
            })
            
            if not asignacion_actual:
                QMessageBox.warning(self, "Error", "No se encontró la asignación a modificar")
                return

            # Crear información para el historial
            info_historial = (
                f"Modificación de asignación:\n"
                f"Tren: {asignacion_actual[0]} → {id_tren}\n"
                f"Ruta: {asignacion_actual[1]} → {id_ruta}\n"
                f"Horario: {asignacion_actual[2]} → {id_horario}\n"
                f"Hora salida real: {asignacion_actual[3] or 'N/A'}\n"
                f"Hora llegada real: {asignacion_actual[4] or 'N/A'}"
            )

            # Iniciar transacción
            cursor = self.db.connection.cursor()

            # Actualizar la asignación
            cursor.execute("""
                UPDATE ASIGNACION_TREN SET
                    ID_TREN = :id_tren,
                    ID_RUTA = :id_ruta,
                    ID_HORARIO = :id_horario
                WHERE ID_ASIGNACION = :id_asignacion
            """, {
                "id_tren": id_tren,
                "id_ruta": id_ruta,
                "id_horario": id_horario,
                "id_asignacion": self.id_asignacion
            })

            # Registrar en historial
            id_historial = self.db.fetch_one("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")[0]
            cursor.execute("""
                INSERT INTO HISTORIAL (
                    ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_ASIGNACION, FECHA_REGISTRO
                ) VALUES (
                    :1, :2, :3, :4, SYSDATE
                )
            """, [id_historial, info_historial, self.username, self.id_asignacion])

            # Confirmar la transacción
            self.db.connection.commit()

            # Emitir señal para actualizar la interfaz de home
            self.modificacion_exitosa.emit()

            # Mostrar mensaje de éxito al usuario
            QMessageBox.information(
                self, 
                "Modificación Exitosa",
                f"Se modificó la asignación {self.id_asignacion} correctamente"
            )

            # Actualizar interfaz
            #self.ocultar_panel_modificar()
            self.db.event_manager.update_triggered.emit()

        except oracledb.DatabaseError as e:
            error_obj = e.args[0]
            print(f"[ERROR ORACLE] Código: {error_obj.code}, Mensaje: {error_obj.message}")
            self.db.rollback()
            QMessageBox.critical(
                self, 
                "Error en Base de Datos",
                f"Error al modificar:\n{error_obj.message}"
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
    
    def configurar_validacion_15min(self, activar: bool):
        """Activa o desactiva la validación de ventana de 15 minutos"""
        self.validar_ventana_15min = activar
        if self.combo_ruta.currentIndex() > 0:
            # Recargar horarios si ya hay una ruta seleccionada
            self.cargar_horarios_disponibles(self.combo_ruta.currentData())
        