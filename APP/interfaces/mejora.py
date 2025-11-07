from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QPushButton, QMessageBox, QScrollArea, QFrame,
                             QHeaderView, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
import logging
from typing import List, Dict, Tuple, Optional
from utils import obtener_ruta_recurso

logger = logging.getLogger(__name__)

class MejoraContinua(QWidget):
    """Panel de análisis y mejora continua: reportes y historial.

    Muestra historial de horarios, rutas y asignaciones, además de reportes
    agregados por ruta y por tren.
    """

    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        # Coalescer de recargas
        self._refresh_timer: QTimer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(150)
        self._refresh_timer.timeout.connect(self.cargar_datos)
        self._event_connected = False
        
        self.setWindowTitle("Análisis y Mejora Continua")
        # Aumentar altura inicial y mínima para más espacio vertical
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1200, 800)
        self.initUI()
        self.cargar_datos()
        
    def initUI(self):
        # Layout principal con scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Widget contenedor principal (usar todo el ancho disponible)
        self.main_container = QWidget()
        # Expandir también verticalmente para aprovechar más espacio
        self.main_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # Configurar el scroll area
        self.scroll_area.setWidget(self.main_container)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.scroll_area)
        self.layout().setContentsMargins(0, 0, 0, 0)
    
        # --- Encabezado con logo y título ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 15)

        # Título principal centrado
        title_label = QLabel("Mejora Continua")
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
    
        # --- Primera fila: Tres tablas en horizontal ---
        tablas_superiores_container = QWidget()
        tablas_superiores_layout = QHBoxLayout(tablas_superiores_container)
        tablas_superiores_layout.setContentsMargins(0, 0, 0, 0)
        tablas_superiores_layout.setSpacing(15)
    
        # Función para configurar tablas
        def configurar_tabla(tabla, headers):
            tabla.setColumnCount(len(headers))
            tabla.setHorizontalHeaderLabels(headers)
            tabla.setStyleSheet("""
                QTableWidget {
                    background-color: #0b1522;
                    border: 1px solid #0b1522;
                    border-radius: 4px;
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
            tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tabla.verticalHeader().setVisible(False)
            tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            # Alinear comportamiento con interfaz de horarios para mejor visualización
            tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            tabla.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
        # Función para crear sección de tabla con título (solo para las 3 primeras tablas)
        def crear_seccion_tabla_horizontal(titulo, tabla, stretch=1):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)
            
            label = QLabel(titulo)
            label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #197fbc;
                    padding-bottom: 5px;
                }
            """)
            
            layout.addWidget(label)
            layout.addWidget(tabla)
            tablas_superiores_layout.addWidget(container, stretch)
    
        # Tabla 1: Historial de Horarios
        self.tabla_horarios = QTableWidget()
        configurar_tabla(self.tabla_horarios, ["ID Horario", "Información", "Fecha Registro"])
        crear_seccion_tabla_horizontal("Historial de Horarios:", self.tabla_horarios, 1)
        # Dar más altura mínima a la tabla para evitar vista "apretada"
        self.tabla_horarios.setMinimumHeight(220)
        self.tabla_horarios.setSortingEnabled(True)
    
        # Tabla 2: Reporte de Rutas
        self.tabla_reporte_rutas = QTableWidget()
        configurar_tabla(self.tabla_reporte_rutas, ["ID Ruta", "Asignaciones", "Retraso Promedio", "Incidencias"])
        crear_seccion_tabla_horizontal("Reporte de Rutas:", self.tabla_reporte_rutas, 1)
        self.tabla_reporte_rutas.setMinimumHeight(200)
        # Evitar que el encabezado "Retraso Promedio" se corte
        self.tabla_reporte_rutas.horizontalHeader().setMinimumSectionSize(60)
        self.tabla_reporte_rutas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    
        # Tabla 3: Reporte de Trenes
        self.tabla_reporte_trenes = QTableWidget()
        configurar_tabla(self.tabla_reporte_trenes, ["ID Tren", "Asignaciones", "Retraso Promedio", "Incidencias"])
        crear_seccion_tabla_horizontal("Reporte de Trenes:", self.tabla_reporte_trenes, 1)
        self.tabla_reporte_trenes.setMinimumHeight(200)
        # Evitar corte del encabezado "Retraso Promedio"
        self.tabla_reporte_trenes.horizontalHeader().setMinimumSectionSize(60)
        self.tabla_reporte_trenes.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    
        # Dar un poco de espacio, pero priorizar tablas inferiores
        self.main_layout.addWidget(tablas_superiores_container, 1)
    
        # --- Segunda fila: Historial de Rutas ---
        rutas_label = QLabel("Historial de Rutas:")
        rutas_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #197fbc;
                padding-bottom: 5px;
            }
        """)
        self.main_layout.addWidget(rutas_label)
        
        self.tabla_rutas = QTableWidget()
        configurar_tabla(self.tabla_rutas, ["ID Ruta", "Información", "Fecha Registro"])
        # Copiar comportamiento de tabla de rutas en Horarios: columnas en modo Stretch
        self.tabla_rutas.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_rutas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Más altura para que se vea mejor con pocos datos
        self.tabla_rutas.setMinimumHeight(320)
        # Priorizar más espacio vertical para esta tabla
        self.main_layout.addWidget(self.tabla_rutas, 2)
        self.tabla_rutas.setSortingEnabled(True)
    
        # --- Tercera fila: Historial de Asignaciones ---
        asignaciones_label = QLabel("Historial de Asignaciones:")
        asignaciones_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #197fbc;
                padding-bottom: 5px;
            }
        """)
        self.main_layout.addWidget(asignaciones_label)
        
        self.tabla_asignaciones = QTableWidget()
        configurar_tabla(self.tabla_asignaciones, ["ID Asignación", "Información", "Fecha Registro"])
        # Mismo comportamiento que Historial de Rutas: columnas en modo Stretch
        self.tabla_asignaciones.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Más altura para que se vea mejor con pocos datos
        self.tabla_asignaciones.setMinimumHeight(320)
        # Priorizar más espacio vertical para esta tabla
        self.main_layout.addWidget(self.tabla_asignaciones, 2)
        self.tabla_asignaciones.setSortingEnabled(True)
    
        # Botón para actualizar con estilo
        btn_actualizar = QPushButton("Actualizar Datos")
        #btn_actualizar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #3498db;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        font-size: 14px;
        #        font-weight: bold;
        #        min-width: 200px;
        #    }
        #    QPushButton:hover {
        #        background-color: #2980b9;
        #    }
        #""")
        btn_actualizar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 200px;
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
        btn_actualizar.clicked.connect(self.actualizar_datos)
        
        # Contenedor para centrar el botón
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_actualizar)
        btn_layout.addStretch()
        
        self.main_layout.addWidget(btn_container)
        
        # Color del fondo de la ventana
        self.setStyleSheet("background-color: #0b1522;")
        # Políticas de scroll como en la interfaz de horarios
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)

    def cargar_datos(self) -> None:
        self.cargar_historial_horarios()
        self.cargar_historial_rutas()
        self.cargar_historial_asignaciones()
        self.generar_reporte_rutas()
        self.generar_reporte_trenes()

    # Ya no se requiere resizeEvent personalizado ni ajustador de ancho: con Stretch se adapta solo

    def actualizar_datos(self) -> None:
        """Programa una recarga coalescida y se engancha al EventManager si existe."""
        try:
            if not self._event_connected and getattr(self.db, "event_manager", None) and hasattr(self.db.event_manager, "update_triggered"):
                try:
                    self.db.event_manager.update_triggered.connect(self.actualizar_datos)
                    self._event_connected = True
                except Exception as em:
                    logger.warning("No se pudo conectar a update_triggered: %s", em)
            if self._refresh_timer.isActive():
                self._refresh_timer.stop()
            self._refresh_timer.start()
        except Exception:
            # Fallback directo si el timer falla
            self.cargar_datos()
        
    def cargar_historial_horarios(self) -> None:
        try:
            # 1. Obtener datos
            historial = self.db.fetch_all("""
                SELECT ID_HORARIO, INFORMACION, FECHA_REGISTRO
                FROM HISTORIAL
                WHERE ID_HORARIO IS NOT NULL
            """)

            if not historial:
                self.tabla_horarios.setRowCount(0)
                return

            # 2. Obtener horarios actuales en una sola consulta (evitar N+1)
            ids_horarios = sorted({int(h[0]) for h in historial if h and h[0] is not None})
            horarios_actuales_map: Dict[int, str] = {}
            if ids_horarios:
                bind_map = {f"id{i}": hid for i, hid in enumerate(ids_horarios)}
                placeholders = ','.join(f":{k}" for k in bind_map.keys())
                res = self.db.fetch_all(f"""
                    SELECT ID_HORARIO,
                           TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI') || ' - ' || 
                           TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI') AS HOR
                    FROM HORARIO
                    WHERE ID_HORARIO IN ({placeholders})
                """, bind_map)
                horarios_actuales_map = {int(r[0]): r[1] for r in (res or [])}

            # 3. Precalcular filas necesarias
            total_filas = len(historial) + len(horarios_actuales_map)

            # 4. Configurar tabla y volcar
            self.tabla_horarios.setUpdatesEnabled(False)
            self.tabla_horarios.setSortingEnabled(False)  # Desactivar ordenamiento temporal
            self.tabla_horarios.setRowCount(total_filas)

            # 5. Llenar datos
            fila = 0
            horarios_mostrados = set()

            for id_horario, info_hist, fecha in historial:
                # Procesar CLOB
                if hasattr(info_hist, 'read'):
                    info_hist = info_hist.read()

                # Datos de historial
                self.tabla_horarios.setItem(fila, 0, QTableWidgetItem(str(id_horario)))
                self.tabla_horarios.setItem(fila, 1, QTableWidgetItem(info_hist))
                self.tabla_horarios.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
                fila += 1

                # Datos de horario actual (solo una vez por ID)
                if id_horario not in horarios_mostrados:
                    horarios_mostrados.add(id_horario)
                    hor_str = horarios_actuales_map.get(int(id_horario))
                    if hor_str:
                        self.tabla_horarios.setItem(fila, 0, QTableWidgetItem(str(id_horario)))
                        self.tabla_horarios.setItem(fila, 1, QTableWidgetItem("HORARIO ACTUAL: " + hor_str))
                        self.tabla_horarios.setItem(fila, 2, QTableWidgetItem(""))
                        fila += 1

            # 6. Ajustes finales (sin ordenamiento)
            self.tabla_horarios.setSortingEnabled(True)
            self.tabla_horarios.sortItems(0, Qt.SortOrder.AscendingOrder)
            self.tabla_horarios.setUpdatesEnabled(True)

        except Exception as e:
            logger.exception("Error en cargar_historial_horarios: %s", e)
            self.tabla_horarios.setRowCount(0)  # Limpiar tabla en caso de error

    def cargar_historial_rutas(self) -> None:
        try:
            # 1. Obtener datos del historial
            historial = self.db.fetch_all("""
                SELECT ID_RUTA, INFORMACION, FECHA_REGISTRO
                FROM HISTORIAL
                WHERE ID_RUTA IS NOT NULL
            """)

            if not historial:
                self.tabla_rutas.setRowCount(0)
                return

            # 2. Obtener info de rutas actuales para IDs únicos (evitar N+1)
            ids_ruta = sorted({int(r[0]) for r in historial if r and r[0] is not None})
            rutas_actuales_map: Dict[int, Tuple[str, str]] = {}
            if ids_ruta:
                bind_map = {f"id{i}": rid for i, rid in enumerate(ids_ruta)}
                placeholders = ','.join(f":{k}" for k in bind_map.keys())
                res = self.db.fetch_all(f"""
                    SELECT R.ID_RUTA,
                           R.DURACION_ESTIMADA,
                           LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ESTACIONES
                    FROM RUTA R
                    JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
                    JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                    WHERE R.ID_RUTA IN ({placeholders})
                    GROUP BY R.ID_RUTA, R.DURACION_ESTIMADA
                """, bind_map)
                rutas_actuales_map = {int(r[0]): (r[1], r[2]) for r in (res or [])}

            total_filas = len(historial) + len(rutas_actuales_map)
            # 3. Configurar tabla
            self.tabla_rutas.setUpdatesEnabled(False)
            self.tabla_rutas.setSortingEnabled(False)  # Desactivar ordenamiento temporal
            self.tabla_rutas.setRowCount(total_filas)

            # 4. Llenar datos
            fila = 0
            rutas_mostradas = set()  # Reiniciamos para el llenado

            for id_ruta, info_hist, fecha in historial:
                # Convertir CLOB si es necesario
                if hasattr(info_hist, 'read'):
                    info_hist = info_hist.read()
                elif not isinstance(info_hist, str):
                    info_hist = str(info_hist)

                # Datos de historial
                self.tabla_rutas.setItem(fila, 0, QTableWidgetItem(str(id_ruta)))
                self.tabla_rutas.setItem(fila, 1, QTableWidgetItem(info_hist))
                self.tabla_rutas.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
                fila += 1

                # Datos de ruta actual (solo una vez por ID)
                if id_ruta not in rutas_mostradas:
                    rutas_mostradas.add(id_ruta)
                    actual = rutas_actuales_map.get(int(id_ruta))
                    if actual:
                        duracion, estaciones = actual
                        info_actual = f"RUTA ACTUAL: Duración: {duracion}; Orden: {estaciones}"

                        self.tabla_rutas.setItem(fila, 0, QTableWidgetItem(str(id_ruta)))
                        self.tabla_rutas.setItem(fila, 1, QTableWidgetItem(info_actual))
                        self.tabla_rutas.setItem(fila, 2, QTableWidgetItem(""))
                        fila += 1

            # 5. Ajustes finales
            self.tabla_rutas.resizeRowsToContents()
            self.tabla_rutas.setSortingEnabled(True)
            self.tabla_rutas.sortItems(0, Qt.SortOrder.AscendingOrder)
            self.tabla_rutas.setUpdatesEnabled(True)
            

        except Exception as e:
            logger.exception("Error en cargar_historial_rutas: %s", e)
            self.tabla_rutas.setRowCount(0)  # Limpiar tabla en caso de error
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los datos de rutas: {str(e)}")

    def cargar_historial_asignaciones(self) -> None:
        try:
            # 1. Obtener datos del historial
            historial = self.db.fetch_all("""
                SELECT ID_ASIGNACION, INFORMACION, FECHA_REGISTRO
                FROM HISTORIAL
                WHERE ID_ASIGNACION IS NOT NULL 
                  AND ID_INCIDENCIA IS NULL 
                  AND HORA_REAL IS NULL
                ORDER BY FECHA_REGISTRO DESC
            """)
            
            if not historial:
                self.tabla_asignaciones.setRowCount(0)
                return
    
            # 2. Cargar en lotes los datos actuales relacionados (evitar N+1)
            ids_asig = sorted({int(a[0]) for a in historial if a and a[0] is not None})
            asign_map: Dict[int, Tuple[int, int, int]] = {}
            horario_map: Dict[int, Tuple[str, str]] = {}
            ruta_map: Dict[int, Tuple[str, str]] = {}
            tren_map: Dict[int, str] = {}
            if ids_asig:
                # Asignaciones
                bind_asig = {f"id{i}": aid for i, aid in enumerate(ids_asig)}
                ph_asig = ','.join(f":{k}" for k in bind_asig.keys())
                res_asig = self.db.fetch_all(f"""
                    SELECT ID_ASIGNACION, ID_RUTA, ID_HORARIO, ID_TREN
                    FROM ASIGNACION_TREN
                    WHERE ID_ASIGNACION IN ({ph_asig})
                """, bind_asig)
                asign_map = {int(r[0]): (int(r[1]), int(r[2]), int(r[3])) for r in (res_asig or [])}

                # Derivar sets
                ids_hor = sorted({v[1] for v in asign_map.values()})
                ids_ruta = sorted({v[0] for v in asign_map.values()})
                ids_tren = sorted({v[2] for v in asign_map.values()})

                if ids_hor:
                    bind_h = {f"h{i}": hid for i, hid in enumerate(ids_hor)}
                    ph_h = ','.join(f":{k}" for k in bind_h.keys())
                    res_h = self.db.fetch_all(f"""
                        SELECT ID_HORARIO,
                               TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI') AS SAL,
                               TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI') AS LLEG
                        FROM HORARIO
                        WHERE ID_HORARIO IN ({ph_h})
                    """, bind_h)
                    horario_map = {int(r[0]): (r[1], r[2]) for r in (res_h or [])}

                if ids_ruta:
                    bind_r = {f"r{i}": rid for i, rid in enumerate(ids_ruta)}
                    ph_r = ','.join(f":{k}" for k in bind_r.keys())
                    res_r = self.db.fetch_all(f"""
                        SELECT R.ID_RUTA,
                               R.DURACION_ESTIMADA,
                               LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ESTACIONES
                        FROM RUTA R
                        JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
                        JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                        WHERE R.ID_RUTA IN ({ph_r})
                        GROUP BY R.ID_RUTA, R.DURACION_ESTIMADA
                    """, bind_r)
                    ruta_map = {int(r[0]): (r[1], r[2]) for r in (res_r or [])}

                if ids_tren:
                    bind_t = {f"t{i}": tid for i, tid in enumerate(ids_tren)}
                    ph_t = ','.join(f":{k}" for k in bind_t.keys())
                    res_t = self.db.fetch_all(f"""
                        SELECT ID_TREN, NOMBRE
                        FROM TREN
                        WHERE ID_TREN IN ({ph_t})
                    """, bind_t)
                    tren_map = {int(r[0]): r[1] for r in (res_t or [])}
    
            total_filas = len(historial) + len(asign_map)
            # 3. Configurar tabla
            self.tabla_asignaciones.setUpdatesEnabled(False)
            self.tabla_asignaciones.setSortingEnabled(False)
            self.tabla_asignaciones.setRowCount(total_filas)
    
            # 4. Llenar datos
            fila = 0
            asignaciones_mostradas = set()  # Reiniciamos para el llenado
            
            for id_asignacion, info_hist, fecha in historial:
                # Convertir CLOB si es necesario
                if hasattr(info_hist, 'read'):
                    info_hist = info_hist.read()
                elif not isinstance(info_hist, str):
                    info_hist = str(info_hist)
    
                # Datos de historial
                self.tabla_asignaciones.setItem(fila, 0, QTableWidgetItem(str(id_asignacion)))
                self.tabla_asignaciones.setItem(fila, 1, QTableWidgetItem(info_hist))
                self.tabla_asignaciones.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
                fila += 1
    
                # Datos de asignación actual (solo una vez por ID)
                if id_asignacion not in asignaciones_mostradas:
                    asignaciones_mostradas.add(id_asignacion)
                    datos_asignacion = asign_map.get(int(id_asignacion))
                    if datos_asignacion:
                        id_ruta, id_horario, id_tren = datos_asignacion
                        hora_inicio, hora_fin = horario_map.get(int(id_horario), ("?", "?"))
                        duracion, estaciones = ruta_map.get(int(id_ruta), ("?", "?"))
                        nombre_tren = tren_map.get(int(id_tren), "?")
                        
                        # Construir información actual
                        info_actual = (
                            f"ASIGNACIÓN ACTUAL: Duración: {duracion}; "
                            f"Estaciones: {estaciones}; "
                            f"Horario: {hora_inicio}-{hora_fin}; "
                            f"Tren: {nombre_tren}"
                        )
                        
                        # Insertar datos actuales
                        self.tabla_asignaciones.setItem(fila, 0, QTableWidgetItem(str(id_asignacion)))
                        self.tabla_asignaciones.setItem(fila, 1, QTableWidgetItem(info_actual))
                        self.tabla_asignaciones.setItem(fila, 2, QTableWidgetItem(""))
                        fila += 1
    
            # 5. Ajustes finales (con Stretch no hace falta ajustar columnas al contenido)
            self.tabla_asignaciones.resizeRowsToContents()
            self.tabla_asignaciones.setSortingEnabled(True)
            self.tabla_asignaciones.sortItems(0, Qt.SortOrder.AscendingOrder)
            self.tabla_asignaciones.setUpdatesEnabled(True)
            
        except Exception as e:
            logger.exception("Error en cargar_historial_asignaciones: %s", e)
            self.tabla_asignaciones.setRowCount(0)
            QMessageBox.warning(self, "Error", 
                f"No se pudieron cargar los datos de asignaciones:\n{str(e)}")

    def generar_reporte_rutas(self) -> None:
        try:
            # 1. Reporte agregado de rutas (asignaciones, retraso promedio en SQL, incidencias)
            filas = self.db.fetch_all(
                """
                SELECT R.ID_RUTA,
                       NVL(A.CNT_ASIG, 0) AS ASIGNACIONES,
                       D.RETRASO_PROMEDIO,
                       NVL(I.CNT_INC, 0) AS INCIDENCIAS
                FROM RUTA R
                LEFT JOIN (
                    SELECT ID_RUTA, COUNT(*) CNT_ASIG
                    FROM ASIGNACION_TREN
                    GROUP BY ID_RUTA
                ) A ON A.ID_RUTA = R.ID_RUTA
                LEFT JOIN (
                    SELECT T.ID_RUTA,
                           CASE WHEN SUM(T.CNT_TOTAL) > 0 THEN SUM(T.MINS_TOTAL) / SUM(T.CNT_TOTAL) END AS RETRASO_PROMEDIO
                    FROM (
                        SELECT A.ID_RUTA,
                               (
                                   CASE 
                                       WHEN TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') >= TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')
                                            AND (TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440 <= 10
                                       THEN (TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440
                                       ELSE 0
                                   END
                                   +
                                   CASE 
                                       WHEN TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') >= TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')
                                            AND (TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440 <= 10
                                       THEN (TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440
                                       ELSE 0
                                   END
                               ) AS MINS_TOTAL,
                               (
                                   CASE 
                                       WHEN TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') >= TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')
                                            AND (TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440 <= 10
                                       THEN 1 ELSE 0
                                   END
                                   +
                                   CASE 
                                       WHEN TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') >= TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')
                                            AND (TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440 <= 10
                                       THEN 1 ELSE 0
                                   END
                               ) AS CNT_TOTAL
                        FROM HISTORIAL H
                        JOIN ASIGNACION_TREN A ON H.ID_ASIGNACION = A.ID_ASIGNACION
                        JOIN HORARIO HO ON A.ID_HORARIO = HO.ID_HORARIO
                        WHERE H.HORA_REAL IS NOT NULL
                    ) T
                    GROUP BY T.ID_RUTA
                ) D ON D.ID_RUTA = R.ID_RUTA
                LEFT JOIN (
                    SELECT A.ID_RUTA, COUNT(*) CNT_INC
                    FROM INCIDENCIA I
                    JOIN ASIGNACION_TREN A ON I.ID_ASIGNACION = A.ID_ASIGNACION
                    GROUP BY A.ID_RUTA
                ) I ON I.ID_RUTA = R.ID_RUTA
                ORDER BY R.ID_RUTA
                """
            )

            if not filas:
                self.tabla_reporte_rutas.setRowCount(0)
                return

            # Preparar la tabla
            self.tabla_reporte_rutas.setRowCount(len(filas))
            self.tabla_reporte_rutas.setSortingEnabled(False)

            for i, (id_ruta, num_asignaciones, retraso_promedio, num_incidencias) in enumerate(filas):
                # El retraso_promedio ahora viene desde SQL (puede ser None)

                # Insertar datos en la tabla
                self.tabla_reporte_rutas.setItem(i, 0, QTableWidgetItem(str(id_ruta)))
                self.tabla_reporte_rutas.setItem(i, 1, QTableWidgetItem(str(num_asignaciones)))
                self.tabla_reporte_rutas.setItem(i, 2, QTableWidgetItem(f"{float(retraso_promedio):.1f} min" if retraso_promedio is not None else "N/A"))
                self.tabla_reporte_rutas.setItem(i, 3, QTableWidgetItem(str(num_incidencias)))

            # Ajustes finales
            self.tabla_reporte_rutas.setSortingEnabled(True)
            self.tabla_reporte_rutas.resizeColumnsToContents()

        except Exception as e:
            logger.exception("Error al generar reporte de rutas: %s", e)
            self.tabla_reporte_rutas.setRowCount(0)
            QMessageBox.warning(self, "Error", f"No se pudo generar el reporte: {str(e)}")

    def calcular_retraso_promedio_ruta(self, id_ruta: int) -> Optional[float]:
        try:
            # 1. Obtener todas las asignaciones para esta ruta
            asignaciones = self.db.fetch_all("""
                SELECT A.ID_ASIGNACION, A.ID_HORARIO
                FROM ASIGNACION_TREN A
                WHERE A.ID_RUTA = :id_ruta
            """, {"id_ruta": id_ruta})

            if not asignaciones:
                return None

            total_retrasos = 0
            total_registros = 0

            for id_asignacion, id_horario in asignaciones:
                # 2. Obtener horario programado
                horario = self.db.fetch_one("""
                    SELECT 
                        TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'),
                        TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
                    FROM HORARIO
                    WHERE ID_HORARIO = :id_horario
                """, {"id_horario": id_horario})

                if not horario:
                    continue

                hora_salida_prog, hora_llegada_prog = horario

                # 3. Obtener registros históricos con horas reales
                registros = self.db.fetch_all("""
                    SELECT HORA_REAL
                    FROM HISTORIAL
                    WHERE ID_ASIGNACION = :id_asignacion 
                      AND HORA_REAL IS NOT NULL
                """, {"id_asignacion": id_asignacion})

                for (hora_real_str,) in registros:
                    # Extraer horas de salida y llegada reales
                    try:
                        # Formato: "HH:mm:ss-HH:mm:ss"
                        hora_salida_real_str, hora_llegada_real_str = hora_real_str.split('-')

                        # Convertir a objetos datetime.time para comparación
                        from datetime import datetime
                        hora_salida_real = datetime.strptime(hora_salida_real_str, '%H:%M:%S').time()
                        hora_llegada_real = datetime.strptime(hora_llegada_real_str, '%H:%M:%S').time()
                        hora_salida_prog_obj = datetime.strptime(hora_salida_prog, '%H:%M:%S').time()
                        hora_llegada_prog_obj = datetime.strptime(hora_llegada_prog, '%H:%M:%S').time()

                        # Calcular diferencia en minutos (considerando días diferentes)
                        def calcular_diferencia_minutos(hora_real, hora_prog):
                            real = datetime.combine(datetime.today(), hora_real)
                            prog = datetime.combine(datetime.today(), hora_prog)
                            if real < prog:  # Si llegó temprano, considerar como 0
                                return 0
                            return (real - prog).total_seconds() / 60

                        retraso_salida = calcular_diferencia_minutos(hora_salida_real, hora_salida_prog_obj)
                        retraso_llegada = calcular_diferencia_minutos(hora_llegada_real, hora_llegada_prog_obj)

                        # Solo considerar retrasos entre 1 y 10 minutos
                        if 0 < retraso_salida <= 10:
                            total_retrasos += retraso_salida
                            total_registros += 1

                        if 0 < retraso_llegada <= 10:
                            total_retrasos += retraso_llegada
                            total_registros += 1

                    except Exception as e:
                        logger.exception("Error procesando registro %s: %s", hora_real_str, e)
                        continue

            return total_retrasos / total_registros if total_registros > 0 else 0.0

        except Exception as e:
            logger.exception("Error al calcular retraso para ruta %s: %s", id_ruta, e)
            return None
        
    def generar_reporte_trenes(self) -> None:
        try:
            # 1. Reporte agregado de trenes (asignaciones, retraso promedio en SQL, incidencias)
            filas = self.db.fetch_all(
                """
                SELECT T.ID_TREN,
                       NVL(A.CNT_ASIG, 0) AS ASIGNACIONES,
                       D.RETRASO_PROMEDIO,
                       NVL(I.CNT_INC, 0) AS INCIDENCIAS
                FROM TREN T
                LEFT JOIN (
                    SELECT ID_TREN, COUNT(*) CNT_ASIG
                    FROM ASIGNACION_TREN
                    GROUP BY ID_TREN
                ) A ON A.ID_TREN = T.ID_TREN
                LEFT JOIN (
                    SELECT T2.ID_TREN,
                           CASE WHEN SUM(T2.CNT_TOTAL) > 0 THEN SUM(T2.MINS_TOTAL) / SUM(T2.CNT_TOTAL) END AS RETRASO_PROMEDIO
                    FROM (
                        SELECT A.ID_TREN,
                               (
                                   CASE 
                                       WHEN TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') >= TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')
                                            AND (TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440 <= 10
                                       THEN (TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440
                                       ELSE 0
                                   END
                                   +
                                   CASE 
                                       WHEN TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') >= TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')
                                            AND (TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440 <= 10
                                       THEN (TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440
                                       ELSE 0
                                   END
                               ) AS MINS_TOTAL,
                               (
                                   CASE 
                                       WHEN TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') >= TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')
                                            AND (TO_DATE(SUBSTR(H.HORA_REAL, 1, INSTR(H.HORA_REAL,'-')-1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440 <= 10
                                       THEN 1 ELSE 0
                                   END
                                   +
                                   CASE 
                                       WHEN TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') >= TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')
                                            AND (TO_DATE(SUBSTR(H.HORA_REAL, INSTR(H.HORA_REAL,'-')+1), 'HH24:MI:SS') - TO_DATE(TO_CHAR(HO.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 'HH24:MI:SS')) * 1440 <= 10
                                       THEN 1 ELSE 0
                                   END
                               ) AS CNT_TOTAL
                        FROM HISTORIAL H
                        JOIN ASIGNACION_TREN A ON H.ID_ASIGNACION = A.ID_ASIGNACION
                        JOIN HORARIO HO ON A.ID_HORARIO = HO.ID_HORARIO
                        WHERE H.HORA_REAL IS NOT NULL
                    ) T2
                    GROUP BY T2.ID_TREN
                ) D ON D.ID_TREN = T.ID_TREN
                LEFT JOIN (
                    SELECT A.ID_TREN, COUNT(*) CNT_INC
                    FROM INCIDENCIA I
                    JOIN ASIGNACION_TREN A ON I.ID_ASIGNACION = A.ID_ASIGNACION
                    GROUP BY A.ID_TREN
                ) I ON I.ID_TREN = T.ID_TREN
                ORDER BY T.ID_TREN
                """
            )

            if not filas:
                self.tabla_reporte_trenes.setRowCount(0)
                return

            # Preparar la tabla
            self.tabla_reporte_trenes.setRowCount(len(filas))
            self.tabla_reporte_trenes.setSortingEnabled(False)

            for i, (id_tren, num_asignaciones, retraso_promedio, num_incidencias) in enumerate(filas):
                # El retraso_promedio ahora viene desde SQL (puede ser None)

                # Insertar datos en la tabla
                self.tabla_reporte_trenes.setItem(i, 0, QTableWidgetItem(f"{id_tren}"))
                self.tabla_reporte_trenes.setItem(i, 1, QTableWidgetItem(str(num_asignaciones)))
                self.tabla_reporte_trenes.setItem(i, 2, QTableWidgetItem(f"{float(retraso_promedio):.1f} min" if retraso_promedio is not None else "N/A"))
                self.tabla_reporte_trenes.setItem(i, 3, QTableWidgetItem(str(num_incidencias)))

            # Ajustes finales
            self.tabla_reporte_trenes.setSortingEnabled(True)
            self.tabla_reporte_trenes.resizeColumnsToContents()

        except Exception as e:
            logger.exception("Error al generar reporte de trenes: %s", e)
            self.tabla_reporte_trenes.setRowCount(0)
            QMessageBox.warning(self, "Error", f"No se pudo generar el reporte de trenes: {str(e)}")

    def calcular_retraso_promedio_tren(self, id_tren: int) -> Optional[float]:
        try:
            # 1. Obtener todas las asignaciones para este tren
            asignaciones = self.db.fetch_all("""
                SELECT A.ID_ASIGNACION, A.ID_HORARIO
                FROM ASIGNACION_TREN A
                WHERE A.ID_TREN = :id_tren
            """, {"id_tren": id_tren})

            if not asignaciones:
                return None

            total_retrasos = 0
            total_registros = 0

            for id_asignacion, id_horario in asignaciones:
                # 2. Obtener horario programado
                horario = self.db.fetch_one("""
                    SELECT 
                        TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'),
                        TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
                    FROM HORARIO
                    WHERE ID_HORARIO = :id_horario
                """, {"id_horario": id_horario})

                if not horario:
                    continue
                
                hora_salida_prog, hora_llegada_prog = horario

                # 3. Obtener registros históricos con horas reales
                registros = self.db.fetch_all("""
                    SELECT HORA_REAL
                    FROM HISTORIAL
                    WHERE ID_ASIGNACION = :id_asignacion 
                      AND HORA_REAL IS NOT NULL
                """, {"id_asignacion": id_asignacion})

                for (hora_real_str,) in registros:
                    # Extraer horas de salida y llegada reales
                    try:
                        # Formato: "HH:mm:ss-HH:mm:ss"
                        hora_salida_real_str, hora_llegada_real_str = hora_real_str.split('-')

                        # Convertir a objetos datetime.time para comparación
                        from datetime import datetime
                        hora_salida_real = datetime.strptime(hora_salida_real_str, '%H:%M:%S').time()
                        hora_llegada_real = datetime.strptime(hora_llegada_real_str, '%H:%M:%S').time()
                        hora_salida_prog_obj = datetime.strptime(hora_salida_prog, '%H:%M:%S').time()
                        hora_llegada_prog_obj = datetime.strptime(hora_llegada_prog, '%H:%M:%S').time()

                        # Calcular diferencia en minutos (considerando días diferentes)
                        def calcular_diferencia_minutos(hora_real, hora_prog):
                            real = datetime.combine(datetime.today(), hora_real)
                            prog = datetime.combine(datetime.today(), hora_prog)
                            if real < prog:  # Si llegó temprano, considerar como 0
                                return 0
                            return (real - prog).total_seconds() / 60

                        retraso_salida = calcular_diferencia_minutos(hora_salida_real, hora_salida_prog_obj)
                        retraso_llegada = calcular_diferencia_minutos(hora_llegada_real, hora_llegada_prog_obj)

                        # Solo considerar retrasos entre 1 y 10 minutos
                        if 0 < retraso_salida <= 10:
                            total_retrasos += retraso_salida
                            total_registros += 1

                        if 0 < retraso_llegada <= 10:
                            total_retrasos += retraso_llegada
                            total_registros += 1

                    except Exception as e:
                        logger.exception("Error procesando registro %s: %s", hora_real_str, e)
                        continue
                    
            return total_retrasos / total_registros if total_registros > 0 else 0.0

        except Exception as e:
            logger.exception("Error al calcular retraso para tren %s: %s", id_tren, e)
            return None
        