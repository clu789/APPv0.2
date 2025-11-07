from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy,
    QHBoxLayout,
)
from PyQt6.QtCore import (
    pyqtSignal,
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QSize,
    QEvent,
)
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QPaintEvent
import logging

from utils import obtener_ruta_recurso

logger = logging.getLogger(__name__)


class MenuLateral(QWidget):
    """Menú lateral de navegación con colapso/expansión, fijación y cabecera de usuario."""

    cambio_interfaz = pyqtSignal(int)
    cerrar_sesion = pyqtSignal()  # Señal para cerrar sesión

    def __init__(self, db, username) -> None:
        super().__init__()
        self.username = username
        self.db = db
        self.expanded_width = 150  # Ancho expandido
        self.collapsed_width = 50  # Ancho colapsado
        # Comenzar expandido y "fijado" por defecto (sin autocierre por mouse)
        self.is_expanded = True
        self.is_pinned = True  # Cuando está fijado, no se colapsa al salir el mouse
        # Usamos mínimos/máximos para que la animación de minimumWidth funcione correctamente
        self.setMinimumWidth(self.expanded_width)
        self.setMaximumWidth(self.expanded_width)
        
        # Configuración de colores
        self.menu_color = QColor(11, 21, 34)
        self.button_color = QColor(19, 34, 57, 1)  # Color botones
        self.text_color = QColor(130, 202, 255)  # Color texto
        
        self.initUI()

    def initUI(self) -> None:
        # Fondo base del widget (pintado también en paintEvent)
        self.setStyleSheet(f"background-color: {self.menu_color.name()};")
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Encabezado con botones (☰ y 📌)
        header_frame = QFrame()
        header_frame.setFixedHeight(44)
        header_frame.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(2, 2, 2, 2)
        header_layout.setSpacing(2)

        # Botón ☰: abre/cierra el menú (no controla fijación)
        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setFixedSize(40, 40)  # Tamaño fijo
        self.btn_toggle.setToolTip("Abrir/cerrar menú")
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

        # Toggle 📌: fija/libera el menú (controla autocierre por mouse)
        self.pin_toggle = QPushButton("📌")
        self.pin_toggle.setCheckable(True)
        self.pin_toggle.setChecked(self.is_pinned)
        self.pin_toggle.setFixedSize(40, 40)
        self.pin_toggle.setToolTip("Fijar menú (desactiva autocierre)")
        self.pin_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.text_color.name()};
                font-size: 16px;
                border: none;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {self.button_color.name()};
            }}
            QPushButton:checked {{
                color: #ffd166;  /* resalta cuando está fijado */
            }}
        """)
        self.pin_toggle.toggled.connect(self.on_pin_toggled)

        header_layout.addWidget(self.btn_toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(self.pin_toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch(1)
        
        # 2. Encabezado con usuario (oculto por defecto)

        self.user_frame = QFrame()
        self.user_frame.setFixedHeight(100)
        # Hacemos el frame transparente para que el fondo del padre (y su highlight) se vea uniforme
        self.user_frame.setStyleSheet("background-color: transparent;")

        user_layout = QVBoxLayout(self.user_frame)
        user_layout.setContentsMargins(5, 5, 5, 5)
        user_layout.setSpacing(5)


        
        # Icono de usuario (se ocultará cuando el menú esté colapsado)
        self.user_icon = QLabel()
        self.user_icon.setPixmap(QIcon(obtener_ruta_recurso("APP/icons/user.png")).pixmap(32, 32))
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
        self.button_logout.setStyleSheet("background-color: #197fbc; color: white;")
        self.button_logout.clicked.connect(self.cerrar_sesion.emit)

        user_layout.addWidget(self.user_icon, 0, Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(self.user_label, 0, Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(self.button_logout, 0, Qt.AlignmentFlag.AlignCenter)

        # 3. Separador (oculto por defecto)
        self.separator1 = QFrame()
        self.separator1.setFrameShape(QFrame.Shape.HLine)
        #self.separator1.setStyleSheet("border: 1px solid #2d3e50;")
        self.separator1.setFixedHeight(1)
        
        # 4. Botones del menú
        self.button_container = QWidget()
        # Fondo transparente: dejamos que el padre pinte el fondo uniforme
        self.button_container.setStyleSheet("background-color: transparent;")
        self.button_layout = QVBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_layout.setSpacing(5)
        
        self.botones = [
            ("Home", QIcon(obtener_ruta_recurso("APP/icons/casa.png")), 0),
            ("Horarios", QIcon(obtener_ruta_recurso("APP/icons/reloj.png")), 1),
            ("Monitoreo", QIcon(obtener_ruta_recurso("APP/icons/pantalla.png")), 2),
            ("Incidencias", QIcon(obtener_ruta_recurso("APP/icons/exclamacion.png")), 3),
            ("Infraestructura", QIcon(obtener_ruta_recurso("APP/icons/entrenar.png")), 4),
            ("Optimización", QIcon(obtener_ruta_recurso("APP/icons/llave-inglesa.png")), 5),
            ("Mejora", QIcon(obtener_ruta_recurso("APP/icons/mejorar.png")), 6)
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
                    color: white;
                    padding: 8px 5px;
                    border: none;
                    text-align: left;
                    font-size: 11px;
                    border-radius: 4px;
                    font-weight: bold;
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
        #self.separator2.setStyleSheet("border: 1px solid #2d3e50;")
        self.separator2.setFixedHeight(1)
        
        # 6. Sección de reconocimientos (oculto por defecto)
        self.credits_frame = QFrame()
        # Fondo transparente para coherencia con el padre
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
            color: #197fbc;
            font-size: 22px;
            font-style: italic;
        """)
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.nombre1 = QLabel("Emiliano\nArista\nRodriguez")
        self.nombre1.setStyleSheet(f"""
            color: white;
            font-size: 10px;
            font-style: italic;
            font-weight: bold;
        """)
        self.nombre1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nombre2 = QLabel("Milton\nFlorencio\nArzate")
        self.nombre2.setStyleSheet(f"""
            color: white;
            font-size: 10px;
            font-style: italic;
            font-weight: bold;
        """)
        self.nombre2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nombre3 = QLabel("Nery\nYael\nHernandez\nVillavicencio")
        self.nombre3.setStyleSheet(f"""
            color: white;
            font-size: 10px;
            font-style: italic;
            font-weight: bold;
        """)
        self.nombre3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.nombre4 = QLabel("Jesus\nFidel\nVaca\nVilchiz")
        self.nombre4.setStyleSheet(f"""
            color: white;
            font-size: 10px;
            font-style: italic;
            font-weight: bold;
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
        self.main_layout.addWidget(header_frame)
        self.main_layout.addWidget(self.user_frame)
        self.main_layout.addWidget(self.separator1)
        self.main_layout.addWidget(self.button_container)
        self.main_layout.addWidget(self.separator2)
        self.main_layout.addWidget(self.credits_frame)
        self.main_layout.addStretch()
        
        self.setLayout(self.main_layout)
        
        # Inicialmente ajustamos visibilidad según estado expandido
        self.update_visibility()
        
        # Truco de inicialización: forzar colapso y expansión en el siguiente ciclo
        # del event loop para asentar correctamente la geometría y evitar "aplastamiento" inicial.
        QTimer.singleShot(0, self._kickstart_layout)

    def _kickstart_layout(self) -> None:
        """Forzar un ciclo colapso/expansión rápido para estabilizar la geometría inicial sin animación."""
        # Colapsamos sin animación
        self.is_expanded = False
        self.setMinimumWidth(self.collapsed_width)
        self.setMaximumWidth(self.collapsed_width)
        self.update_visibility()
        # En el próximo tick expandimos de nuevo
        QTimer.singleShot(0, self._kickstart_expand)

    def _kickstart_expand(self) -> None:
        self.is_expanded = True
        self.setMinimumWidth(self.expanded_width)
        self.setMaximumWidth(self.expanded_width)
        self.update_visibility()

    def toggle_menu(self) -> None:
        """Alternar entre estado expandido y colapsado."""
        logger.debug("Toggle menú: expandido=%s", not self.is_expanded)
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.animar_expansion()
        else:
            self.animar_colapso()
        
        self.update_visibility()

    def update_visibility(self) -> None:
        """Mostrar/ocultar elementos según el estado."""
        # Elementos que se muestran solo cuando está expandido
        elements_to_toggle = [
            self.user_frame,
            self.user_icon,
            self.user_label,
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
        
        # El botón de fijar sólo debe verse cuando el menú está expandido
        if hasattr(self, 'pin_toggle'):
            self.pin_toggle.setVisible(self.is_expanded)

    def animar_expansion(self) -> None:
        """Animación para expandir el menú."""
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.expanded_width)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.finished.connect(self._on_expand_finished)
        self.animation.start()

    def animar_colapso(self) -> None:
        """Animación para colapsar el menú."""
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.collapsed_width)
        self.animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self.animation.finished.connect(self._on_collapse_finished)
        self.animation.start()

    def _on_expand_finished(self) -> None:
        # Fijamos los límites al ancho expandido, evitando que el layout lo aplaste
        self.setMinimumWidth(self.expanded_width)
        self.setMaximumWidth(self.expanded_width)

    def _on_collapse_finished(self) -> None:
        # Fijamos los límites al ancho colapsado para que el header no impida cerrar del todo
        self.setMinimumWidth(self.collapsed_width)
        self.setMaximumWidth(self.collapsed_width)

    def leaveEvent(self, event: QEvent) -> None:
        """Colapsar el menú cuando el cursor sale (solo si no está fijado)."""
        if self.is_expanded and not getattr(self, 'is_pinned', False):
            self.is_expanded = False
            self.animar_colapso()
            self.update_visibility()
        super().leaveEvent(event)
 
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo del menú
        painter.setBrush(QBrush(self.menu_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        # No dibujamos overlay extra: queremos que el menú expandido tenga
        # exactamente el mismo color que el colapsado.
    
    def load_user_name(self) -> None:
        """Carga el nombre del usuario desde BD y lo muestra en el encabezado.

        Intenta castear `username` a entero como ID; si falla, deja "Usuario" y registra aviso.
        """
        try:
            user_id = int(self.username)
        except Exception:
            logger.warning("ID de usuario no numérico en MenuLateral: %r", self.username)
            self.user_label.setText("Usuario")
            return

        try:
            row = self.db.fetch_one(
                """
                SELECT NOMBRE || ' ' || APELLIDO_PATERNO
                FROM USUARIO
                WHERE ID_USUARIO = :id_usuario
                """,
                {"id_usuario": user_id},
            )
            nombre = row[0] if row and row[0] else "Usuario"
            self.user_label.setText(str(nombre))
            logger.debug("Usuario cargado en menú: %s", nombre)
        except Exception as e:
            logger.exception("Error al cargar nombre de usuario %s: %s", user_id, e)
            self.user_label.setText("Usuario")

    def on_pin_toggled(self, checked: bool) -> None:
        """Maneja el cambio de estado fijado/no fijado del menú."""
        logger.debug("Pin toggled: %s", checked)
        self.is_pinned = checked
        if checked:
            self.pin_toggle.setToolTip("Menú fijado: no se autocierra al salir el mouse")
        else:
            self.pin_toggle.setToolTip("Menú libre: se autocierra al salir el mouse")