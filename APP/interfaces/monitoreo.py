from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QProgressBar, QFrame
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
from base_de_datos.db import DatabaseConnection  
from base_de_datos.event_manager import EventManager

class MonitoreoInterface(QWidget):
    def __init__(self, main_window,db):
        super().__init__()
        self.main_window = main_window  # Referencia a la ventana principal
        
        self.setWindowTitle("Monitoreo en Tiempo Real")
        self.setGeometry(200, 200, 800, 500)
        
        # Conexión a la base de datos
        self.db = db

        
        self.initUI()
        self.load_real_time_data()
    
    def initUI(self):
        # Layout principal
        layout = QVBoxLayout()
        
        # Crear encabezado con botón del menú lateral y título
        header_layout = QHBoxLayout()

        label = QLabel("Monitoreo en Tiempo Real")
        
        # Alineación de los widgets
        header_layout.addWidget(label)

        # Ajuste de márgenes para el encabezado
        header_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes alrededor
        header_layout.setSpacing(20)  # Eliminar espacio entre los widgets

        # Agregar el encabezado al layout
        layout.addLayout(header_layout)

        # Crear tabla de trenes
        label_estado = QLabel("Estado Actual de los Trenes")
        layout.addWidget(label_estado)
        
        self.tabla_trenes = QTableWidget()
        self.tabla_trenes.setColumnCount(5)
        self.tabla_trenes.setHorizontalHeaderLabels(["ID Tren", "Nombre", "Estado", "Ruta", "Horario"])
        self.tabla_trenes.setWordWrap(True)
        layout.addWidget(self.tabla_trenes)
        
        # Sección de botones
        button_layout = QHBoxLayout()
        self.btn_refrescar = QPushButton("Actualizar")
        self.btn_detalles = QPushButton("Ver Detalles")
        self.btn_emergencia = QPushButton("Reporte de Emergencia")
        
        button_layout.addWidget(self.btn_refrescar)
        button_layout.addWidget(self.btn_detalles)
        button_layout.addWidget(self.btn_emergencia)
        
        layout.addLayout(button_layout)

        # Botón para volver al menú
        btn_volver = QPushButton("Volver al Menú")
        layout.addWidget(btn_volver)
        #self.btn_volver.clicked.connect(lambda: self.main_window.change_interface("0"))  # Cambiar a la interfaz del menú principal

        self.setLayout(layout)

        # Conectar botón de actualización
        self.btn_refrescar.clicked.connect(self.load_real_time_data)

        # Nuevo: Contenedor de barra de progreso y detalles
        self.detalle_layout = QVBoxLayout()
        layout.addLayout(self.detalle_layout)

        # Conectar selección de tabla
        self.tabla_trenes.cellClicked.connect(self.on_row_selected)

        # Timer de actualización en tiempo real
        self.timer_progreso = QTimer()
        self.timer_progreso.timeout.connect(self.actualizar_barra_tiempo_real)

    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de MonitoreoInterface")
        self.load_real_time_data()

    def load_real_time_data(self):
        """Carga el estado actual de los trenes en servicio"""
        query_trains = """
            SELECT T.ID_TREN, T.NOMBRE, T.ESTADO, 
                   R.ID_RUTA, 
                   TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS')
            FROM TREN T
            LEFT JOIN ASIGNACION_TREN A ON T.ID_TREN = A.ID_TREN
            LEFT JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            LEFT JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
        """
        trains = self.db.fetch_all(query_trains)
        
        self.tabla_trenes.setRowCount(len(trains))
        for i, train in enumerate(trains):
            self.tabla_trenes.setItem(i, 0, QTableWidgetItem(str(train[0])))  # ID Tren
            self.tabla_trenes.setItem(i, 1, QTableWidgetItem(train[1]))  # Nombre
            self.tabla_trenes.setItem(i, 2, QTableWidgetItem(train[2]))  # Estado
            self.tabla_trenes.setItem(i, 3, QTableWidgetItem(str(train[3]) if train[3] else "Sin Ruta"))  # ID Ruta
            self.tabla_trenes.setItem(i, 4, QTableWidgetItem(train[4] if train[4] else "Sin Horario"))  # Hora de salida

        # Ajustar tamaño de columnas y filas
        self.tabla_trenes.resizeColumnsToContents()
        self.tabla_trenes.resizeRowsToContents()

    def on_row_selected(self, row, column):
        id_tren = self.tabla_trenes.item(row, 0).text()
        id_ruta = self.tabla_trenes.item(row, 3).text()
        hora_programada = self.tabla_trenes.item(row, 4).text()

        if id_ruta == "Sin Ruta" or hora_programada == "Sin Horario":
            return

        self.id_tren_seleccionado = id_tren
        self.id_ruta_seleccionada = id_ruta

        self.refrescar_detalles_tren(id_tren, id_ruta)
        self.timer_progreso.start(1000)

    def refrescar_detalles_tren(self, id_tren, id_ruta):
        # Limpiar anterior
        while self.detalle_layout.count():
            item = self.detalle_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                inner_layout = item.layout()
                while inner_layout.count():
                    inner_item = inner_layout.takeAt(0)
                    if inner_item.widget():
                        inner_item.widget().deleteLater()
                self.detalle_layout.removeItem(inner_layout)

        # Obtener datos del tren
        tren = self.db.fetch_one(
            "SELECT NOMBRE, CAPACIDAD, ESTADO FROM TREN WHERE ID_TREN = :id",
            {'id': id_tren}
        )

        ruta = self.db.fetch_one("""
            SELECT 
                E1.NOMBRE AS ESTACION_ORIGEN,
                E2.NOMBRE AS ESTACION_DESTINO,
                R.DURACION_ESTIMADA
            FROM RUTA R
            JOIN RUTA_DETALLE RD1 ON R.ID_RUTA = RD1.ID_RUTA AND RD1.ORDEN = (
                SELECT MIN(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = R.ID_RUTA
            )
            JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
            JOIN RUTA_DETALLE RD2 ON R.ID_RUTA = RD2.ID_RUTA AND RD2.ORDEN = (
                SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = R.ID_RUTA
            )
            JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
            WHERE R.ID_RUTA = :r
        """, {'r': id_ruta})

        if not tren or not ruta:
            return

        self.duracion_estimada = ruta[2]

        # Barra de progreso visual
        barra_layout = QVBoxLayout()
        barra_superior = QHBoxLayout()

        label_inicio = QLabel(ruta[0])
        label_inicio.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_fin = QLabel(ruta[1])
        label_fin.setAlignment(Qt.AlignmentFlag.AlignRight)

        barra_superior.addWidget(label_inicio)
        barra_superior.addStretch()
        barra_superior.addWidget(label_fin)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% completado")
        self.progress_bar.setValue(0)  # Reinicia la barra al seleccionar un nuevo tren

        barra_layout.addLayout(barra_superior)
        barra_layout.addWidget(self.progress_bar)
        self.detalle_layout.addLayout(barra_layout)

        # Detalles divididos en dos columnas
        columnas_layout = QHBoxLayout()

        # Columna izquierda
        col_izq = QVBoxLayout()
        col_izq.addWidget(QLabel(f"ID Tren: {self.id_tren_seleccionado}"))
        col_izq.addWidget(QLabel(f"Nombre: {tren[0]}"))
        col_izq.addWidget(QLabel(f"Capacidad: {tren[1]} pax"))
        col_izq.addWidget(QLabel(f"Estado: {tren[2]}"))
        col_izq.addWidget(QLabel(f"Duración Estimada: {ruta[2]} min"))

        # Columna derecha
        col_der = QVBoxLayout()
        col_der.addWidget(QLabel("Ruta: Desconocida"))

        datos_horario = self.db.fetch_one("""
            SELECT A.ID_HORARIO, TO_CHAR(H.HORA_SALIDA_PROGRAMADA,'HH24:MI:SS'),
                   TO_CHAR(H.HORA_LLEGADA_PROGRAMADA,'HH24:MI:SS')
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            WHERE A.ID_TREN = :id_tren AND A.ID_RUTA = :id_ruta
        """, {'id_tren': self.id_tren_seleccionado, 'id_ruta': self.id_ruta_seleccionada})

        if datos_horario:
            col_der.addWidget(QLabel(f"ID Horario: {datos_horario[0]}"))
            col_der.addWidget(QLabel(f"Salida - Llegada: {datos_horario[1]} - {datos_horario[2]}"))
            self.hora_salida = datos_horario[1]
            self.hora_llegada = datos_horario[2]

        columnas_layout.addLayout(col_izq)
        columnas_layout.addLayout(col_der)
        self.detalle_layout.addLayout(columnas_layout)

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
        except Exception as e:
            print("Error actualizando barra:", e)
            self.progress_bar.setValue(0)
