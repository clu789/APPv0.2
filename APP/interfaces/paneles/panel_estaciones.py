from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

class InterfazAgregarEstacion(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Campo: Nombre
        self.input_nombre = QLineEdit()
        layout.addWidget(QLabel("Nombre de la Estacion:"))
        layout.addWidget(self.input_nombre)

        # Botones
        botones_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_consultar = QPushButton("Consultar")
        self.btn_confirmar = QPushButton("Confirmar")
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)

        layout.addLayout(botones_layout)
        self.setLayout(layout)

        # Conexiones
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
        layout = QVBoxLayout()

        # Campo: Nombre
        self.input_nombre = QLineEdit()
        layout.addWidget(QLabel("Nombre de la Estacion:"))
        layout.addWidget(self.input_nombre)

        # Botones
        botones_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_consultar = QPushButton("Consultar")
        self.btn_confirmar = QPushButton("Confirmar")
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)

        layout.addLayout(botones_layout)
        self.setLayout(layout)

        # Conexiones
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
        
        try:
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
