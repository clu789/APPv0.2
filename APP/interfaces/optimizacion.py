from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection

class OptimizacionDinamica(QWidget):
    def __init__(self, main_window,db):
        super().__init__()
        self.main_window = main_window  # Ventana principal
        self.setWindowTitle("Optimización Dinámica")
        self.setGeometry(100, 100, 1000, 600)

        self.db = db  # Usar la conexión existente


        self.initUI()
        self.load_delays()
        self.load_train_suggestions()

    def initUI(self):
        layout = QVBoxLayout()

        # Encabezado con título y botón de menú
        header_layout = QHBoxLayout()

        label = QLabel("Optimización Dinámica")
        header_layout.addWidget(label)
        layout.addLayout(header_layout)

        # Tabla para mostrar los retrasos detectados
        self.tabla_retrasos = QTableWidget()
        self.tabla_retrasos.setColumnCount(3)
        self.tabla_retrasos.setHorizontalHeaderLabels(["ID Horario", "Retraso (min)", "Tren Asignado"])
        layout.addWidget(self.tabla_retrasos)

        # Tabla para sugerencias de reajuste de horarios
        self.tabla_sugerencias = QTableWidget()
        self.tabla_sugerencias.setColumnCount(4)
        self.tabla_sugerencias.setHorizontalHeaderLabels(["ID Horario", "Nuevo Horario", "Tren Propuesto", "Acción"])
        layout.addWidget(self.tabla_sugerencias)

        # Botones de acción
        button_layout = QHBoxLayout()
        self.btn_aceptar_cambio = QPushButton("Aceptar Cambios")
        self.btn_rechazar_cambio = QPushButton("Rechazar Cambios")
        button_layout.addWidget(self.btn_aceptar_cambio)
        button_layout.addWidget(self.btn_rechazar_cambio)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        #Recargar los datos de la interfaz
  
    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de incidencias...")
        self.load_delays()
        self.load_train_suggestions()

    def load_delays(self):
        """Carga los retrasos detectados comparando horarios programados y reales"""
        query = """
            SELECT H.ID_HORARIO, 
                   ROUND((H.HORA_SALIDA_REAL - H.HORA_SALIDA_PROGRAMADA) * 1440) AS RETRASO, 
                   T.NOMBRE
            FROM HORARIO H
            LEFT JOIN ASIGNACION_TREN A ON H.ID_HORARIO = A.ID_HORARIO
            LEFT JOIN TREN T ON A.ID_TREN = T.ID_TREN
            WHERE H.HORA_SALIDA_REAL IS NOT NULL
            ORDER BY RETRASO DESC
        """
        delays = self.db.fetch_all(query)

        self.tabla_retrasos.setRowCount(len(delays))
        for i, delay in enumerate(delays):
            self.tabla_retrasos.setItem(i, 0, QTableWidgetItem(str(delay[0])))
            self.tabla_retrasos.setItem(i, 1, QTableWidgetItem(str(delay[1])))
            self.tabla_retrasos.setItem(i, 2, QTableWidgetItem(delay[2] if delay[2] else "No asignado"))

    def load_train_suggestions(self):
        """Carga sugerencias de reajuste basadas en la disponibilidad de trenes"""
        query = """
            SELECT H.ID_HORARIO, 
                   TO_CHAR(H.HORA_SALIDA_PROGRAMADA + INTERVAL '30' MINUTE, 'HH24:MI:SS') AS NUEVO_HORARIO, 
                   T.NOMBRE,
                   'Reprogramar' AS ACCION
            FROM HORARIO H
            LEFT JOIN ASIGNACION_TREN A ON H.ID_HORARIO = A.ID_HORARIO
            LEFT JOIN TREN T ON A.ID_TREN = T.ID_TREN
            WHERE T.ESTADO = 'ACTIVO'
        """
        suggestions = self.db.fetch_all(query)

        self.tabla_sugerencias.setRowCount(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            self.tabla_sugerencias.setItem(i, 0, QTableWidgetItem(str(suggestion[0])))
            self.tabla_sugerencias.setItem(i, 1, QTableWidgetItem(suggestion[1]))
            self.tabla_sugerencias.setItem(i, 2, QTableWidgetItem(suggestion[2]))
            self.tabla_sugerencias.setItem(i, 3, QTableWidgetItem(suggestion[3]))