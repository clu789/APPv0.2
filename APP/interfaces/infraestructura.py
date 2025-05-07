from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection

class GestionInfraestructura(QWidget):
    def __init__(self, main_window,db):
        super().__init__()
        self.main_window = main_window  # Referencia a MainWindow
        self.setWindowTitle("Gestión de Infraestructura")
        self.setGeometry(200, 200, 900, 500)

        # Conexión a la base de datos
        self.db = db  # Usar la conexión existente


        # Layout principal
        self.layout = QVBoxLayout()

        # Encabezado con el botón de menú y título
        header_layout = QHBoxLayout()

        label = QLabel("Gestión de Infraestructura")
        
        # Alineación de los widgets
        header_layout.addWidget(label)
        header_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes alrededor
        header_layout.setSpacing(20)  # Eliminar espacio entre los widgets
        self.layout.addLayout(header_layout)

        # Sección para botones de gestión
        self.btn_trenes = QPushButton("Administrar Trenes")
        self.btn_estaciones = QPushButton("Administrar Estaciones")
        self.layout.addWidget(self.btn_trenes)
        self.layout.addWidget(self.btn_estaciones)

        # Crear y cargar tablas
        self.create_trenes_table()
        self.create_estaciones_table()

        # Botón para volver al menú principal
        self.btn_volver = QPushButton("Volver al Menú")
        #self.btn_volver.clicked.connect(self.main_window.volver_al_menu)  # Función de volver al menú
        self.layout.addWidget(self.btn_volver)

        self.setLayout(self.layout)

        # Cargar los datos de trenes y estaciones
        self.load_trenes_data()
        self.load_estaciones_data()

        #Recargar los datos de la interfaz
    
    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de GestionInfraestructura")
        self.load_trenes_data()
        self.load_estaciones_data()

    def create_trenes_table(self):
        """Crea la tabla de trenes"""
        self.trenes_table = QTableWidget()
        self.trenes_table.setColumnCount(4)
        self.trenes_table.setHorizontalHeaderLabels(["ID Tren", "Nombre", "Capacidad", "Estado"])
        self.trenes_table.setWordWrap(True)
        self.layout.addWidget(self.trenes_table)

    def create_estaciones_table(self):
        """Crea la tabla de estaciones"""
        self.estaciones_table = QTableWidget()
        self.estaciones_table.setColumnCount(2)
        self.estaciones_table.setHorizontalHeaderLabels(["ID Estación", "Nombre Estación"])
        self.estaciones_table.setWordWrap(True)
        self.layout.addWidget(self.estaciones_table)

    def load_trenes_data(self):
        """Carga los trenes desde la base de datos"""
        query_trenes = """
            SELECT ID_TREN, NOMBRE, CAPACIDAD, ESTADO
            FROM TREN
        """
        trenes = self.db.fetch_all(query_trenes)
        
        self.trenes_table.setRowCount(len(trenes))
        for i, tren in enumerate(trenes):
            self.trenes_table.setItem(i, 0, QTableWidgetItem(str(tren[0])))  # ID Tren
            self.trenes_table.setItem(i, 1, QTableWidgetItem(tren[1]))  # Nombre
            self.trenes_table.setItem(i, 2, QTableWidgetItem(str(tren[2])))  # Capacidad
            self.trenes_table.setItem(i, 3, QTableWidgetItem(tren[3]))  # Estado

        # Ajustar el tamaño de las columnas
        self.trenes_table.resizeColumnsToContents()

    def load_estaciones_data(self):
        """Carga las estaciones desde la base de datos"""
        query_estaciones = """
            SELECT ID_ESTACION, NOMBRE
            FROM ESTACION
        """
        estaciones = self.db.fetch_all(query_estaciones)
        
        self.estaciones_table.setRowCount(len(estaciones))
        for i, estacion in enumerate(estaciones):
            self.estaciones_table.setItem(i, 0, QTableWidgetItem(str(estacion[0])))  # ID Estación
            self.estaciones_table.setItem(i, 1, QTableWidgetItem(estacion[1]))  # Nombre Estación

        # Ajustar el tamaño de las columnas
        self.estaciones_table.resizeColumnsToContents()
