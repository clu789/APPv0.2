from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

class InterfazAgregarEstacion(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.initUI()

    def initUI(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título del panel
        titulo = QLabel("Agregar Nueva Estación")
        titulo.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 2px solid #3498db;
        """)
        layout.addWidget(titulo)

        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 20, 10, 20)  # Más espacio vertical
        form_layout.setSpacing(15)

        # Campo: Nombre
        lbl_nombre = QLabel("Nombre de la Estación:")
        lbl_nombre.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.input_nombre.setMinimumHeight(35)  # Altura aumentada
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.input_nombre)

        layout.addWidget(form_container)

        # Contenedor para botones
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 10, 0, 0)
        botones_layout.setSpacing(15)

        # Botones con estilos consistentes
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)

        layout.addWidget(botones_container)
        layout.addStretch()

        self.setLayout(layout)

        # Conexiones se mantienen exactamente igual
        self.btn_consultar.clicked.connect(self.verificar_nombre)
        self.btn_confirmar.clicked.connect(self.insertar_estacion)

    def cancelar(self):
        self.input_nombre.clear()

    def verificar_nombre(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingresa un nombre.")
            return
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM ESTACION WHERE NOMBRE = :1", (nombre,))
        resultado = cursor.fetchone()
        if resultado and resultado[0] > 0:
            QMessageBox.warning(self, "Nombre duplicado", "Ya existe una estación con ese nombre.")
        else:
            QMessageBox.information(self, "Disponible", "El nombre está disponible.")

    def insertar_estacion(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        
        try:
            cursor = self.db.connection.cursor()
            id_estacion = self.db.fetch_one("SELECT NVL(MAX(ID_ESTACION), 0) + 1 FROM ESTACION")[0]
            cursor.execute(
                "INSERT INTO ESTACION (ID_ESTACION, NOMBRE) VALUES (:1, :2)",
                [id_estacion, nombre]
            )
            self.db.connection.commit()
            QMessageBox.information(self, "Éxito", "Estación agregado correctamente.")
            # Emitir la señal update_triggered
            self.db.event_manager.update_triggered.emit()
            self.cancelar()
        except Exception as e:
            QMessageBox.critical(self, "Error", "Ya existe una estación con ese nombre.")

class InterfazEditarEstacion(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.id_estacion = None  # Se asigna desde la tabla principal
        self.initUI()

    def initUI(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
    
        # Título del panel
        titulo = QLabel("Editar Estación Existente")
        titulo.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 2px solid #3498db;
        """)
        layout.addWidget(titulo)
    
        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 20, 10, 20)  # Más espacio vertical
        form_layout.setSpacing(15)
    
        # Campo: Nombre
        lbl_nombre = QLabel("Nombre de la Estación:")
        lbl_nombre.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.input_nombre.setMinimumHeight(35)  # Altura aumentada
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.input_nombre)
    
        layout.addWidget(form_container)
    
        # Contenedor para botones
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 10, 0, 0)
        botones_layout.setSpacing(15)
    
        # Botones con estilos consistentes
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
    
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
    
        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
    
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)
    
        layout.addWidget(botones_container)
        layout.addStretch()
    
        self.setLayout(layout)
    
        # Conexiones se mantienen exactamente igual
        self.btn_consultar.clicked.connect(self.verificar_nombre)
        self.btn_confirmar.clicked.connect(self.actualizar_estacion)

    def cancelar(self):
        self.input_nombre.clear()

    def cargar_datos(self, id_estacion, nombre):
        """Carga los datos de la estación seleccionada"""
        self.id_estacion = id_estacion
        self.input_nombre.setText(nombre)

    def verificar_nombre(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingresa un nombre.")
            return
        resultado = self.db.fetch_one("SELECT COUNT(*) FROM ESTACION WHERE NOMBRE = :1 AND ID_ESTACION != :2", [nombre, self.id_estacion])
        if resultado and resultado[0] > 0:
            QMessageBox.warning(self, "Nombre duplicado", "Ya existe otra estación con ese nombre.")
        else:
            QMessageBox.information(self, "Disponible", "El nombre está disponible.")

    def actualizar_estacion(self):
        if self.id_estacion is None:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ninguna estación.")
            return

        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar cambios")
        confirmacion.setText(f"¿Estás seguro de que deseas modificar la estación #{self.id_estacion}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
        
        try:
            if confirmacion.exec() == 2:
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "UPDATE ESTACION SET NOMBRE = :1 WHERE ID_ESTACION = :2",
                    [nombre, self.id_estacion]
                )
                self.db.connection.commit()
                QMessageBox.information(self, "Éxito", "Estación actualizada correctamente.")
                # Emitir la señal update_triggered
                self.db.event_manager.update_triggered.emit()
                self.cancelar()
        except Exception as e:
            QMessageBox.critical(self, "Error", "Ya existe una estación con ese nombre.")
