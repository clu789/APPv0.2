from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QPushButton, QHBoxLayout, 
                             QSizePolicy, QHeaderView, QStackedWidget, QScrollArea,
                             QMessageBox, QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection
from interfaces.paneles.panel_incidencias import InterfazAgregarIncidencia
from PyQt6.QtGui import QPixmap
from utils import obtener_ruta_recurso

class GestionIncidencias(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db

        self.setWindowTitle("Gestión de Incidencias")
        self.setGeometry(100, 100, 1000, 600)

        self.initUI()
        self.load_incidencias()

    def initUI(self):
        # Layout principal con scroll (solo para diseño)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor principal
        self.main_container = QWidget()
        self.main_container.setFixedWidth(1400)
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
                color: #2c3e50;
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
        """)
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(self.titulo)

        header_layout.addWidget(logo_container)
        self.main_layout.addLayout(header_layout)

        # Sección de tabla de asignaciones
        label_estado = QLabel("Asignaciones de Trenes")
        label_estado.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 5px;
            }
        """)
        self.main_layout.addWidget(label_estado)

        # Contenedor para el contenido con ancho fijo
        self.content_container = QWidget()
        self.content_container.setFixedWidth(1350)
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
        botones_container.setFixedWidth(900)
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 0, 0, 0)
        botones_layout.setSpacing(15)

        # Botón Agregar
        self.btn_agregar_incidencia = QPushButton("Agregar Incidencia")
        self.btn_agregar_incidencia.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_agregar_incidencia.clicked.connect(lambda: self.mostrar_panel(0))

        # Botón Resolver
        self.btn_resolver_incidencia = QPushButton("Resolver Incidencia")
        self.btn_resolver_incidencia.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
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
        self.db.event_manager.update_triggered.connect(self.panel_incidencias.actualizar_datos)
        self.panel_incidencias.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_incidencias.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_incidencias.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_incidencias.setWidget(self.panel_incidencias)

        self.stacked.addWidget(self.scroll_incidencias)
        self.main_layout.addWidget(self.stacked)

        # Ajustes del scroll area
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def _configurar_tabla(self, tabla):
        """Configura el estilo de las tablas sin modificar su funcionamiento"""
        tabla.verticalHeader().setVisible(False)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 5px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
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
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 2px solid #3498db;
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
        print("Actualizando datos de GestionHorariosRutas")
        self.load_incidencias()
    
    def _con_titulo(self, titulo, tabla):
        """Devuelve un widget vertical con título y tabla"""
        contenedor = QVBoxLayout()
        label = QLabel(titulo)
        label.setStyleSheet("font-weight: bold;")
        contenedor.addWidget(label)
        contenedor.addWidget(tabla)
        widget = QWidget()
        widget.setLayout(contenedor)
        return widget

    def mostrar_afectaciones_no_resuelta(self, row, col):
        id_asignacion = self.tabla_no_resueltas.item(row, 1).text()
        cursor = self.db.connection.cursor()

        # Obtener ID_HORARIO e ID_RUTA de la asignación seleccionada
        cursor.execute("""
            SELECT A.ID_HORARIO, A.ID_RUTA
            FROM ASIGNACION_TREN A
            WHERE A.ID_ASIGNACION = :1
        """, (id_asignacion,))
        id_horario, id_ruta = cursor.fetchone()

        # Obtener estaciones ordenadas de la ruta
        cursor.execute("""
            SELECT LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
            FROM RUTA_DETALLE RD
            JOIN ESTACION E ON E.ID_ESTACION = RD.ID_ESTACION
            WHERE RD.ID_RUTA = :1
        """, (id_ruta,))
        orden_ruta = cursor.fetchone()[0]

        # Obtener asignaciones futuras en la misma ruta, con tren incluido
        cursor.execute("""
            SELECT A.ID_ASIGNACION,
                   TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                   TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI'),
                   T.NOMBRE
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            WHERE A.ID_RUTA = :1 AND H.ID_HORARIO > :2
            ORDER BY H.ID_HORARIO
        """, (id_ruta, id_horario))
        filas = cursor.fetchall()

        # Agregar ruta (igual para todas) y tren individual
        afectadas = [(f[0], f[1], f[2], orden_ruta, f[3]) for f in filas]
        self._cargar_tabla(self.tabla_horarios_afectados, afectadas)

    def mostrar_afectaciones_resuelta(self, row, col):
        id_incidencia = self.tabla_resueltas.item(row, 0).text()
        cursor = self.db.connection.cursor()

        # Obtener campo INFORMACION del historial
        cursor.execute("SELECT INFORMACION FROM HISTORIAL WHERE ID_INCIDENCIA = :1", (id_incidencia,))
        resultado = cursor.fetchone()
        if resultado:
            lob = resultado[0]
            info = lob.read() if hasattr(lob, 'read') else str(lob)  # manejar CLOB

            # Extraer datos
            estaciones_objetivo = self._extraer_valor(info, "Orden").strip()
            tren_inicial = self._extraer_valor(info, "Tren").strip()
            horario = self._extraer_valor(info, "Horario")
            hora_inicio = horario.split(" - ")[0]

            # Obtener asignaciones posteriores
            cursor.execute("""
                SELECT A.ID_ASIGNACION,
                       TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                       TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI'),
                       A.ID_RUTA,
                       A.ID_TREN
                FROM ASIGNACION_TREN A
                JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                WHERE TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') >= :1
                ORDER BY H.HORA_SALIDA_PROGRAMADA
            """, (hora_inicio + ":00",))
            filas = cursor.fetchall()

            afectadas = []
            for fila in filas:
                id_asignacion, salida, llegada, id_ruta, id_tren = fila

                # Obtener orden de estaciones de esta ruta
                cursor.execute("""
                    SELECT LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                    FROM RUTA_DETALLE RD
                    JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                    WHERE RD.ID_RUTA = :1
                """, (id_ruta,))
                orden_ruta = cursor.fetchone()[0]

                # Comparar orden
                if orden_ruta.strip() == estaciones_objetivo:
                    # Obtener nombre del tren real de esta asignación
                    cursor.execute("SELECT NOMBRE FROM TREN WHERE ID_TREN = :1", (id_tren,))
                    nombre_tren = cursor.fetchone()[0]
                    afectadas.append((id_asignacion, salida, llegada, orden_ruta, nombre_tren))

            self._cargar_tabla(self.tabla_horarios_afectados, afectadas)

    def _extraer_valor(self, texto, clave):
        partes = texto.split(";")
        for parte in partes:
            if parte.strip().startswith(clave):
                return parte.split(":")[1].strip()
        return ""

    def load_incidencias(self):
        query_no_resueltas = """
            SELECT ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION, TO_CHAR(FECHA_HORA, 'YYYY-MM-DD HH24:MI:SS')
            FROM INCIDENCIA
            WHERE ESTADO = 'NO RESUELTO'
        """
        query_resueltas = """
            SELECT ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION, TO_CHAR(FECHA_HORA, 'YYYY-MM-DD HH24:MI:SS')
            FROM INCIDENCIA
            WHERE ESTADO = 'RESUELTO'
        """
        no_resueltas = self.db.fetch_all(query_no_resueltas)
        resueltas = self.db.fetch_all(query_resueltas)

        self._cargar_tabla(self.tabla_no_resueltas, no_resueltas)
        self._cargar_tabla(self.tabla_resueltas, resueltas)

    def _cargar_tabla(self, tabla, datos):
        tabla.setRowCount(len(datos))
        for i, fila in enumerate(datos):
            for j, valor in enumerate(fila):
                tabla.setItem(i, j, QTableWidgetItem(str(valor)))
        tabla.resizeRowsToContents()

    def resolver_incidencia(self):
        fila = self.tabla_no_resueltas.currentRow()
        # Si no hay horario seleccionado manda una advertencia
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona una incidencia a resolver.")
            return
        id_incidencia = self.tabla_no_resueltas.item(fila, 0).text()
        cursor = self.db.connection.cursor()
        
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar resolución")
        confirmacion.setText(f"¿Estás seguro de que deseas marcar como resuelta la incidencia #{id_incidencia}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)

        try:
            if confirmacion.exec() == 2:
                cursor.execute("""
                    UPDATE INCIDENCIA
                    SET ESTADO = 'RESUELTO'
                    WHERE ID_INCIDENCIA = :1
                """, (id_incidencia,))
                self.db.connection.commit()
                self.db.event_manager.update_triggered.emit()
                QMessageBox.information(self, "Éxito", f"Incidencia {id_incidencia} marcada como resuelta.")
                self.tabla_no_resueltas.clearSelection()
                self.tabla_no_resueltas.clearFocus()
                self.btn_resolver_incidencia.setEnabled(False)
            else:
                self.tabla_no_resueltas.clearSelection()
                self.tabla_no_resueltas.clearFocus()
                self.btn_resolver_incidencia.setEnabled(False)
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo resolver la incidencia: {str(e)}")
        finally:
            cursor.close()
