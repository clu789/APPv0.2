from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
import logging
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from utils import obtener_ruta_recurso

class LineEditSeleccion(QLineEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Espera un instante antes de seleccionar todo el texto (soluciona conflicto con el click del mouse)
        QTimer.singleShot(0, self.selectAll)

class LoginInterface(QWidget):
    login_exitoso = pyqtSignal(str)
    login_es_admin = pyqtSignal()
    def __init__(self, db, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._logger = logging.getLogger(__name__)

        self.setWindowTitle("Inicio de sesión - TRACKSYNC")
        self.setGeometry(600, 100, 400, 700)
        
        self.db = db
        self._busy = False

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
                color: #197fbc;
                padding-bottom: 10px;
            }
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(titulo)

        # Campo de usuario
        self.label_usuario = QLabel("Usuario:")
        self.label_usuario.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")

        self.input_usuario = LineEditSeleccion()
        self.input_usuario.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 40px;
                color: #82caff;
            }
        """)
        form_layout.addWidget(self.label_usuario)
        form_layout.addWidget(self.input_usuario)

        # Campo de contraseña
        self.label_contrasena = QLabel("Contraseña:")
        self.label_contrasena.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc")

        self.input_contrasena = LineEditSeleccion()
        self.input_contrasena.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-height: 40px;
                color: #82caff;
            }
        """)
        self.input_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.label_contrasena)
        form_layout.addWidget(self.input_contrasena)

        # Botón de login con el mismo estilo que editar estación
        self.boton_login = QPushButton("Iniciar sesión")
        #self.boton_login.setStyleSheet("""
        #    QPushButton {
        #        padding: 12px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        font-size: 14px;
        #        font-weight: bold;
        #        min-height: 45px;
        #    }
        #    QPushButton:hover {
        #        background-color: #27ae60;
        #    }
        #""")
        self.boton_login.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-height: 45px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219653;
                padding: 9px 14px 7px 16px;  /* Efecto de profundidad */
            }
        """)
        form_layout.addWidget(self.boton_login)

        layout_principal.addWidget(form_container, 0, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout_principal)
        # Color de fondo de la ventana
        self.setStyleSheet("background-color: #0b1522;")

        # Conexiones se mantienen exactamente igual
        self.intentos_login = 0
        self.boton_login.clicked.connect(self.verificar_credenciales)
        self.input_usuario.returnPressed.connect(self.boton_login.click)
        self.input_contrasena.returnPressed.connect(self.boton_login.click)

    def verificar_credenciales(self):
        if self._busy:
            return
        usuario = (self.input_usuario.text() or "").strip()
        contrasena = self.input_contrasena.text() or ""

        if not usuario or not contrasena:
            msg = QMessageBox(self)
            msg.setWindowTitle("Campos vacíos")
            msg.setText("Por favor ingresa usuario y contraseña.")
            msg.setIcon(QMessageBox.Icon.Warning)
            # Cambia el color del texto (mensaje y botones) a blanco
            msg.setStyleSheet("QMessageBox QLabel, QMessageBox QPushButton { color: white; }")
            msg.exec()
            return

        # Anti doble-click: deshabilitar inputs y botón mientras se verifica
        self._set_busy(True)
        try:
            self._logger.info("Intento de login para usuario=%s", usuario)
            query = "SELECT COUNT(*) FROM USUARIO WHERE ID_USUARIO = :usuario AND CONTRASENA = :pwd"
            row = self.db.fetch_one(query, {"usuario": usuario, "pwd": contrasena})
            count_ok = bool(row and row[0] and int(row[0]) > 0)

            if count_ok:
                # No registrar contraseñas en logs
                self._logger.info("Login exitoso para usuario=%s", usuario)
                if usuario == "9999" and contrasena == "ADMIN_CONTROL_TRENES_0000":
                    self.intentos_login = 0
                    self.login_es_admin.emit()
                    self.input_usuario.clear()
                    self.input_usuario.setFocus()
                    self.input_contrasena.clear()
                else:
                    self.login_exitoso.emit(usuario)
                    # Reinicia en caso de éxito
                    self.intentos_login = 0
                    self.input_usuario.clear()
                    self.input_usuario.setFocus()
                    self.input_contrasena.clear()
            else:
                self.intentos_login += 1
                self._logger.warning("Login fallido para usuario=%s (intento %d)", usuario, self.intentos_login)
                if self.intentos_login >= 3:
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Acceso denegado")
                    msg.setText("Has excedido el número de intentos permitidos. El programa se cerrará.")
                    msg.setIcon(QMessageBox.Icon.Critical)
                    msg.setStyleSheet("QMessageBox QLabel, QMessageBox QPushButton { color: white; }")
                    msg.exec()
                    try:
                        # Cierre ordenado de la aplicación
                        from PyQt6.QtWidgets import QApplication
                        app = QApplication.instance()
                        if app is not None:
                            app.quit()
                        else:
                            import sys
                            sys.exit()
                    except Exception:
                        import sys
                        sys.exit()
                else:
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Error")
                    msg.setText("Usuario o contraseña incorrectos.")
                    msg.setIcon(QMessageBox.Icon.Critical)
                    msg.setStyleSheet("QMessageBox QLabel, QMessageBox QPushButton { color: white; }")
                    msg.exec()
                    self.input_contrasena.clear()
                    # Programar el enfoque para el siguiente ciclo de evento, cuando ya esté habilitado
                    QTimer.singleShot(0, lambda: self.input_contrasena.setFocus())
        finally:
            self._set_busy(False)

    def _set_busy(self, busy: bool):
        self._busy = busy
        try:
            self.input_usuario.setEnabled(not busy)
            self.input_contrasena.setEnabled(not busy)
            self.boton_login.setEnabled(not busy)
        except Exception:
            pass
