from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QComboBox, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt

class InterfazAgregarTren(QWidget):
    def __init__(self,main_window, db):
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
        titulo = QLabel("Agregar Nuevo Tren")
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
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        # Campo: Nombre
        lbl_nombre = QLabel("Nombre del Tren:")
        lbl_nombre.setStyleSheet("font-weight: bold;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.input_nombre)

        # Campo: Capacidad
        lbl_capacidad = QLabel("Capacidad:")
        lbl_capacidad.setStyleSheet("font-weight: bold;")
        self.input_capacidad = QLineEdit()
        self.input_capacidad.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(lbl_capacidad)
        form_layout.addWidget(self.input_capacidad)

        # Campo: Estado
        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet("font-weight: bold;")
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Activo", "En mantenimiento", "Fuera de servicio"])
        self.estado_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(lbl_estado)
        form_layout.addWidget(self.estado_combo)

        layout.addWidget(form_container)

        # Contenedor para botones
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 10, 0, 0)
        botones_layout.setSpacing(15)

        # Botones con estilos
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
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

        # Conexiones (se mantienen exactamente igual)
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
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
    
        # Título del panel
        titulo = QLabel("Editar Tren Existente")
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
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)
    
        # Campo: Nombre
        lbl_nombre = QLabel("Nombre del Tren:")
        lbl_nombre.setStyleSheet("font-weight: bold;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.input_nombre)
    
        # Campo: Capacidad
        lbl_capacidad = QLabel("Capacidad:")
        lbl_capacidad.setStyleSheet("font-weight: bold;")
        self.input_capacidad = QLineEdit()
        self.input_capacidad.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(lbl_capacidad)
        form_layout.addWidget(self.input_capacidad)
    
        # Campo: Estado
        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet("font-weight: bold;")
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Activo", "En mantenimiento", "Fuera de servicio"])
        self.estado_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(lbl_estado)
        form_layout.addWidget(self.estado_combo)
    
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
                padding: 8px 15px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
    
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
    
        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
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
