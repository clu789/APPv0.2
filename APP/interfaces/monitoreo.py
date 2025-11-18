import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QProgressBar, QFrame, QGridLayout, QScrollArea, QHeaderView
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from datetime import datetime
from utils import obtener_ruta_recurso

class MonitoreoInterface(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window  # Referencia a la ventana principal
        
        self.setWindowTitle("Monitoreo en Tiempo Real")
        self.setGeometry(200, 200, 1000, 600)
        
        # Conexión a la base de datos
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Timer para coalescer recargas
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.load_real_time_data)

        self.initUI()
        self.load_real_time_data()
    
    def initUI(self):
        # Layout principal con scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor principal
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Configurar el scroll area
        self.scroll_area.setWidget(self.main_container)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.scroll_area)
        self.layout().setContentsMargins(0, 0, 0, 0)

        # --- Encabezado con logo y título ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 15)

        # Título principal centrado
        title_label = QLabel("Monitoreo en Tiempo Real")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: white;
                padding: 5px 0;
            }
        """)
        header_layout.addWidget(title_label)

        # Contenedor para logo a la derecha
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(20)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Logo
        self.logo = QLabel()
        self.logo.setFixedSize(160, 80)
        self.logo.setPixmap(QPixmap(obtener_ruta_recurso("APP/icons/TRACKSYNC.png")).scaled(
            160, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(self.logo)

        # Título debajo del logo
        self.titulo = QLabel("TRACKSYNC")
        self.titulo.setStyleSheet("""
            font-size: 22px;
            font-style: italic;
            color: #197fbc;
        """)
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(self.titulo)

        header_layout.addWidget(logo_container)
        self.main_layout.addLayout(header_layout)

        # Sección de tabla de asignaciones
        label_estado = QLabel("Asignaciones de Trenes")
        # fon size estaba en 20 xd
        label_estado.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #197fbc;
                padding-bottom: 5px;
            }
        """)
        self.main_layout.addWidget(label_estado)

        # Configuración de la tabla (manteniendo los mismos estilos)
        self.tabla_trenes = QTableWidget()
        self.tabla_trenes.setStyleSheet("""
            QTableWidget {
                border: 1px solid #0b1522;
                border-radius: 4px;
                background-color: #0b1522;
            }
            QHeaderView::section {
                background-color: #121f30ff;
                color: #55a2e7;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #55a2e7;
            }
            QTableWidget::item {
                background-color: #2a4254ff;
                color: white;
                padding: 6px;
                border-bottom: 1px solid #0b1522;
            }
        """)

        self.tabla_trenes.setColumnCount(8)
        self.tabla_trenes.setHorizontalHeaderLabels([
            "ID Asignación", 
            "ID Tren", 
            "Nombre Tren", 
            "ID Ruta", 
            "ID Horario", 
            "Salida Programada", 
            "Llegada Programada", 
            "Estado"
        ])

        # Ajustes de tabla mejorados
        self.tabla_trenes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_trenes.horizontalHeader().setStretchLastSection(True)
        self.tabla_trenes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tabla_trenes.setWordWrap(True)
        self.tabla_trenes.setAlternatingRowColors(True)
        self.tabla_trenes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_trenes.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_trenes.verticalHeader().setVisible(False)
        self.tabla_trenes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.main_layout.addWidget(self.tabla_trenes)

        # Panel de detalles (modificado para manejar el fixedHeight correctamente)
        self.detalle_panel = QFrame()
        self.detalle_panel.setStyleSheet("""
            QFrame {
                background-color: #0b1522;
                border: 1px solid #1f3a56;
                border-radius: 8px;
            }
        """)
        self.detalle_panel.setFixedHeight(400)  # Altura reducida pero funcional

        # Creamos un scroll area interno para el panel de detalles
        self.detalle_scroll = QScrollArea()
        self.detalle_scroll.setWidgetResizable(True)
        self.detalle_scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor para el contenido del detalle
        self.detalle_content = QWidget()
        self.detalle_layout = QVBoxLayout(self.detalle_content)
        self.detalle_layout.setContentsMargins(15, 15, 15, 15)
        self.detalle_layout.setSpacing(15)

        # Configuramos el scroll area
        self.detalle_scroll.setWidget(self.detalle_content)

        # Layout para el panel que contendrá el scroll area
        panel_layout = QVBoxLayout(self.detalle_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(self.detalle_scroll)

        self.main_layout.addWidget(self.detalle_panel)
        self.detalle_panel.setVisible(False)

        # Conexiones originales
        self.tabla_trenes.cellClicked.connect(self.on_row_selected)
        self.timer_progreso = QTimer()
        self.timer_progreso.timeout.connect(self.actualizar_barra_tiempo_real)
        
        # Color del fondo de la ventana
        self.setStyleSheet("background-color: #0b1522;")

    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        # Coalescer múltiples llamadas cercanas
        if self._refresh_timer.isActive():
            self._refresh_timer.stop()
        self._refresh_timer.start(150)
        self.logger.debug("Programada recarga de datos de MonitoreoInterface en 150 ms")

    def determinar_estado_horario(self, hora_salida_str, hora_llegada_str):
        """Determina si un horario está en curso, próximo o finalizado"""
        try:
            fmt = "%H:%M:%S"
            ahora = datetime.now().time()
            salida = datetime.strptime(hora_salida_str, fmt).time()
            llegada = datetime.strptime(hora_llegada_str, fmt).time()
            
            if ahora < salida:
                return "Próximamente"
            elif salida <= ahora <= llegada:
                return "En curso"
            else:
                return "Finalizado"
        except:
            return "Desconocido"

    def load_real_time_data(self):
        """Carga el estado actual de los trenes en servicio"""
        query = """
            SELECT 
                A.ID_ASIGNACION,
                T.ID_TREN, 
                T.NOMBRE, 
                R.ID_RUTA, 
                H.ID_HORARIO,
                TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS HORA_SALIDA,
                TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS HORA_LLEGADA,
                TO_CHAR(A.HORA_SALIDA_REAL, 'HH24:MI:SS') AS HORA_SALIDA_REAL,
                TO_CHAR(A.HORA_LLEGADA_REAL, 'HH24:MI:SS') AS HORA_LLEGADA_REAL
            FROM ASIGNACION_TREN A
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            ORDER BY H.HORA_SALIDA_PROGRAMADA ASC
        """
        try:
            asignaciones = self.db.fetch_all(query)
        except Exception:
            self.logger.exception("Error consultando asignaciones para monitoreo")
            self.tabla_trenes.setRowCount(0)
            return

        if not asignaciones:
            self.logger.debug("No se encontraron datos para la tabla de monitoreo")
            self.tabla_trenes.setRowCount(0)
            return

        # Repoblación básica de tabla minimizando parpadeos
        self.tabla_trenes.setUpdatesEnabled(False)
        try:
            self.tabla_trenes.setRowCount(len(asignaciones))
            for i, asignacion in enumerate(asignaciones):
                estado = self.determinar_estado_horario(asignacion[5], asignacion[6])
                self.tabla_trenes.setItem(i, 0, QTableWidgetItem(str(asignacion[0])))  # ID Asignación
                self.tabla_trenes.setItem(i, 1, QTableWidgetItem(str(asignacion[1])))  # ID Tren
                self.tabla_trenes.setItem(i, 2, QTableWidgetItem(asignacion[2]))      # Nombre Tren
                self.tabla_trenes.setItem(i, 3, QTableWidgetItem(str(asignacion[3]))) # ID Ruta
                self.tabla_trenes.setItem(i, 4, QTableWidgetItem(str(asignacion[4]))) # ID Horario
                self.tabla_trenes.setItem(i, 5, QTableWidgetItem(asignacion[5]))      # Hora Salida
                self.tabla_trenes.setItem(i, 6, QTableWidgetItem(asignacion[6]))      # Hora Llegada
                self.tabla_trenes.setItem(i, 7, QTableWidgetItem(estado))             # Estado
            # Asegurar que las columnas ocupen todo el ancho disponible
            header = self.tabla_trenes.horizontalHeader()
            for c in range(self.tabla_trenes.columnCount()):
                header.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)
            header.setStretchLastSection(True)
            self.tabla_trenes.resizeRowsToContents()
        finally:
            self.tabla_trenes.setUpdatesEnabled(True)

    def on_row_selected(self, row, column):
        # Evitar solapes del timer de progreso
        try:
            if hasattr(self, 'timer_progreso'):
                self.timer_progreso.stop()
        except Exception:
            pass

        self.limpiar_panel_detalles()
        
        item = self.tabla_trenes.item(row, 0)
        if item is None:
            return
        id_asignacion = item.text()
        self.refrescar_detalles_asignacion(id_asignacion)
        try:
            self.timer_progreso.start(1000)
        except Exception:
            pass

    def refrescar_detalles_asignacion(self, id_asignacion):
        self.limpiar_panel_detalles()
        while self.detalle_layout.count():
            child = self.detalle_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Mostrar el panel de detalles
        self.detalle_panel.setVisible(True)

        # Obtener datos completos de la asignación
        query = """
            SELECT 
                A.ID_ASIGNACION,
                T.ID_TREN, T.NOMBRE, T.CAPACIDAD, T.ESTADO,
                R.ID_RUTA, R.DURACION_ESTIMADA,
                H.ID_HORARIO,
                TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS HORA_SALIDA_PROG,
                TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS HORA_LLEGADA_PROG,
                TO_CHAR(A.HORA_SALIDA_REAL, 'HH24:MI:SS') AS HORA_SALIDA_REAL,
                TO_CHAR(A.HORA_LLEGADA_REAL, 'HH24:MI:SS') AS HORA_LLEGADA_REAL,
                E1.NOMBRE AS ESTACION_ORIGEN,
                E2.NOMBRE AS ESTACION_DESTINO
            FROM ASIGNACION_TREN A
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN RUTA_DETALLE RD1 ON R.ID_RUTA = RD1.ID_RUTA AND RD1.ORDEN = (
                SELECT MIN(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = R.ID_RUTA
            )
            JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
            JOIN RUTA_DETALLE RD2 ON R.ID_RUTA = RD2.ID_RUTA AND RD2.ORDEN = (
                SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = R.ID_RUTA
            )
            JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
            WHERE A.ID_ASIGNACION = :id
        """
        try:
            datos = self.db.fetch_one(query, {'id': id_asignacion})
        except Exception:
            self.logger.exception("Error obteniendo detalles de asignación %s", id_asignacion)
            self.detalle_panel.setVisible(True)
            return

        if not datos:
            self.logger.error("No se encontraron datos para la asignación %s", id_asignacion)
            self.detalle_panel.setVisible(True)  # Mostrar el panel vacío
            return

        if len(datos) < 15:
            self.logger.warning("Datos incompletos para la asignación %s: %s", id_asignacion, datos)

        # Guardar datos importantes para la barra de progreso
        self.hora_salida = datos[8] if len(datos) > 8 else "N/A"
        self.hora_llegada = datos[9] if len(datos) > 9 else "N/A"
        self.id_asignacion = id_asignacion

        estacion_origen = datos[12] if len(datos) > 12 and datos[12] else "Desconocido"
        estacion_destino = datos[13] if len(datos) > 13 and datos[13] else "Desconocido"

        # Encabezado dinámico con estado (badge)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        header_texts = QVBoxLayout()
        titulo = QLabel(f"{datos[2]}")
        titulo.setStyleSheet("""
            QLabel { font-size: 18px; font-weight: 700; color: #eaf3ff; }
        """)
        subtitulo = QLabel(f"Asignación #{id_asignacion} • Ruta {datos[5]} • Horario {datos[7]}")
        subtitulo.setStyleSheet("""
            QLabel { font-size: 12px; color: #9fb3c8; }
        """)
        header_texts.addWidget(titulo)
        header_texts.addWidget(subtitulo)

        estado = self.determinar_estado_horario(datos[8], datos[9])
        estado_badge = QLabel(estado)
        estado_bg, estado_fg = self._colores_estado(estado)
        estado_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {estado_bg};
                color: {estado_fg};
                border: 1px solid #1f3a56;
                border-radius: 12px;
                padding: 4px 10px;
                font-weight: 600;
            }}
        """)
        header.addLayout(header_texts)
        header.addStretch()
        header.addWidget(estado_badge)

        # Botón cerrar panel
        btn_close = QPushButton("✕")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFixedSize(28, 28)
        btn_close.setToolTip("Cerrar detalles")
        btn_close.setStyleSheet("""
            QPushButton {
                color: #cfd8e3; background-color: #0e1a26; border: 1px solid #1f3a56;
                border-radius: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #122335; color: #ffffff; }
            QPushButton:pressed { background-color: #091521; }
        """)
        btn_close.clicked.connect(self.cerrar_panel_detalles)
        header.addSpacing(6)
        header.addWidget(btn_close)

        self.detalle_layout.addLayout(header)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #1f3a56;")
        self.detalle_layout.addWidget(sep)

        # Barra de progreso visual
        barra_layout = QVBoxLayout()
        barra_layout.setContentsMargins(0, 0, 0, 0)

        barra_superior = QHBoxLayout()

        label_inicio = QLabel(estacion_origen)
        label_inicio.setStyleSheet("""
            QLabel {
                color: #eaf3ff; background-color: #0e1a26; border: 1px solid #1f3a56;
                border-radius: 10px; padding: 4px 8px; font-weight: 600;
            }
        """)
        label_inicio.setAlignment(Qt.AlignmentFlag.AlignLeft)

        label_fin = QLabel(estacion_destino)
        label_fin.setStyleSheet("""
            QLabel {
                color: #eaf3ff; background-color: #0e1a26; border: 1px solid #1f3a56;
                border-radius: 10px; padding: 4px 8px; font-weight: 600;
            }
        """)
        label_fin.setAlignment(Qt.AlignmentFlag.AlignRight)

        barra_superior.addWidget(label_inicio)
        barra_superior.addStretch()
        barra_superior.addWidget(label_fin)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% completado")
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #0e1a26; color: #ffffff; border: 1px solid #1f3a56;
                border-radius: 8px; text-align: center; height: 14px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                  stop:0 #197fbc, stop:1 #55a2e7);
                border-radius: 8px;
            }
        """)

        barra_inferior = QHBoxLayout()
        hora_salida_lbl = QLabel(f"Salida {self.hora_salida}")
        hora_salida_lbl.setStyleSheet("QLabel { color: #9fb3c8; font-family: Consolas, 'Courier New', monospace; }")
        hora_llegada_lbl = QLabel(f"Llegada {self.hora_llegada}")
        hora_llegada_lbl.setStyleSheet("QLabel { color: #9fb3c8; font-family: Consolas, 'Courier New', monospace; }")
        barra_inferior.addWidget(hora_salida_lbl)
        barra_inferior.addStretch()
        barra_inferior.addWidget(hora_llegada_lbl)

        barra_layout.addLayout(barra_superior)
        barra_layout.addWidget(self.progress_bar)
        barra_layout.addLayout(barra_inferior)
        self.detalle_layout.addLayout(barra_layout)

        # Detalles en un grid layout
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(10)

        # Información del tren
        grid_layout.addWidget(self._kv_label("ID Tren:"), 0, 0)
        grid_layout.addWidget(self._value_label(str(datos[1])), 0, 1)
        
        grid_layout.addWidget(self._kv_label("Nombre Tren:"), 1, 0)
        grid_layout.addWidget(self._value_label(datos[2]), 1, 1)
        
        grid_layout.addWidget(self._kv_label("Capacidad:"), 2, 0)
        grid_layout.addWidget(self._value_label(f"{datos[3]} pax"), 2, 1)
        
        grid_layout.addWidget(self._kv_label("Estado del Tren:"), 3, 0)
        grid_layout.addWidget(self._value_label(datos[4]), 3, 1)

        # Información de la ruta
        grid_layout.addWidget(self._kv_label("ID Ruta:"), 0, 2)
        grid_layout.addWidget(self._value_label(str(datos[5])), 0, 3)
        
        grid_layout.addWidget(self._kv_label("Duración Estimada:"), 1, 2)
        grid_layout.addWidget(self._value_label(f"{datos[6]} min"), 1, 3)
        
        grid_layout.addWidget(self._kv_label("ID Horario:"), 2, 2)
        grid_layout.addWidget(self._value_label(str(datos[7])), 2, 3)

        # Horarios programados
        grid_layout.addWidget(self._kv_label("Salida Programada:"), 4, 0)
        grid_layout.addWidget(self._mono_value_label(datos[8]), 4, 1)
        
        grid_layout.addWidget(self._kv_label("Llegada Programada:"), 5, 0)
        grid_layout.addWidget(self._mono_value_label(datos[9]), 5, 1)

        # Horarios reales (si existen)
        if datos[10]:
            grid_layout.addWidget(self._kv_label("Salida Real:"), 4, 2)
            grid_layout.addWidget(self._mono_value_label(datos[10]), 4, 3)
        
        if datos[11]:
            grid_layout.addWidget(self._kv_label("Llegada Real:"), 5, 2)
            grid_layout.addWidget(self._mono_value_label(datos[11]), 5, 3)

        self.detalle_layout.addLayout(grid_layout)

    def cerrar_panel_detalles(self):
        """Oculta el panel de detalles y detiene actualizaciones en tiempo real."""
        try:
            if hasattr(self, 'timer_progreso'):
                self.timer_progreso.stop()
        except Exception:
            pass
        self.limpiar_panel_detalles()
        self.detalle_panel.setVisible(False)

    def _kv_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("QLabel { color: #197fbc; font-weight: 600; }")
        return lbl

    def _value_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("QLabel { color: #eaf3ff; }")
        return lbl

    def _mono_value_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("QLabel { color: #eaf3ff; font-family: Consolas, 'Courier New', monospace; }")
        return lbl

    def _colores_estado(self, estado: str):
        estado = (estado or '').lower()
        if 'curso' in estado:      # En curso
            return ("#114d2e", "#9ff2bd")
        if 'próxim' in estado or 'proxim' in estado:  # Próximamente
            return ("#5a3a13", "#ffd79a")
        if 'finaliz' in estado:    # Finalizado
            return ("#2c2f33", "#c7d1db")
        return ("#1f3a56", "#eaf3ff")

    def actualizar_barra_tiempo_real(self):
        if not hasattr(self, 'hora_salida') or not hasattr(self, 'hora_llegada'):
            return

        try:
            fmt = "%H:%M:%S"
            ahora = datetime.now().time()
            salida = datetime.strptime(self.hora_salida, fmt).time()
            llegada = datetime.strptime(self.hora_llegada, fmt).time()

            total = (datetime.combine(datetime.today(), llegada) - datetime.combine(datetime.today(), salida)).total_seconds()
            transcurrido = (datetime.combine(datetime.today(), ahora) - datetime.combine(datetime.today(), salida)).total_seconds()

            if transcurrido < 0:
                progreso = 0
            elif transcurrido > total:
                progreso = 100
            else:
                progreso = (transcurrido / total) * 100

            self.progress_bar.setValue(int(progreso))
        except Exception:
            self.logger.exception("Error actualizando barra de progreso")
            self.progress_bar.setValue(0)

    def limpiar_panel_detalles(self):
        """Limpia completamente el panel de detalles"""
        # Detener el timer si está activo
        try:
            if hasattr(self, 'timer_progreso'):
                self.timer_progreso.stop()
        except Exception:
            pass
        
        # Eliminar todos los widgets del layout
        while self.detalle_layout.count():
            item = self.detalle_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                # Si es un layout, eliminamos sus widgets recursivamente
                if item.layout() is not None:
                    self.limpiar_layout_recursivo(item.layout())
        
        # Opcional: eliminar cualquier layout vacío que quede
        for i in reversed(range(self.detalle_layout.count())):
            item = self.detalle_layout.itemAt(i)
            if item.layout():
                self.limpiar_layout_recursivo(item.layout())
                self.detalle_layout.removeItem(item)

    def limpiar_layout_recursivo(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.limpiar_layout_recursivo(item.layout())