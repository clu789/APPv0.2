import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QPushButton, QHBoxLayout, 
                             QSizePolicy, QHeaderView, QStackedWidget, QScrollArea,
                             QMessageBox, QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer
from interfaces.paneles.panel_incidencias import InterfazAgregarIncidencia
from PyQt6.QtGui import QPixmap
from utils import obtener_ruta_recurso

class GestionIncidencias(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Timer para coalescer recargas
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.load_incidencias)

        self.setWindowTitle("Gestión de Incidencias")
        self.setGeometry(100, 100, 1000, 600)

        self.initUI()
        self.load_incidencias()

    def initUI(self):
        # Layout principal con scroll (solo para diseño)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor principal (usar todo el ancho)
        self.main_container = QWidget()
        self.main_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
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
        title_label = QLabel("Gestión de Incidencias")
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
        label_estado = QLabel("Incidencias por Asignaciones de Trenes")
        label_estado.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #197fbc;
                padding-bottom: 5px;
            }
        """)
        self.main_layout.addWidget(label_estado)

        # Contenedor para el contenido (usar todo el ancho)
        self.content_container = QWidget()
        self.content_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        # === Sección 1: Incidencias del día y todas ===
        seccion1_layout = QHBoxLayout()
        seccion1_layout.setContentsMargins(0, 0, 0, 0)
        seccion1_layout.setSpacing(15)

        # Tabla incidencias por resolver
        self.tabla_no_resueltas = QTableWidget()
        self.tabla_no_resueltas.setColumnCount(5)
        self.tabla_no_resueltas.setHorizontalHeaderLabels(["ID", "ID Asignacion", "Tipo", "Descripción", "Fecha y Hora"])
        self._configurar_tabla(self.tabla_no_resueltas)
        self.tabla_no_resueltas.itemSelectionChanged.connect(self._controlar_boton_resolver)
        seccion1_layout.addWidget(self._con_titulo("Incidencias por Resolver", self.tabla_no_resueltas))

        # Tabla incidencias resueltas
        self.tabla_resueltas = QTableWidget()
        self.tabla_resueltas.setColumnCount(5)
        self.tabla_resueltas.setHorizontalHeaderLabels(["ID", "ID Asignacion", "Tipo", "Descripción", "Fecha y Hora"])
        self._configurar_tabla(self.tabla_resueltas)
        seccion1_layout.addWidget(self._con_titulo("Incidencias Resueltas", self.tabla_resueltas))

        content_layout.addLayout(seccion1_layout)

        # === Sección 2: Afectaciones ===
        seccion2_layout = QHBoxLayout()
        seccion2_layout.setContentsMargins(0, 0, 0, 0)
        seccion2_layout.setSpacing(15)

        # Tabla horarios afectados
        self.tabla_horarios_afectados = QTableWidget()
        self.tabla_horarios_afectados.setColumnCount(5)
        self.tabla_horarios_afectados.setHorizontalHeaderLabels([
            "ID Asignación", "Hora Salida", "Hora Llegada", "Ruta", "Tren"
        ])
        self._configurar_tabla(self.tabla_horarios_afectados)
        seccion2_layout.addWidget(self._con_titulo("Asignaciones Afectadas", self.tabla_horarios_afectados))

        content_layout.addLayout(seccion2_layout)

        # Conectar señales (igual que antes)
        self.tabla_no_resueltas.cellClicked.connect(self.mostrar_afectaciones_no_resuelta)
        self.tabla_resueltas.cellClicked.connect(self.mostrar_afectaciones_resuelta)

        # Añadir contenedor de contenido al layout principal
        self.main_layout.addWidget(self.content_container, 1)

        # === Botones de acción ===
        botones_container = QWidget()
        botones_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 0, 0, 0)
        botones_layout.setSpacing(15)

        # Botón Agregar
        self.btn_agregar_incidencia = QPushButton("Agregar Incidencia")
        #self.btn_agregar_incidencia.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 150px;
        #    }
        #    QPushButton:hover {
        #        background-color: #27ae60;
        #    }
        #""")
        self.btn_agregar_incidencia.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 150px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219653;
                padding: 9px 14px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.btn_agregar_incidencia.clicked.connect(lambda: self.mostrar_panel(0))

        # Botón Resolver
        self.btn_resolver_incidencia = QPushButton("Resolver Incidencia")
        #self.btn_resolver_incidencia.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #3498db;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 150px;
        #    }
        #    QPushButton:hover {
        #        background-color: #2980b9;
        #    }
        #    QPushButton:disabled {
        #        background-color: #95a5a6;
        #    }
        #""")
        self.btn_resolver_incidencia.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 150px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
                padding: 9px 14px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.btn_resolver_incidencia.setEnabled(False)
        self.btn_resolver_incidencia.clicked.connect(self.resolver_incidencia)

        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_agregar_incidencia)
        botones_layout.addWidget(self.btn_resolver_incidencia)
        botones_layout.addStretch()

        # Añadir contenedor de botones al layout principal
        botones_main_container = QWidget()
        botones_main_layout = QHBoxLayout(botones_main_container)
        botones_main_layout.addWidget(botones_container)
        self.main_layout.addWidget(botones_main_container)

        # === Panel desplegable === 
        # (MANTENEMOS EXACTAMENTE LA MISMA LÓGICA ORIGINAL)
        self.stacked = QStackedWidget()
        self.stacked.hide()

        # Panel para agregar incidencias (igual que antes)
        self.scroll_incidencias = QScrollArea()
        self.scroll_incidencias.setWidgetResizable(True)
        self.scroll_incidencias.hide()
        self.panel_incidencias = InterfazAgregarIncidencia(self.main_window, self.db, self.username)
        # Nota: evitamos conectar update_triggered -> panel_incidencias.actualizar_datos para no duplicar recargas
        # que no aportan cambios en la lista de asignaciones.
        self.panel_incidencias.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_incidencias.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_incidencias.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_incidencias.setWidget(self.panel_incidencias)

        self.stacked.addWidget(self.scroll_incidencias)
        self.main_layout.addWidget(self.stacked)

        # Ajustes del scroll area
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Color del fondo de la ventana
        self.setStyleSheet("background-color: #0b1522;")

    def _configurar_tabla(self, tabla):
        """Configura el estilo de las tablas sin modificar su funcionamiento"""
        tabla.verticalHeader().setVisible(False)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setStyleSheet("""
            QTableWidget {
                background-color: #0b1522;
                border: 1px solid #0b1522;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #121f30ff;
                color: #55a2e7;
                padding: 5px;
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
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _con_titulo(self, titulo, widget):
        """Envuelve un widget con un título con estilo"""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel(titulo)
        label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: white;
            padding: 2px;
        """)

        layout.addWidget(label)
        layout.addWidget(widget)

        return contenedor

    def _controlar_boton_resolver(self):
        if self.tabla_no_resueltas.currentRow() == -1:
            self.btn_resolver_incidencia.setEnabled(False)
        else:
            self.btn_resolver_incidencia.setEnabled(True)

    def mostrar_panel(self, index):
        """Muestra el panel de asignación y el scroll"""
        self.stacked.setCurrentIndex(index)
        self.stacked.show()

    def ocultar_panel(self):
        """Oculta el panel de asignación y el scroll"""
        self.stacked.hide()

    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        # Coalescer llamadas cercanas para evitar repaints innecesarios
        try:
            if self._refresh_timer.isActive():
                self._refresh_timer.stop()
            self._refresh_timer.start(150)
            self.logger.debug("Programada recarga de incidencias en 150 ms")
        except Exception:
            # Fallback directo si el timer falla
            self.logger.exception("Fallo programando recarga; cargando directamente")
            self.load_incidencias()
    
    #def _con_titulo(self, titulo, tabla):
    #    """Devuelve un widget vertical con título y tabla"""
    #    contenedor = QVBoxLayout()
    #    label = QLabel(titulo)
    #    label.setStyleSheet("font-weight: bold;")
    #    contenedor.addWidget(label)
    #    contenedor.addWidget(tabla)
    #    widget = QWidget()
    #    widget.setLayout(contenedor)
    #    return widget

    def mostrar_afectaciones_no_resuelta(self, row, col):
        item = self.tabla_no_resueltas.item(row, 1)
        if item is None:
            return
        id_asignacion = item.text()
        self.btn_resolver_incidencia.setEnabled(True)
        try:
            # Obtener hora de salida e ID_RUTA de la asignación seleccionada
            fila = self.db.fetch_one(
                """
                SELECT H.HORA_SALIDA_PROGRAMADA, A.ID_RUTA
                FROM ASIGNACION_TREN A
                JOIN HORARIO H ON H.ID_HORARIO = A.ID_HORARIO
                WHERE A.ID_ASIGNACION = :id
                """,
                {"id": id_asignacion},
            )
            if not fila:
                self._cargar_tabla(self.tabla_horarios_afectados, [])
                return
            hora_salida, id_ruta = fila

            # Obtener estaciones ordenadas de la ruta
            _row_ord = self.db.fetch_one(
                """
                SELECT LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                FROM RUTA_DETALLE RD
                JOIN ESTACION E ON E.ID_ESTACION = RD.ID_ESTACION
                WHERE RD.ID_RUTA = :id_ruta
                """,
                {"id_ruta": id_ruta},
            )
            orden_ruta = _row_ord[0] if _row_ord and _row_ord[0] else None

            # Obtener asignaciones futuras en la misma ruta, con tren incluido (comparando por hora)
            filas = self.db.fetch_all(
                """
                SELECT A.ID_ASIGNACION,
                       TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                       TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI'),
                       T.NOMBRE
                FROM ASIGNACION_TREN A
                JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                JOIN TREN T ON A.ID_TREN = T.ID_TREN
                WHERE A.ID_RUTA = :id_ruta AND H.HORA_SALIDA_PROGRAMADA > :hora
                ORDER BY H.HORA_SALIDA_PROGRAMADA
                """,
                {"id_ruta": id_ruta, "hora": hora_salida},
            ) or []

            # Agregar ruta (igual para todas) y tren individual
            ruta_str = orden_ruta if orden_ruta is not None else ""
            afectadas = [(f[0], f[1], f[2], ruta_str, f[3]) for f in filas]
            self._cargar_tabla(self.tabla_horarios_afectados, afectadas)
        except Exception:
            self.logger.exception("Error mostrando afectaciones (no resuelta) para asignación %s", id_asignacion)
            self._cargar_tabla(self.tabla_horarios_afectados, [])
            
    """Resumen de la lógica actual
    No resueltas: misma ruta, comparación por DATE real 
    (H.HORA_SALIDA_PROGRAMADA > hora de la asignación seleccionada).
    Resueltas:
    Preferente: usa orden del HISTORIAL y hora de inicio del historial 
    anclada a la fecha de la incidencia; busca coincidencias en cualquier ruta.
    Fallback: usa orden actual de la ruta de la incidencia y hora de 
    esa asignación, igualmente anclada a la fecha de la incidencia; busca coincidencias en cualquier ruta.
    """

    def mostrar_afectaciones_resuelta(self, row, col):
        item = self.tabla_resueltas.item(row, 0)
        if item is None:
            return
        id_incidencia = item.text()
        self.btn_resolver_incidencia.setEnabled(False)

        try:
            # 1) Intentar obtener ORDEN y HORARIO desde HISTORIAL (estado "congelado")
            row_info = self.db.fetch_one(
                "SELECT INFORMACION FROM HISTORIAL WHERE ID_INCIDENCIA = :id",
                {"id": id_incidencia},
            )

            orden_objetivo_norm = None
            hora_inicio_str = None

            if row_info and row_info[0]:
                lob = row_info[0]
                info = lob.read() if hasattr(lob, 'read') else str(lob)
                estaciones_objetivo = self._extraer_valor(info, "Orden").strip()
                if estaciones_objetivo:
                    orden_objetivo_norm = self._normalizar_orden_str(estaciones_objetivo)
                horario = self._extraer_valor(info, "Horario").strip()
                if horario:
                    # Tomar la hora de inicio (puede venir HH:MM o HH:MM:SS)
                    hora_inicio_str = horario.split(" - ")[0].strip()
                    if len(hora_inicio_str) == 5:  # HH:MM
                        hora_inicio_str += ":00"

            if orden_objetivo_norm and hora_inicio_str:
                # 2) Buscar asignaciones en cualquier ruta cuyo ORDEN coincida y sean posteriores a la hora del historial
                #    Comparación por DATE usando solo la parte de hora (independiente de la fecha).
                filas = self.db.fetch_all(
                    """
                    WITH RUTAS_ORDEN AS (
                        SELECT RD.ID_RUTA,
                               LISTAGG(E.NOMBRE, ' - ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ORDEN
                        FROM RUTA_DETALLE RD
                        JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                        GROUP BY RD.ID_RUTA
                    )
                    SELECT A.ID_ASIGNACION,
                           TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                           TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI'),
                           T.NOMBRE
                    FROM ASIGNACION_TREN A
                    JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                    JOIN TREN T ON A.ID_TREN = T.ID_TREN
                    JOIN RUTAS_ORDEN R ON R.ID_RUTA = A.ID_RUTA
                    WHERE R.ORDEN = :orden
                      AND (H.HORA_SALIDA_PROGRAMADA - TRUNC(H.HORA_SALIDA_PROGRAMADA)) >=
                          (TO_DATE(:hora_str, 'HH24:MI:SS') - TRUNC(TO_DATE(:hora_str, 'HH24:MI:SS')))
                    ORDER BY H.HORA_SALIDA_PROGRAMADA
                    """,
                    {"orden": orden_objetivo_norm, "hora_str": hora_inicio_str},
                ) or []

                ruta_display = orden_objetivo_norm.replace(' - ', ' → ')
                afectadas = [(f[0], f[1], f[2], ruta_display, f[3]) for f in filas]
                self._cargar_tabla(self.tabla_horarios_afectados, afectadas)
                return

            # 3) Fallback: usar la ruta/hora actual de la incidencia y derivar ORDEN en vivo
            fila = self.db.fetch_one(
                """
                SELECT A.ID_RUTA, H.HORA_SALIDA_PROGRAMADA
                FROM INCIDENCIA I
                JOIN ASIGNACION_TREN A ON A.ID_ASIGNACION = I.ID_ASIGNACION
                JOIN HORARIO H ON H.ID_HORARIO = A.ID_HORARIO
                WHERE I.ID_INCIDENCIA = :1
                """,
                {"id": id_incidencia},
            )
            if not fila:
                self._cargar_tabla(self.tabla_horarios_afectados, [])
                return
            id_ruta, hora_salida = fila

            row_ord = self.db.fetch_one(
                """
                SELECT LISTAGG(E.NOMBRE, ' - ') WITHIN GROUP (ORDER BY RD.ORDEN)
                FROM RUTA_DETALLE RD
                JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                WHERE RD.ID_RUTA = :1
                """,
                {"id_ruta": id_ruta},
            )
            orden_objetivo_norm = row_ord[0] if row_ord and row_ord[0] else ''

            filas = self.db.fetch_all(
                """
                WITH RUTAS_ORDEN AS (
                    SELECT RD.ID_RUTA,
                           LISTAGG(E.NOMBRE, ' - ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ORDEN
                    FROM RUTA_DETALLE RD
                    JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                    GROUP BY RD.ID_RUTA
                )
                SELECT A.ID_ASIGNACION,
                       TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                       TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI'),
                       T.NOMBRE
                FROM ASIGNACION_TREN A
                JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                JOIN TREN T ON A.ID_TREN = T.ID_TREN
                JOIN RUTAS_ORDEN R ON R.ID_RUTA = A.ID_RUTA
                WHERE R.ORDEN = :orden
                  AND (H.HORA_SALIDA_PROGRAMADA - TRUNC(H.HORA_SALIDA_PROGRAMADA)) >= (:hora_ref - TRUNC(:hora_ref))
                ORDER BY H.HORA_SALIDA_PROGRAMADA
                """,
                {"orden": orden_objetivo_norm, "hora_ref": hora_salida},
            ) or []

            ruta_display = orden_objetivo_norm.replace(' - ', ' → ')
            afectadas = [(f[0], f[1], f[2], ruta_display, f[3]) for f in filas]
            self._cargar_tabla(self.tabla_horarios_afectados, afectadas)
        except Exception:
            self.logger.exception("Error mostrando afectaciones (resuelta) para incidencia %s", id_incidencia)
            self._cargar_tabla(self.tabla_horarios_afectados, [])

    def _normalizar_orden_str(self, s: str) -> str:
        """Normaliza el string de orden de estaciones a formato 'A - B - C' para comparaciones.
        Cambia distintos separadores (→, ->, —, –) a '-', recorta espacios y colapsa separadores.
        """
        if not s:
            return ''
        # Unificar separadores a '-'
        tmp = s.replace('→', '-').replace('->', '-').replace('—', '-').replace('–', '-')
        # Partir por '-', limpiar y descartar vacíos
        partes = [p.strip() for p in tmp.split('-') if p and p.strip()]
        return ' - '.join(partes)

    def _extraer_valor(self, texto, clave):
        partes = texto.split(";")
        for parte in partes:
            if parte.strip().startswith(clave):
                return parte.split(":")[1].strip()
        return ""

    def load_incidencias(self):
        # Cargar ambas tablas de una sola vez para reducir el tiempo de bloqueo
        query = """
            SELECT ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION,
                   TO_CHAR(FECHA_HORA, 'YYYY-MM-DD HH24:MI:SS') AS FH,
                   ESTADO
            FROM INCIDENCIA
        """
        try:
            filas = self.db.fetch_all(query)
        except Exception:
            self.logger.exception("Error cargando incidencias")
            filas = []

        no_resueltas = [f[:5] for f in filas if str(f[5]).upper().startswith('NO RESUELT')]
        resueltas = [f[:5] for f in filas if str(f[5]).upper().startswith('RESUELT')]

        # Suspender repintado mientras se rellenan datos
        self.tabla_no_resueltas.setUpdatesEnabled(False)
        self.tabla_resueltas.setUpdatesEnabled(False)
        try:
            self._cargar_tabla(self.tabla_no_resueltas, no_resueltas)
            self._cargar_tabla(self.tabla_resueltas, resueltas)
        finally:
            self.tabla_no_resueltas.setUpdatesEnabled(True)
            self.tabla_resueltas.setUpdatesEnabled(True)

    def _cargar_tabla(self, tabla, datos):
        # Optimización de pintado
        tabla.setSortingEnabled(False)
        tabla.setUpdatesEnabled(False)
        try:
            tabla.clearContents()
            tabla.setRowCount(len(datos))
            for i, fila in enumerate(datos):
                for j, valor in enumerate(fila):
                    tabla.setItem(i, j, QTableWidgetItem(str(valor)))
            tabla.resizeRowsToContents()
        finally:
            tabla.setUpdatesEnabled(True)
            tabla.setSortingEnabled(True)

    def resolver_incidencia(self):
        fila = self.tabla_no_resueltas.currentRow()
        # Si no hay horario seleccionado manda una advertencia
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona una incidencia a resolver.")
            return
        item = self.tabla_no_resueltas.item(fila, 0)
        if item is None:
            return
        id_incidencia = item.text()
        
        confirmacion = QMessageBox(self)
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar resolución")
        confirmacion.setText(f"¿Estás seguro de que deseas marcar como resuelta la incidencia #{id_incidencia}?")
        boton_si = confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)

        try:
            # Ejecutar el diálogo y verificar explícitamente el botón pulsado
            confirmacion.exec()
            if confirmacion.clickedButton() == boton_si:
                self.db.execute_query(
                    """
                    UPDATE INCIDENCIA
                    SET ESTADO = 'RESUELTO'
                    WHERE ID_INCIDENCIA = :id
                    """,
                    {"id": id_incidencia},
                )
                # Emitir evento de actualización si existe
                try:
                    if hasattr(self.db, "event_manager") and getattr(self.db.event_manager, "update_triggered", None):
                        self.db.event_manager.update_triggered.emit()
                except Exception:
                    self.logger.exception("Fallo al emitir update_triggered tras resolver incidencia")
                QMessageBox.information(self, "Éxito", f"Incidencia {id_incidencia} marcada como resuelta.")
                # Actualizar tablas de forma liviana
                self.load_incidencias()
                self.btn_resolver_incidencia.setEnabled(False)
            else:
                self.btn_resolver_incidencia.setEnabled(False)
            self.tabla_horarios_afectados.clearContents()
            self.tabla_horarios_afectados.setRowCount(0)
        except Exception as e:
            self.logger.exception("Error resolviendo incidencia %s", id_incidencia)
            QMessageBox.critical(self, "Error", f"No se pudo resolver la incidencia: {str(e)}")
