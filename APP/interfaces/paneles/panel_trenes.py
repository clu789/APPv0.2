from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QComboBox, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt

class InterfazAgregarTren(QWidget):
    def __init__(self,main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Campo: Nombre
        self.input_nombre = QLineEdit()
        layout.addWidget(QLabel("Nombre del Tren:"))
        layout.addWidget(self.input_nombre)

        # Campo: Capacidad
        self.input_capacidad = QLineEdit()
        layout.addWidget(QLabel("Capacidad:"))
        layout.addWidget(self.input_capacidad)

        # Campo: Estado
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Activo", "En mantenimiento", "Fuera de servicio"])
        layout.addWidget(QLabel("Estado:"))
        layout.addWidget(self.estado_combo)

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
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.verificar_nombre)
        self.btn_confirmar.clicked.connect(self.insertar_tren)

    def cancelar(self):
        self.input_nombre.clear()
        self.input_capacidad.clear()
        self.estado_combo.setCurrentIndex(0)

    def verificar_nombre(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingresa un nombre.")
            return
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM TREN WHERE NOMBRE = :1", (nombre,))
        resultado = cursor.fetchone()
        if resultado and resultado[0] > 0:
            QMessageBox.warning(self, "Nombre duplicado", "Ya existe un tren con ese nombre.")
        else:
            QMessageBox.information(self, "Disponible", "El nombre está disponible.")

    def insertar_tren(self):
        nombre = self.input_nombre.text().strip()
        try:
            capacidad = int(self.input_capacidad.text())
            if capacidad <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Error", "La capacidad debe ser un número mayor a 0.")
            return
        estado = self.estado_combo.currentText()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        
        try:
            cursor = self.db.connection.cursor()
            id_tren = self.db.fetch_one("SELECT NVL(MAX(ID_TREN), 0) + 1 FROM TREN")[0]
            cursor.execute(
                "INSERT INTO TREN (ID_TREN, NOMBRE, CAPACIDAD, ESTADO) VALUES (:1, :2, :3, UPPER(:4))",
                [id_tren, nombre, capacidad, estado]
            )
            self.db.connection.commit()
            QMessageBox.information(self, "Éxito", "Tren agregado correctamente.")
            # Emitir la señal update_triggered
            self.db.event_manager.update_triggered.emit()
            self.cancelar()
        except Exception as e:
            QMessageBox.critical(self, "Error", "Ya existe un tren con ese nombre.")

class InterfazEditarTren(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.id_tren = None  # Se llena con el ID del tren seleccionado
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Campo: Nombre
        self.input_nombre = QLineEdit()
        layout.addWidget(QLabel("Nombre del Tren:"))
        layout.addWidget(self.input_nombre)

        # Campo: Capacidad
        self.input_capacidad = QLineEdit()
        layout.addWidget(QLabel("Capacidad:"))
        layout.addWidget(self.input_capacidad)

        # Campo: Estado
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Activo", "En mantenimiento", "Fuera de servicio"])
        layout.addWidget(QLabel("Estado:"))
        layout.addWidget(self.estado_combo)

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
        self.btn_confirmar.clicked.connect(self.actualizar_tren)

    def cancelar(self):
        self.input_nombre.clear()
        self.input_capacidad.clear()
        self.estado_combo.setCurrentIndex(0)

    def cargar_datos(self, id_tren, nombre, capacidad, estado):
        """Carga los datos del tren seleccionado para editarlos"""
        self.id_tren = id_tren
        self.input_nombre.setText(nombre)
        self.input_capacidad.setText(str(capacidad))
        self.estado_combo.setCurrentText(estado)

    def verificar_nombre(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingresa un nombre.")
            return
        resultado = self.db.fetch_one("SELECT COUNT(*) FROM TREN WHERE NOMBRE = :1 AND ID_TREN != :2", [nombre, self.id_tren])
        if resultado and resultado[0] > 0:
            QMessageBox.warning(self, "Nombre duplicado", "Ya existe otro tren con ese nombre.")
        else:
            QMessageBox.information(self, "Disponible", "El nombre está disponible.")

    def actualizar_tren(self):
        if self.id_tren is None:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún tren.")
            return

        nombre = self.input_nombre.text().strip()
        try:
            capacidad = int(self.input_capacidad.text())
            if capacidad <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Error", "La capacidad debe ser un número mayor a 0.")
            return
        estado = self.estado_combo.currentText()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar cambios")
        confirmacion.setText(f"¿Estás seguro de que deseas modificar el tren #{self.id_tren}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
        
        try:
            if confirmacion.exec() == 2:
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "UPDATE TREN SET NOMBRE = :1, CAPACIDAD = :2, ESTADO = UPPER(:3) WHERE ID_TREN = :4",
                    [nombre, capacidad, estado, self.id_tren]
                )
                self.db.connection.commit()
                QMessageBox.information(self, "Éxito", "Tren actualizado correctamente.")
                # Emitir la señal update_triggered
                self.db.event_manager.update_triggered.emit()
                self.cancelar()
        except Exception as e:
            QMessageBox.critical(self, "Error", "Ya existe un tren con ese nombre.")
