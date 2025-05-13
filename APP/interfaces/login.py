from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCore import Qt, pyqtSignal
from base_de_datos.db import DatabaseConnection

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
        self.setGeometry(150, 100, 1300, 700)
        
        self.db = db

        self.initUI()

    def initUI(self):
        layout_principal = QVBoxLayout()

        # Logo y título
        logo_titulo_layout = QHBoxLayout()

        self.logo = QLabel()
        self.logo.setFixedSize(400, 200)
        self.logo.setPixmap(QPixmap("APP/icons/TRACKSYNC.png").scaled(400, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.titulo = QLabel("TRACKSYNC")
        self.titulo.setFont(QFont("Arial", 50, QFont.Weight.Bold))
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        logo_titulo_layout.addWidget(self.logo)
        logo_titulo_layout.addWidget(self.titulo)
        logo_titulo_layout.setSpacing(100)

        layout_principal.addLayout(logo_titulo_layout)

        fuente_grande = QFont("Arial", 35)  # Tamaño 14 o más si quieres
        
        # Campo de usuario
        self.label_usuario = QLabel("Usuario:")
        self.label_usuario.setFont(fuente_grande)
        self.input_usuario = LineEditSeleccion()
        self.input_usuario.setFont(fuente_grande)
        layout_principal.addWidget(self.label_usuario)
        layout_principal.addWidget(self.input_usuario)

        # Campo de contraseña
        self.label_contrasena = QLabel("Contraseña:")
        self.label_contrasena.setFont(fuente_grande)
        self.input_contrasena = LineEditSeleccion()
        self.input_contrasena.setEchoMode(QLineEdit.EchoMode.Password)  # Oculta caracteres
        self.input_contrasena.setFont(fuente_grande)
        layout_principal.addWidget(self.label_contrasena)
        layout_principal.addWidget(self.input_contrasena)

        # Botón de iniciar sesión
        self.boton_login = QPushButton("Iniciar sesión")
        self.boton_login.setFont(fuente_grande)
        self.boton_login.setFixedHeight(50)
        layout_principal.addWidget(self.boton_login)

        # Alinear todo al centro verticalmente
        layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_principal.setSpacing(35)
        layout_principal.setContentsMargins(40, 20, 40, 20)

        self.setLayout(layout_principal)
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
