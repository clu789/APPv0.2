from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection  

class MonitoreoInterface(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Referencia a la ventana principal
        
        self.setWindowTitle("Monitoreo en Tiempo Real")
        self.setGeometry(200, 200, 800, 500)
        
        self.db = DatabaseConnection("PROYECTO_IS", "123", "localhost", 1521, "XE")
        self.db.connect()
        
        self.initUI()
        self.load_real_time_data()
    
    def initUI(self):
        # Layout principal
        layout = QVBoxLayout()
        
        # Crear encabezado con botón del menú lateral y título
        header_layout = QHBoxLayout()
        self.btn_menu = QPushButton("☰")  # Botón de tres rayas
        self.btn_menu.setFixedSize(40, 40)  # Tamaño del botón
        self.btn_menu.clicked.connect(self.main_window.toggle_menu)  # Función para abrir/cerrar el menú

        label = QLabel("Monitoreo en Tiempo Real")
        
        # Alineación de los widgets
        header_layout.addWidget(self.btn_menu)
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
