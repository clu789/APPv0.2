from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                            QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QBrush
from PyQt6.QtCore import QSize, QPoint


from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                            QFrame, QSpacerItem, QSizePolicy, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QBrush
from PyQt6.QtCore import QSize

from utils import obtener_ruta_recurso

class MenuLateral(QWidget):
    cambio_interfaz = pyqtSignal(int)
    cerrar_sesion = pyqtSignal()  # Señal para cerrar sesión
    def __init__(self, db, username):
        super().__init__()
        self.username = username
        self.db = db
        self.expanded_width = 150  # Ancho expandido
        self.collapsed_width = 50  # Ancho colapsado
        self.is_expanded = False
        self.setFixedWidth(self.collapsed_width)
        
        # Configuración de colores
        self.menu_color = QColor(52, 152, 219)  # Azul grajáceo
        self.button_color = QColor(72, 101, 129)  # Color botones
        self.text_color = QColor(0, 0, 0)  # Color texto
        
        self.initUI()

    def initUI(self):
        self.setStyleSheet(f"""
            background-color: {self.menu_color.name()};
            border-right: 1px solid #2d3e50;
        """)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Contenedor fijo para el botón ☰ (siempre visible)
        #self.btn_container = QFrame()
        #self.btn_container.setFixedHeight(40)
        #self.btn_container.setStyleSheet("background-color: transparent;")
        
        #btn_layout = QHBoxLayout(self.btn_container)
        #btn_layout.setContentsMargins(0, 0, 0, 0)
        
    # Botón ☰ centrado y fijo
        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setFixedSize(40, 40)  # Tamaño fijo
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.text_color.name()};
                font-size: 20px;
                border: none;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {self.button_color.name()};
            }}
        """)
        self.btn_toggle.clicked.connect(self.toggle_menu)
        
        #btn_layout.addWidget(self.btn_toggle, alignment=Qt.AlignmentFlag.AlignCenter)
        #self.main_layout.addWidget(self.btn_toggle)
        
        # 2. Encabezado con usuario (oculto por defecto)

        self.user_frame = QFrame()
        self.user_frame.setFixedHeight(100)
        self.user_frame.setStyleSheet(f"background-color: {self.menu_color.darker(120).name()};")
        
        user_layout = QVBoxLayout(self.user_frame)
        user_layout.setContentsMargins(5, 5, 5, 5)
        user_layout.setSpacing(5)


        
        # Icono de usuario (se ocultará cuando el menú esté colapsado)
        self.user_icon = QLabel()
        self.user_icon.setPixmap(QIcon(obtener_ruta_recurso("APP/icons/usuario.png")).pixmap(32, 32))
        self.user_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_icon.setStyleSheet("background-color: transparent;")
        
            
        self.user_label = QLabel()
        self.load_user_name()
        self.user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_label.setStyleSheet(f"""
            color: {self.text_color.name()};
            font-weight: bold;
            font-size: 12px;
        """)
        
        self.button_logout = QPushButton("Cerrar sesión")
        self.button_logout.setFixedHeight(20)
        #self.button_logout.setStyleSheet(f"""
        #    QPushButton {{
        #        background-color: transparent;
        #        color: {self.text_color.name()};
        #        padding: 8px 5px;
        #        border: none;
        #        text-align: left;
        #        font-size: 11px;
        #        border-radius: 4px;
        #    }}
        #    QPushButton:hover {{
        #        background-color: {self.button_color.name()};
        #    }}
        #""")
        self.button_logout.clicked.connect(self.cerrar_sesion.emit)

        user_layout.addWidget(self.user_icon, 0, Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(self.user_label, 0, Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(self.button_logout, 0, Qt.AlignmentFlag.AlignCenter)

        # 3. Separador (oculto por defecto)
        self.separator1 = QFrame()
        self.separator1.setFrameShape(QFrame.Shape.HLine)
        self.separator1.setStyleSheet("border: 1px solid #2d3e50;")
        self.separator1.setFixedHeight(1)
        
        # 4. Botones del menú
        self.button_container = QWidget()
        self.button_container.setStyleSheet("background-color: transparent;")
        self.button_layout = QVBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_layout.setSpacing(5)
        
        self.botones = [
            ("Home", QIcon(obtener_ruta_recurso("APP/icons/home.png")), 0),
            ("Horarios", QIcon(obtener_ruta_recurso("APP/icons/schedule.png")), 1),
            ("Monitoreo", QIcon(obtener_ruta_recurso("APP/icons/monitor.png")), 2),
            ("Incidencias", QIcon(obtener_ruta_recurso("APP/icons/alert.png")), 3),
            ("Infraestructura", QIcon(obtener_ruta_recurso("APP/icons/infra.png")), 4),
            ("Optimización", QIcon(obtener_ruta_recurso("APP/icons/optimize.png")), 5),
            ("Mejora", QIcon(obtener_ruta_recurso("APP/icons/mejora.png")), 6)
        ]
        
        self.button_widgets = []
        for texto, icono, idx in self.botones:
            btn = QPushButton()
            btn.setIcon(icono)
            btn.setIconSize(QSize(24, 24))
            btn.setText(texto)
            btn.setProperty("index", idx)
            btn.setToolTip(texto)
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.text_color.name()};
                    padding: 8px 5px;
                    border: none;
                    text-align: left;
                    font-size: 11px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {self.button_color.name()};
                }}
            """)
            
            btn.clicked.connect(lambda _, x=idx: self.cambio_interfaz.emit(x))
            self.button_layout.addWidget(btn)
            self.button_widgets.append(btn)
        
        # 5. Separador inferior (oculto por defecto)
        self.separator2 = QFrame()
        self.separator2.setFrameShape(QFrame.Shape.HLine)
        self.separator2.setStyleSheet("border: 1px solid #2d3e50;")
        self.separator2.setFixedHeight(1)
        
        # 6. Sección de reconocimientos (oculto por defecto)
        self.credits_frame = QFrame()
        self.credits_frame.setStyleSheet("background-color: transparent;")
        credits_layout = QVBoxLayout(self.credits_frame)
        credits_layout.setContentsMargins(5, 5, 5, 5)
        
        self.credits_label = QLabel("Reconocimientos")
        self.credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.credits_label.setStyleSheet(f"""
            color: {self.text_color.name()};
            font-size: 15px;
            font-style: italic;
        """)
        
        self.logo = QLabel()
        self.logo.setFixedSize(160, 80)
        self.logo.setPixmap(QPixmap(obtener_ruta_recurso("APP/icons/TRACKSYNC.png")).scaled(160, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo = QLabel("TRACKSYNC")
        self.titulo.setStyleSheet(f"""
            color: {self.text_color.name()};
            font-size: 22px;
            font-style: italic;
        """)
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.nombre1 = QLabel("Emiliano\nArista\nRodriguez")
        self.nombre1.setStyleSheet(f"""
            color: {self.text_color.name()};
            font-size: 10px;
            font-style: italic;
        """)
        self.nombre1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nombre2 = QLabel("Milton\nFlorencio\nArzate")
        self.nombre2.setStyleSheet(f"""
            color: {self.text_color.name()};
            font-size: 10px;
            font-style: italic;
        """)
        self.nombre2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nombre3 = QLabel("Nery\nYael\nHernandez\nVillavicencio")
        self.nombre3.setStyleSheet(f"""
            color: {self.text_color.name()};
            font-size: 10px;
            font-style: italic;
        """)
        self.nombre3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.nombre4 = QLabel("Jesus\nFidel\nVaca\nVilchiz")
        self.nombre4.setStyleSheet(f"""
            color: {self.text_color.name()};
            font-size: 10px;
            font-style: italic;
        """)
        self.nombre4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        credits_layout.addWidget(self.credits_label)
        credits_layout.addWidget(self.logo)
        credits_layout.addWidget(self.titulo)
        credits_layout.addWidget(self.nombre1)
        credits_layout.addWidget(self.nombre2)
        credits_layout.addWidget(self.nombre3)
        credits_layout.addWidget(self.nombre4)
        
        # Ensamblar el layout principal
        self.main_layout.addWidget(self.btn_toggle)
        self.main_layout.addWidget(self.user_frame)
        self.main_layout.addWidget(self.separator1)
        self.main_layout.addWidget(self.button_container)
        self.main_layout.addWidget(self.separator2)
        self.main_layout.addWidget(self.credits_frame)
        self.main_layout.addStretch()
        
        self.setLayout(self.main_layout)
        
        # Inicialmente ocultamos los elementos que no son botones
        self.update_visibility()

    def toggle_menu(self):
        """Alternar entre estado expandido y colapsado"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.animar_expansion()
        else:
            self.animar_colapso()
        
        self.update_visibility()

    def update_visibility(self):
        """Mostrar/ocultar elementos según el estado"""
        # Elementos que se muestran solo cuando está expandido
        elements_to_toggle = [
            self.user_frame,
            self.user_icon,
            self.user_label,
            self.user_icon,
            self.separator1,
            self.separator2,
            self.credits_frame,
            self.credits_label
        ]
        
        for element in elements_to_toggle:
            element.setVisible(self.is_expanded)
        
        # Para los botones, mostramos solo el icono cuando está colapsado
        for btn in self.button_widgets:
            if self.is_expanded:
                btn.setText(btn.toolTip())
            else:
                btn.setText("")

    def animar_expansion(self):
        """Animación para expandir el menú"""
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.expanded_width)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.start()

    def animar_colapso(self):
        """Animación para colapsar el menú"""
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.collapsed_width)
        self.animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self.animation.start()

    def leaveEvent(self, event):
        """Colapsar el menú cuando el cursor sale"""
        if self.is_expanded:
            self.is_expanded = False
            self.animar_colapso()
            self.update_visibility()
 
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo del menú
        painter.setBrush(QBrush(self.menu_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

        # Efecto de iluminación cuando está expandido
        if self.width() > self.collapsed_width:
            highlight = QColor(255, 255, 255, 20)
            painter.setBrush(QBrush(highlight))
            painter.drawRect(self.rect())
    
    def load_user_name(self):
        print(self.username)
        query = "SELECT NOMBRE||' '||APELLIDO_PATERNO FROM USUARIO WHERE ID_USUARIO = :1"
        result = self.db.fetch_all(query, (self.username,))
        print(result)
        if result:
            nombre_usuario = result[0][0]
            self.user_label.setText(f"{nombre_usuario}")