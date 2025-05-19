from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                            QTableWidgetItem, QSplitter, QPushButton, QScrollArea, QStackedWidget, QSizePolicy, QFrame,
                            QAbstractItemView, QHeaderView)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QMessageBox
import oracledb
from interfaces.asignacion import InterfazAsignacion,InterfazModificarAsignacion
from interfaces.paneles.panel_horarios import InterfazAgregarHorario, InterfazEditarHorario
from interfaces.paneles.panel_rutas import InterfazAgregarRuta, InterfazEditarRuta

class GestionHorariosRutas(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db  # Usar la conexión existente

        self.setWindowTitle("Gestión de Horarios y Rutas")
        self.setGeometry(100, 100, 1000, 600)

        self.initUI()
        self.load_routes()
        self.load_schedules()
        self.load_train_availability()
        self.load_asignaciones()  # Nueva función para cargar asignaciones

    def initUI(self):
        # Layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Encabezado con estilo mejorado
        header_layout = QHBoxLayout()
        label = QLabel("Gestión de Horarios y Rutas")
        label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0;
                border-bottom: 2px solid #3498db;
            }
        """)
        header_layout.addWidget(label)
        header_layout.setContentsMargins(0, 0, 0, 10)
        layout.addLayout(header_layout)

        # Separador principal (manteniendo distribución original)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Sección izquierda ---
        left_container = QWidget()
        left_container.setMinimumWidth(645)  # Manteniendo ancho original
        left_section = QVBoxLayout(left_container)
        left_section.setContentsMargins(0, 0, 0, 0)
        left_section.setSpacing(10)

        # Tabla de rutas con estilo
        routes_label = QLabel("Rutas")
        routes_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.tabla_rutas = QTableWidget()
        self.tabla_rutas.setColumnCount(3)
        self.tabla_rutas.setHorizontalHeaderLabels(["ID Ruta", "Duración", "Estaciones"])
        self._configurar_tabla(self.tabla_rutas)
        self.tabla_rutas.itemSelectionChanged.connect(self._controlar_boton_ruta)
        left_section.addWidget(routes_label)
        left_section.addWidget(self.tabla_rutas)

        # Contenedor para tablas de horarios y disponibilidad
        schedules_container = QHBoxLayout()
        schedules_container.setSpacing(10)

        # Tabla de horarios con estilo
        schedules_label = QLabel("Horarios")
        schedules_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.tabla_horarios = QTableWidget()
        self.tabla_horarios.setColumnCount(3)
        self.tabla_horarios.setHorizontalHeaderLabels(["ID Horario", "Salida", "Llegada"])
        self._configurar_tabla(self.tabla_horarios)
        self.tabla_horarios.itemSelectionChanged.connect(self._controlar_boton_horario)

        # Tabla de disponibilidad de trenes con estilo
        availability_label = QLabel("Disponibilidad de Trenes")
        availability_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.tabla_trenes = QTableWidget()
        self.tabla_trenes.setColumnCount(3)
        self.tabla_trenes.setHorizontalHeaderLabels(["ID Tren", "Nombre", "Estado"])
        self._configurar_tabla(self.tabla_trenes)

        # Layouts para las tablas inferiores
        schedules_left = QVBoxLayout()
        schedules_left.setSpacing(5)
        schedules_left.addWidget(schedules_label)
        schedules_left.addWidget(self.tabla_horarios)

        schedules_right = QVBoxLayout()
        schedules_right.setSpacing(5)
        schedules_right.addWidget(availability_label)
        schedules_right.addWidget(self.tabla_trenes)

        schedules_container.addLayout(schedules_left)
        schedules_container.addLayout(schedules_right)
        left_section.addLayout(schedules_container)

        main_splitter.addWidget(left_container)

        # --- Sección derecha ---
        right_container = QWidget()
        right_section = QVBoxLayout(right_container)
        right_section.setContentsMargins(10, 0, 0, 0)
        right_section.setSpacing(10)
        
        # Contenedor scroll para la imagen de la ruta
        img_scroll = QScrollArea()
        img_scroll.setWidgetResizable(True)
        img_scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Imagen de la ruta con borde
        self.img_ruta = QLabel("Imagen de la ruta")
        self.img_ruta.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                background-color: white;
            }
        """)
        self.img_ruta.setFixedSize(700, 400)
        self.img_ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_ruta.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Configurar el scroll area
        img_scroll.setWidget(self.img_ruta)
        right_section.addWidget(img_scroll)

        # Tabla de asignaciones con estilo
        asignaciones_label = QLabel("Asignaciones de Trenes")
        asignaciones_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.tabla_asignaciones = QTableWidget()
        self.tabla_asignaciones.setColumnCount(5)
        self.tabla_asignaciones.setHorizontalHeaderLabels(["ID Asignación", "Tren", "Ruta", "Horario", "Estado"])
        self._configurar_tabla(self.tabla_asignaciones)
        self.tabla_asignaciones.itemSelectionChanged.connect(self._controlar_boton_asignacion)
        right_section.addWidget(asignaciones_label)
        right_section.addWidget(self.tabla_asignaciones)

        main_splitter.addWidget(right_container)
        layout.addWidget(main_splitter)

        # --- Botones de acción ---
        # Estilo base para botones
        button_style = """
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """

        # Botones para horarios
        horario_buttons = QHBoxLayout()
        horario_buttons.setSpacing(10)

        self.btn_agregar_horario = QPushButton("Agregar Horario")
        self.btn_agregar_horario.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2ecc71;
                color: white;
            }
        """)
        self.btn_agregar_horario.clicked.connect(lambda: self.mostrar_panel(0))

        self.btn_editar_horario = QPushButton("Editar Horario")
        self.btn_editar_horario.setStyleSheet(button_style + """
            QPushButton {
                background-color: #3498db;
                color: white;
            }
        """)
        self.btn_editar_horario.setEnabled(False)
        self.btn_editar_horario.clicked.connect(self.abrir_edicion_horario)

        self.btn_eliminar_horario = QPushButton("Eliminar Horario")
        self.btn_eliminar_horario.setStyleSheet(button_style + """
            QPushButton {
                background-color: #e74c3c;
                color: white;
            }
        """)
        self.btn_eliminar_horario.setEnabled(False)
        self.btn_eliminar_horario.clicked.connect(self.eliminar_horario)

        horario_buttons.addWidget(self.btn_agregar_horario)
        horario_buttons.addWidget(self.btn_editar_horario)
        horario_buttons.addWidget(self.btn_eliminar_horario)
        layout.addLayout(horario_buttons)

        # Botones para rutas
        ruta_buttons = QHBoxLayout()
        ruta_buttons.setSpacing(10)

        self.btn_agregar_ruta = QPushButton("Agregar Ruta")
        self.btn_agregar_ruta.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2ecc71;
                color: white;
            }
        """)
        self.btn_agregar_ruta.clicked.connect(lambda: self.mostrar_panel(1))

        self.btn_editar_ruta = QPushButton("Editar Ruta")
        self.btn_editar_ruta.setStyleSheet(button_style + """
            QPushButton {
                background-color: #3498db;
                color: white;
            }
        """)
        self.btn_editar_ruta.setEnabled(False)
        self.btn_editar_ruta.clicked.connect(self.abrir_edicion_ruta)

        self.btn_eliminar_ruta = QPushButton("Eliminar Ruta")
        self.btn_eliminar_ruta.setStyleSheet(button_style + """
            QPushButton {
                background-color: #e74c3c;
                color: white;
            }
        """)
        self.btn_eliminar_ruta.setEnabled(False)
        self.btn_eliminar_ruta.clicked.connect(self.eliminar_ruta)

        ruta_buttons.addWidget(self.btn_agregar_ruta)
        ruta_buttons.addWidget(self.btn_editar_ruta)
        ruta_buttons.addWidget(self.btn_eliminar_ruta)
        layout.addLayout(ruta_buttons)

        # Botones para asignación de trenes
        asignacion_buttons = QHBoxLayout()
        asignacion_buttons.setSpacing(10)

        self.btn_asignar_tren = QPushButton("Asignar Tren")
        self.btn_asignar_tren.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2ecc71;
                color: white;
            }
        """)
        self.btn_asignar_tren.clicked.connect(lambda: self.mostrar_panel(2))

        self.btn_modificar_asignacion = QPushButton("Modificar Asignación")
        self.btn_modificar_asignacion.setStyleSheet(button_style + """
            QPushButton {
                background-color: #3498db;
                color: white;
            }
        """)
        self.btn_modificar_asignacion.setEnabled(False)
        self.btn_modificar_asignacion.clicked.connect(self.abrir_edicion_asignacion)

        self.btn_quitar_asignacion = QPushButton("Quitar Asignación")
        self.btn_quitar_asignacion.setStyleSheet(button_style + """
            QPushButton {
                background-color: #e74c3c;
                color: white;
            }
        """)
        self.btn_quitar_asignacion.setEnabled(False)
        self.btn_quitar_asignacion.clicked.connect(self.eliminar_asignacion)

        asignacion_buttons.addWidget(self.btn_asignar_tren)
        asignacion_buttons.addWidget(self.btn_modificar_asignacion)
        asignacion_buttons.addWidget(self.btn_quitar_asignacion)
        layout.addLayout(asignacion_buttons)
        
        # Contenedor apilado
        self.stacked = QStackedWidget()
        self.stacked.hide()

        #Panel para agregar horarios
        self.scroll_horarios = QScrollArea()
        self.scroll_horarios.setWidgetResizable(True)
        self.scroll_horarios.hide()
        self.panel_horarios = InterfazAgregarHorario(self.main_window, self.db)
        self.panel_horarios.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_horarios.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_horarios.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_horarios.setWidget(self.panel_horarios)
        
        #Panel para agregar rutas
        self.scroll_rutas = QScrollArea()
        self.scroll_rutas.setWidgetResizable(True)
        self.scroll_rutas.hide()
        self.panel_rutas = InterfazAgregarRuta(self.main_window, self.db)
        self.panel_rutas.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_rutas.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_rutas.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_rutas.setWidget(self.panel_rutas)
        
        # Panel de asignación de trenes (oculto por defecto)
        self.scroll_asignacion = QScrollArea()
        self.scroll_asignacion.setWidgetResizable(True)
        self.scroll_asignacion.hide()  # Oculto inicialmente
        self.panel_asignacion = InterfazAsignacion(self.main_window, self.db)
        self.panel_asignacion.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_asignacion.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.scroll_asignacion.setWidget(self.panel_asignacion)
        
        #Panel para editar horarios
        self.scroll_horarios2 = QScrollArea()
        self.scroll_horarios2.setWidgetResizable(True)
        self.scroll_horarios2.hide()
        self.panel_horarios2 = InterfazEditarHorario(self.main_window, self.db, self.username)
        self.panel_horarios2.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_horarios2.btn_cancelar.clicked.connect(self.bloquear_botones_horario)
        self.panel_horarios2.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_horarios2.btn_confirmar.clicked.connect(self.bloquear_botones_horario)
        self.panel_horarios2.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_horarios2.setWidget(self.panel_horarios2)
        
        #Panel para agregar rutas
        self.scroll_rutas2 = QScrollArea()
        self.scroll_rutas2.setWidgetResizable(True)
        self.scroll_rutas2.hide()
        self.panel_rutas2 = InterfazEditarRuta(self.main_window, self.db, self.username)
        self.panel_rutas2.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_rutas2.btn_cancelar.clicked.connect(self.bloquear_botones_ruta)
        self.panel_rutas2.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_rutas2.btn_confirmar.clicked.connect(self.bloquear_botones_ruta)
        self.panel_rutas2.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_rutas2.setWidget(self.panel_rutas2)

        # Panel de modificación de asignación
        self.scroll_modificar_asignacion = QScrollArea()
        self.scroll_modificar_asignacion.setWidgetResizable(True)
        self.scroll_modificar_asignacion.hide()
        self.scroll_modificar_asignacion.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_modificar_asignacion.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_modificar_asignacion.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Contenedor con layout para el scroll
        contenedor_modificar = QWidget()
        layout_modificar = QVBoxLayout(contenedor_modificar)
        layout_modificar.setContentsMargins(0, 0, 0, 0)
        layout_modificar.setSpacing(0)

        self.panel_modificar_asignacion = InterfazModificarAsignacion(self.main_window, self.db, self.username)
        self.panel_modificar_asignacion.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_modificar_asignacion.btn_cancelar.clicked.connect(self.bloquear_botones_asignacion)
        self.panel_modificar_asignacion.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_modificar_asignacion.btn_cancelar.clicked.connect(self.bloquear_botones_asignacion)
        self.panel_modificar_asignacion.btn_confirmar.clicked.connect(self.actualizar_datos)

        layout_modificar.addWidget(self.panel_modificar_asignacion)
        self.scroll_modificar_asignacion.setWidget(contenedor_modificar)
        
        self.stacked.addWidget(self.scroll_horarios)
        self.stacked.addWidget(self.scroll_rutas)
        self.stacked.addWidget(self.scroll_asignacion)
        self.stacked.addWidget(self.scroll_horarios2)
        self.stacked.addWidget(self.scroll_rutas2)
        self.stacked.addWidget(self.scroll_modificar_asignacion)  
        layout.addWidget(self.stacked)

        self.setLayout(layout)
    
    def _configurar_tabla(self, tabla):
        """Configura el estilo común para todas las tablas"""
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
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #eee;
            }
        """)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    
    def _controlar_boton_asignacion(self):
        """Habilita/deshabilita los botones según la selección"""
        hay_seleccion = self.tabla_asignaciones.currentRow() >= 0
        self.btn_modificar_asignacion.setEnabled(hay_seleccion)
        self.btn_quitar_asignacion.setEnabled(hay_seleccion)

    def bloquear_botones_horario(self):
        self.tabla_horarios.clearSelection()
        self.tabla_horarios.clearFocus()
        self.btn_eliminar_horario.setEnabled(False)
        self.btn_editar_horario.setEnabled(False)
        
    def bloquear_botones_ruta(self):
        self.tabla_rutas.clearSelection()
        self.tabla_rutas.clearFocus()
        self.btn_eliminar_ruta.setEnabled(False)
        self.btn_editar_ruta.setEnabled(False)

    def bloquear_botones_asignacion(self):
        self.tabla_asignaciones.clearSelection()
        self.tabla_asignaciones.clearFocus()
        self.btn_modificar_asignacion.setEnabled(False)
        self.btn_quitar_asignacion.setEnabled(False)

    def _controlar_boton_ruta(self):
        if self.tabla_rutas.currentRow() == -1:
            self.btn_eliminar_ruta.setEnabled(False)
            self.btn_editar_ruta.setEnabled(False)
        else:
            self.btn_eliminar_ruta.setEnabled(True)
            self.btn_editar_ruta.setEnabled(True)

    def _controlar_boton_horario(self):
        if self.tabla_horarios.currentRow() == -1:
            self.btn_eliminar_horario.setEnabled(False)
            self.btn_editar_horario.setEnabled(False)
        else:
            self.btn_eliminar_horario.setEnabled(True)
            self.btn_editar_horario.setEnabled(True)
            
    def _controlar_boton_asignacion(self):
        if self.tabla_asignaciones.currentRow() == -1:
            self.btn_quitar_asignacion.setEnabled(False)
            self.btn_modificar_asignacion.setEnabled(False)
        else:
            self.btn_quitar_asignacion.setEnabled(True)
            self.btn_modificar_asignacion.setEnabled(True)

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
        self.load_routes()
        self.load_schedules()
        self.load_train_availability()
        self.load_asignaciones()

    def abrir_edicion_horario(self):
        fila = self.tabla_horarios.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona un horario para editar.")
            return

        id_horario = self.tabla_horarios.item(fila, 0).text()
        hora_salida = self.tabla_horarios.item(fila, 1).text()
        hora_llegada = self.tabla_horarios.item(fila, 2).text()

        datos_horario = {
            "id": id_horario,
            "salida": hora_salida,
            "llegada": hora_llegada
        }

        self.panel_horarios2.cargar_horario(datos_horario)
        self.mostrar_panel(3)
        
    def abrir_edicion_ruta(self):
        fila = self.tabla_rutas.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona una ruta para editar")
            return
        
        id_ruta = self.tabla_rutas.item(fila, 0).text()
        duracion = self.tabla_rutas.item(fila, 1).text()
        estaciones = self.tabla_rutas.item(fila, 2).text()
        datos_ruta = {
            "id": id_ruta,
            "duracion": duracion,
            "estaciones": estaciones
        }
        self.panel_rutas2.cargar_ruta(datos_ruta)
        self.mostrar_panel(4)

    def load_routes(self):
        """Carga las rutas con su duración y secuencia de estaciones"""
        query = """
            SELECT R.ID_RUTA, R.DURACION_ESTIMADA,
                    LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ESTACIONES
            FROM RUTA R
            JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
            JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
            GROUP BY R.ID_RUTA, R.DURACION_ESTIMADA
        """
        routes = self.db.fetch_all(query)

        self.tabla_rutas.setRowCount(len(routes))
        for i, route in enumerate(routes):
            self.tabla_rutas.setItem(i, 0, QTableWidgetItem(str(route[0])))
            self.tabla_rutas.setItem(i, 1, QTableWidgetItem(str(route[1])))
            self.tabla_rutas.setItem(i, 2, QTableWidgetItem(route[2]))

        self.tabla_rutas.resizeColumnsToContents()
        self.tabla_rutas.resizeRowsToContents()

        # Conectar la selección de una ruta con la carga de la imagen
        self.tabla_rutas.selectionModel().selectionChanged.connect(self.on_route_selected)

        # Cargar automáticamente la imagen de la primera ruta (si existe)
        if routes:
            first_route_id = routes[0][0]  # Obtener el ID de la primera ruta
            self.load_route_image(first_route_id)  # Cargar la imagen de la primera ruta

    def on_route_selected(self):
        """Cargar la imagen de la ruta seleccionada"""
        selected_row = self.tabla_rutas.currentRow()  # Obtener la fila seleccionada
        if selected_row >= 0:  # Verificar que se haya seleccionado una fila
            route_id = self.tabla_rutas.item(selected_row, 0).text()  # Obtener el ID de la ruta
            self.load_route_image(route_id)  # Cargar la imagen de la ruta

    def load_schedules(self):
        """Carga los horarios con los trenes asignados"""
        query = """
            SELECT ID_HORARIO,
                    TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'),
                    TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
            FROM HORARIO
            ORDER BY 1 ASC
        """
        schedules = self.db.fetch_all(query)

        self.tabla_horarios.setRowCount(len(schedules))
        for i, schedule in enumerate(schedules):
            self.tabla_horarios.setItem(i, 0, QTableWidgetItem(str(schedule[0])))
            self.tabla_horarios.setItem(i, 1, QTableWidgetItem(schedule[1]))
            self.tabla_horarios.setItem(i, 2, QTableWidgetItem(schedule[2]))

        self.tabla_horarios.resizeColumnsToContents()
        self.tabla_horarios.resizeRowsToContents()

    def load_train_availability(self):
        """Calcula la disponibilidad de los trenes"""
        query = """
            SELECT T.ID_TREN, T.NOMBRE, T.ESTADO
            FROM TREN T
        """
        trains = self.db.fetch_all(query)

        self.tabla_trenes.setRowCount(len(trains))
        for i, train in enumerate(trains):
            self.tabla_trenes.setItem(i, 0, QTableWidgetItem(str(train[0])))
            self.tabla_trenes.setItem(i, 1, QTableWidgetItem(train[1]))
            self.tabla_trenes.setItem(i, 2, QTableWidgetItem(train[2]))

        self.tabla_trenes.resizeColumnsToContents()
        self.tabla_trenes.resizeRowsToContents()

    def load_route_image(self, id_ruta):
        """Carga la imagen de la ruta desde la base de datos"""
        query = "SELECT IMAGEN FROM RUTA WHERE ID_RUTA = :1"
        image_data = self.db.fetch_all(query, (id_ruta,))  # Ahora se usa fetch_all

        if image_data and image_data[0][0]:
            # Obtener el LOB
            image_lob = image_data[0][0]

            # Leer el LOB completo en memoria
            image_bytes = image_lob.read()  # Leer el contenido del LOB

            # Convertir los bytes a un QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes)  # Cargar la imagen desde los bytes

            # Ajustar el tamaño de la imagen para que no distorsione el layout
            pixmap = pixmap.scaled(700, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            self.img_ruta.setPixmap(pixmap)  # Establecer la imagen en el QLabel
        else:
            self.img_ruta.setText("No disponible")  # Si no hay imagen disponible, mostrar mensaje

    def cargar_datos(self):
        """Recarga los datos de la interfaz de gestión de horarios y rutas"""
        print("Cargando datos en GestionHorariosRutas...")
        self.load_routes()
        self.load_schedules()
        self.load_train_availability()

    def eliminar_horario(self):
        """Elimina un horario seleccionado
            guarda en el historial el horario antes de borrarlo y agrega una nota de que se elimino"""
        self.ocultar_panel()
        # Obtiene horario seleccionado
        fila = self.tabla_horarios.currentRow()
        # Si no hay horario seleccionado manda una advertencia
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona un horario para eliminar.")
            return

        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar eliminación")
        confirmacion.setText(f"¿Estás seguro de que deseas eliminar el horario #{self.tabla_horarios.item(fila, 0).text()}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
        
        try:
            if confirmacion.exec() == 2:
                cursor = self.db.connection.cursor()
                # Se genera el id del nuevo registro del historial
                cursor.execute("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
                nuevo_id = cursor.fetchone()[0]
                # Se inserta en historial
                cursor.execute("""
                    INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_HORARIO, FECHA_REGISTRO)
                    VALUES (:1, :2, :3, :4, SYSDATE)
                """, (nuevo_id, self.tabla_horarios.item(fila, 1).text() + " - " + self.tabla_horarios.item(fila, 2).text(),
                      self.username, self.tabla_horarios.item(fila, 0).text(),))
                # Se elimina el horario
                cursor.execute("""
                    DELETE FROM HORARIO WHERE ID_HORARIO = :1
                """, (self.tabla_horarios.item(fila, 0).text(),))
                # Realiza commit
                self.db.connection.commit()
                # Se notifica que el horario se elimino
                self.db.event_manager.update_triggered.emit()
                QMessageBox.information(self, "Resultado", "El horario se ha eliminado correctamente.")
                self.actualizar_datos()
                self.bloquear_botones_horario()
            else:
                self.bloquear_botones_horario()
        except Exception as e:
            QMessageBox.critical(self, "Error al eliminar", str(e))

    def eliminar_ruta(self):
        """Elimina un horario seleccionado
            guarda en el historial el horario antes de borrarlo y agrega una nota de que se elimino"""
        self.ocultar_panel()
        # Obtiene horario seleccionado
        fila = self.tabla_rutas.currentRow()
        # Si no hay horario seleccionado manda una advertencia
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona un horario para eliminar.")
            return

        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar eliminación")
        confirmacion.setText(f"¿Estás seguro de que deseas eliminar la ruta #{self.tabla_rutas.item(fila, 0).text()}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)

        try:
            if confirmacion.exec() == 2:
                cursor = self.db.connection.cursor()
                # Se genera el id del nuevo registro del historial
                cursor.execute("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
                nuevo_id = cursor.fetchone()[0]
                # Se inserta en historial
                cursor.execute("""
                    INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_RUTA, FECHA_REGISTRO)
                    VALUES (:1, :2, :3, :4, SYSDATE)
                """, (nuevo_id, "Duracion: " + self.tabla_rutas.item(fila, 1).text() + "; Orden: "
                      + self.tabla_rutas.item(fila, 2).text(),
                      self.username, self.tabla_rutas.item(fila, 0).text(),))
                # Se elimina el horario
                cursor.execute("""
                    DELETE FROM RUTA WHERE ID_RUTA = :1
                """, (self.tabla_rutas.item(fila, 0).text(),))
                # Realiza commit
                self.db.connection.commit()
                # Se notifica que el horario se elimino
                self.db.event_manager.update_triggered.emit()
                QMessageBox.information(self, "Resultado", "La ruta se ha eliminado correctamente.")
                self.actualizar_datos()
                self.bloquear_botones_ruta()
            else:
                self.bloquear_botones_ruta()
        except Exception as e:
            QMessageBox.critical(self, "Error al eliminar", str(e))

    def eliminar_asignacion(self):
        """Elimina la asignación seleccionada en la tabla"""
        fila = self.tabla_asignaciones.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona una asignación para eliminar.")
            return

        id_asignacion = self.tabla_asignaciones.item(fila, 0).text()  # Columna 0 = ID Asignación

        confirmacion = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar la asignación {id_asignacion}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmacion == QMessageBox.StandardButton.Yes:
            try:
                cursor = self.db.connection.cursor()
                # Insertar en historial
                cursor.execute("""
                    INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_ASIGNACION, FECHA_REGISTRO)
                    VALUES ((SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL), 
                    'Asignación eliminada', :1, :2, SYSDATE)
                """, (self.username, id_asignacion))
                
                # Eliminar asignación
                cursor.execute("DELETE FROM ASIGNACION_TREN WHERE ID_ASIGNACION = :1", (id_asignacion,))
                self.db.connection.commit()
                self.db.event_manager.update_triggered.emit()
                
                QMessageBox.information(self, "Éxito", "Asignación eliminada correctamente.")
                self.load_asignaciones()  # Recargar la tabla
            except Exception as e:
                self.db.connection.rollback()
                QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")
                
        self.bloquear_botones_asignacion()

    
    def abrir_edicion_asignacion(self):
        """Abre el panel de edición con los datos de la asignación seleccionada"""
        fila = self.tabla_asignaciones.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona una asignación para modificar.")
            return

        id_asignacion = self.tabla_asignaciones.item(fila, 0).text()

        self.panel_modificar_asignacion.set_asignacion(int(id_asignacion))
        self.mostrar_panel(5)  # índice 5 corresponde a scroll_modificar_asignacion


    def mostrar_panel_modificar_asignacion(self):
        """Muestra el panel de modificación de asignación"""
        self.stacked.setCurrentWidget(self.scroll_modificar_asignacion)
        #self.stacked.setCurrentIndex(5) 
        self.scroll_modificar_asignacion.show()
        self.scroll_modificar_asignacion.setMinimumHeight(400)
        self.scroll_modificar_asignacion.setMaximumHeight(400)

    def ocultar_panel_modificar_asignacion(self):
        """Oculta el panel de modificación de asignación"""
        self.scroll_modificar_asignacion.hide()
        self.tabla_asignaciones.clearSelection()
        self.btn_modificar_asignacion.setEnabled(False)

    def load_asignaciones(self):
        """Carga las asignaciones de trenes desde la base de datos"""
        query = """
            SELECT A.ID_ASIGNACION, 
                   T.NOMBRE AS TREN, 
                   R.ID_RUTA AS RUTA, 
                   H.ID_HORARIO AS HORARIO,
                   CASE 
                       WHEN A.HORA_SALIDA_REAL IS NULL THEN 'Pendiente'
                       ELSE 'Completado'
                   END AS ESTADO
            FROM ASIGNACION_TREN A
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            ORDER BY A.ID_ASIGNACION
        """
        asignaciones = self.db.fetch_all(query)

        self.tabla_asignaciones.setRowCount(len(asignaciones))
        for i, asignacion in enumerate(asignaciones):
            self.tabla_asignaciones.setItem(i, 0, QTableWidgetItem(str(asignacion[0])))
            self.tabla_asignaciones.setItem(i, 1, QTableWidgetItem(asignacion[1]))
            self.tabla_asignaciones.setItem(i, 2, QTableWidgetItem(str(asignacion[2])))
            self.tabla_asignaciones.setItem(i, 3, QTableWidgetItem(str(asignacion[3])))
            self.tabla_asignaciones.setItem(i, 4, QTableWidgetItem(asignacion[4]))

        self.tabla_asignaciones.resizeColumnsToContents()
        self.tabla_asignaciones.resizeRowsToContents()