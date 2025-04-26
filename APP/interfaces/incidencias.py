from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection

class GestionIncidencias(QWidget):
    def __init__(self, main_window,db):
        super().__init__()
        self.main_window = main_window  # Referencia al menú principal
        self.db = db  # Usar la conexión existente

        self.setWindowTitle("Gestión de Incidencias")
        self.setGeometry(200, 200, 900, 500)

        self.initUI()
        self.load_incidencias()

    def initUI(self):
        # Layout principal
        layout = QVBoxLayout()

        # Crear encabezado con el título
        header_layout = QHBoxLayout()

        label = QLabel("Gestión de Incidencias")

        # Alineación del widget
        header_layout.addWidget(label)

        # Ajuste de márgenes para el encabezado
        header_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes alrededor
        header_layout.setSpacing(20)  # Eliminar espacio entre los widgets

        # Agregar el encabezado al layout
        layout.addLayout(header_layout)

        # Crear tabla de incidencias
        label_estado = QLabel("Incidencias Registradas")
        layout.addWidget(label_estado)

        self.tabla_incidencias = QTableWidget()
        self.tabla_incidencias.setColumnCount(5)
        self.tabla_incidencias.setHorizontalHeaderLabels(["ID Incidencia", "ID Horario", "Tipo", "Descripción", "Fecha y Hora"])
        self.tabla_incidencias.setWordWrap(True)
        layout.addWidget(self.tabla_incidencias)

        # Sección de botones
        button_layout = QHBoxLayout()
        self.btn_actualizar = QPushButton("Actualizar")
        self.btn_registrar = QPushButton("Registrar Incidencia")

        button_layout.addWidget(self.btn_actualizar)
        button_layout.addWidget(self.btn_registrar)

        layout.addLayout(button_layout)

        # Botón para volver al menú
        btn_volver = QPushButton("Volver al Menú")
        layout.addWidget(btn_volver)

        self.setLayout(layout)

        # Conectar botón de actualización
        self.btn_actualizar.clicked.connect(self.load_incidencias)

    def load_incidencias(self):
        """Carga las incidencias desde la base de datos"""
        query = """
            SELECT ID_INCIDENCIA, ID_HORARIO, TIPO, DESCRIPCION, TO_CHAR(FECHA_HORA, 'YYYY-MM-DD HH24:MI:SS')
            FROM INCIDENCIA
        """
        incidencias = self.db.fetch_all(query)

        self.tabla_incidencias.setRowCount(len(incidencias))
        for i, incidencia in enumerate(incidencias):
            self.tabla_incidencias.setItem(i, 0, QTableWidgetItem(str(incidencia[0])))  # ID Incidencia
            self.tabla_incidencias.setItem(i, 1, QTableWidgetItem(str(incidencia[1])))  # ID Horario
            self.tabla_incidencias.setItem(i, 2, QTableWidgetItem(incidencia[2]))  # Tipo
            self.tabla_incidencias.setItem(i, 3, QTableWidgetItem(incidencia[3]))  # Descripción
            self.tabla_incidencias.setItem(i, 4, QTableWidgetItem(incidencia[4]))  # Fecha y Hora

        # Ajustar tamaño de columnas y filas
        self.tabla_incidencias.resizeColumnsToContents()
        self.tabla_incidencias.resizeRowsToContents()