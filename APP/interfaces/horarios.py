from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                            QTableWidgetItem, QSplitter, QPushButton)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

class GestionHorariosRutas(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db  # Usar la conexión existente

        self.setWindowTitle("Gestión de Horarios y Rutas")
        self.setGeometry(100, 100, 1000, 600)

        self.initUI()
        self.load_routes()
        self.load_schedules()
        self.load_train_availability()

    def initUI(self):
        layout = QVBoxLayout()

        # Crear el encabezado con el título
        header_layout = QHBoxLayout()
        label = QLabel("Gestión de Horarios y Rutas")

        # Alineación del widget a la izquierda
        header_layout.addWidget(label)

        # Ajuste de márgenes para que estén más cerca
        header_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes alrededor
        header_layout.setSpacing(20)  # Eliminar espacio entre los widgets

        # Agregar el layout al layout principal
        layout.addLayout(header_layout)

        # Separador para organizar tabla e imagen de ruta
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sección izquierda: Tablas de rutas y horarios
        left_section = QVBoxLayout()

        # Tabla de rutas con secuencia de estaciones
        self.tabla_rutas = QTableWidget()
        self.tabla_rutas.setColumnCount(3)
        self.tabla_rutas.setHorizontalHeaderLabels(["ID Ruta", "Duración", "Estaciones"])
        left_section.addWidget(self.tabla_rutas)

        # Tabla de horarios
        self.tabla_horarios = QTableWidget()
        self.tabla_horarios.setColumnCount(4)
        self.tabla_horarios.setHorizontalHeaderLabels(["ID Horario", "Salida", "Llegada", "Tren Asignado"])
        left_section.addWidget(self.tabla_horarios)

        # Contenedor izquierdo
        left_container = QWidget()
        left_container.setLayout(left_section)
        left_container.setMinimumWidth(645)  # Fijar un ancho mínimo para la sección izquierda
        splitter.addWidget(left_container)

        # Sección derecha: Imagen de la ruta
        right_section = QVBoxLayout()
        self.img_ruta = QLabel("Imagen de la ruta")
        self.img_ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_section.addWidget(self.img_ruta)

        # Contenedor derecho
        right_container = QWidget()
        right_container.setLayout(right_section)
        splitter.addWidget(right_container)

        layout.addWidget(splitter)

        # Tabla de disponibilidad de trenes
        self.tabla_trenes = QTableWidget()
        self.tabla_trenes.setColumnCount(3)
        self.tabla_trenes.setHorizontalHeaderLabels(["ID Tren", "Nombre", "Estado"])
        layout.addWidget(QLabel("Disponibilidad de Trenes"))
        layout.addWidget(self.tabla_trenes)

        # Botones de acción
        button_layout = QHBoxLayout()
        self.btn_agregar_horario = QPushButton("Agregar Horario")
        self.btn_editar_horario = QPushButton("Editar Horario")
        self.btn_eliminar_horario = QPushButton("Eliminar Horario")

        button_layout.addWidget(self.btn_agregar_horario)
        button_layout.addWidget(self.btn_editar_horario)
        button_layout.addWidget(self.btn_eliminar_horario)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de GestionHorariosRutas")
        self.load_routes()
        self.load_schedules()
        self.load_train_availability()

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
            SELECT H.ID_HORARIO,
                    TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'),
                    TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'),
                    T.NOMBRE
            FROM HORARIO H
            LEFT JOIN ASIGNACION_TREN A ON H.ID_HORARIO = A.ID_HORARIO
            LEFT JOIN TREN T ON A.ID_TREN = T.ID_TREN
        """
        schedules = self.db.fetch_all(query)

        self.tabla_horarios.setRowCount(len(schedules))
        for i, schedule in enumerate(schedules):
            self.tabla_horarios.setItem(i, 0, QTableWidgetItem(str(schedule[0])))
            self.tabla_horarios.setItem(i, 1, QTableWidgetItem(schedule[1]))
            self.tabla_horarios.setItem(i, 2, QTableWidgetItem(schedule[2]))
            self.tabla_horarios.setItem(i, 3, QTableWidgetItem(schedule[3] if schedule[3] else "No asignado"))

        self.tabla_horarios.resizeColumnsToContents()
        self.tabla_horarios.resizeRowsToContents()

    def load_train_availability(self):
        """Calcula la disponibilidad de los trenes"""
        query = """
            SELECT T.ID_TREN, T.NOMBRE,
                    CASE
                        WHEN T.ESTADO <> 'ACTIVO' THEN 'No disponible'
                        WHEN EXISTS (SELECT 1 FROM ASIGNACION_TREN A WHERE A.ID_TREN = T.ID_TREN)
                        THEN 'Asignado'
                        ELSE 'Disponible'
                    END AS DISPONIBILIDAD
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
            pixmap = pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio)

            self.img_ruta.setPixmap(pixmap)  # Establecer la imagen en el QLabel
        else:
            self.img_ruta.setText("No disponible")  # Si no hay imagen disponible, mostrar mensaje

    def cargar_datos(self):
        """Recarga los datos de la interfaz de gestión de horarios y rutas"""
        print("Cargando datos en GestionHorariosRutas...")
        self.load_routes()
        self.load_schedules()
        self.load_train_availability()

