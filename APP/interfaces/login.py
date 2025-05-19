from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCore import Qt, pyqtSignal
from base_de_datos.db import DatabaseConnection
from utils import obtener_ruta_recurso

class LineEditSeleccion(QLineEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Espera un instante antes de seleccionar todo el texto (soluciona conflicto con el click del mouse)
        QTimer.singleShot(0, self.selectAll)

class LoginInterface(QWidget):
    login_exitoso = pyqtSignal(str)
    def __init__(self, db, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Inicio de sesión - TRACKSYNC")
        self.setGeometry(600, 100, 400, 700)
        
        self.db = db

        self.initUI()

    def initUI(self):
        # Layout principal con márgenes y espaciado consistentes
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(30)

        # Contenedor para el formulario (similar al de editar estación)
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(25)

        # Logo centrado
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap(obtener_ruta_recurso("APP/icons/TRACKSYNC.png")).scaled(300, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.logo)

        # Título con el mismo estilo que editar estación
        titulo = QLabel("TRACKSYNC")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 10px;
                border-bottom: 2px solid #3498db;
            }
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(titulo)

        # Campo de usuario
        self.label_usuario = QLabel("Usuario:")
        self.label_usuario.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.input_usuario = LineEditSeleccion()
        self.input_usuario.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 40px;
            }
        """)
        form_layout.addWidget(self.label_usuario)
        form_layout.addWidget(self.input_usuario)

        # Campo de contraseña
        self.label_contrasena = QLabel("Contraseña:")
        self.label_contrasena.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.input_contrasena = LineEditSeleccion()
        self.input_contrasena.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 40px;
            }
        """)
        self.input_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.label_contrasena)
        form_layout.addWidget(self.input_contrasena)

        # Botón de login con el mismo estilo que editar estación
        self.boton_login = QPushButton("Iniciar sesión")
        self.boton_login.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        form_layout.addWidget(self.boton_login)

        layout_principal.addWidget(form_container, 0, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout_principal)

        # Conexiones se mantienen exactamente igual
        self.intentos_login = 0
        self.boton_login.clicked.connect(self.verificar_credenciales)
        self.input_usuario.returnPressed.connect(self.boton_login.click)
        self.input_contrasena.returnPressed.connect(self.boton_login.click)

    def verificar_credenciales(self):
        usuario = self.input_usuario.text()
        contrasena = self.input_contrasena.text()

        if not usuario or not contrasena:
            QMessageBox.warning(self, "Campos vacíos", "Por favor ingresa usuario y contraseña.")
            return

        query = "SELECT COUNT(*) FROM USUARIO WHERE ID_USUARIO = :1 AND CONTRASENA = :2"
        resultado = self.db.fetch_all(query, (usuario, contrasena))

        if resultado and resultado[0][0] > 0:
            self.login_exitoso.emit(usuario)
            # Reinicia en caso de éxito
            self.intentos_login = 0
            self.input_usuario.clear()
            self.input_usuario.setFocus()
            self.input_contrasena.clear()
        else:
            self.intentos_login += 1
            if self.intentos_login >= 3:
                QMessageBox.critical(self, "Acceso denegado", "Has excedido el número de intentos permitidos. El programa se cerrará.")
                import sys
                sys.exit()
            else:
                QMessageBox.critical(self, "Error", "Usuario o contraseña incorrectos.")
                self.input_contrasena.clear()
                self.input_contrasena.setFocus()
