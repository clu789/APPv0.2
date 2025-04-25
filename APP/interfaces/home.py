from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                             QScrollArea, QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QIcon
from base_de_datos.db import DatabaseConnection


class InterfazHome(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Panel de Control - Home")
        self.setGeometry(100, 100, 1200, 700)

        self.db = DatabaseConnection("PROYECTO_IS", "123", "localhost", 1521, "XE")
        self.db.connect()

        self.initUI()
        self.cargar_datos_viajes()
        self.cargar_datos_proximos()

    def initUI(self):
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        self.btn_menu = QPushButton("☰")
        self.btn_menu.setFixedSize(40, 40)
        self.btn_menu.clicked.connect(self.main_window.toggle_menu)
        top_layout.addWidget(self.btn_menu)

        self.btn_correo = QPushButton()
        self.btn_correo.setIcon(QIcon("iconos/correo.png"))
        self.btn_correo.setFixedSize(40, 40)
        top_layout.addWidget(self.btn_correo)

        self.label_reloj = QLabel()
        self.label_reloj.setStyleSheet("font-size: 18px;")
        self.actualizar_reloj()
        timer = QTimer(self)
        timer.timeout.connect(self.actualizar_reloj)
        timer.start(1000)
        top_layout.addWidget(self.label_reloj)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # VIAJES EN CURSO
        layout.addWidget(QLabel("Viajes en curso"))
        self.tabla_viajes = QTableWidget()
        self.tabla_viajes.setColumnCount(10)
        self.tabla_viajes.setHorizontalHeaderLabels([
            "Código Horario", "Salida Programada", "Llegada Programada",
            "Salida Real", "Llegada Real", "Duración", "Origen", "Destino",
            "Nombre del Tren", "Tipo de Incidencia"
        ])
        layout.addWidget(self.crear_scroll_para_tabla(self.tabla_viajes))

        # PROXIMAMENTE
        layout.addWidget(QLabel("Próximamente"))
        self.tabla_proximos = QTableWidget()
        self.tabla_proximos.setColumnCount(8)
        self.tabla_proximos.setHorizontalHeaderLabels([
            "Código Horario", "Salida Programada", "Llegada Programada",
            "Duración", "Origen", "Destino", "Nombre del Tren", "Estado del Tren"
        ])
        layout.addWidget(self.crear_scroll_para_tabla(self.tabla_proximos))

        botones_layout = QHBoxLayout()
        botones_layout.addStretch()
        self.btn_modificar = QPushButton("Modificar")
        self.btn_modificar.clicked.connect(self.accion_modificar)
        self.btn_asignar = QPushButton("Asignar")
        self.btn_asignar.clicked.connect(self.accion_asignar)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.accion_cancelar)
        botones_layout.addWidget(self.btn_modificar)
        botones_layout.addWidget(self.btn_asignar)
        botones_layout.addWidget(self.btn_cancelar)
        layout.addLayout(botones_layout)

        self.setLayout(layout)

    def crear_scroll_para_tabla(self, tabla):
        tabla.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        scroll_frame = QFrame()
        scroll_layout = QVBoxLayout(scroll_frame)
        scroll_layout.addWidget(tabla)
        return scroll_frame

    def actualizar_reloj(self):
        self.label_reloj.setText(QTime.currentTime().toString("HH:mm:ss"))

    def cargar_datos_viajes(self):
        query = """
            SELECT H.ID_HORARIO, 
                   TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 
                   TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 
                   TO_CHAR(H.HORA_SALIDA_REAL, 'HH24:MI:SS'), 
                   TO_CHAR(H.HORA_LLEGADA_REAL, 'HH24:MI:SS'),
                   R.DURACION_ESTIMADA,
                   E1.NOMBRE AS ORIGEN,
                   E2.NOMBRE AS DESTINO,
                   T.NOMBRE AS NOMBRE_TREN,
                   I.TIPO AS TIPO_INCIDENCIA
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            LEFT JOIN INCIDENCIA I ON I.ID_HORARIO = H.ID_HORARIO
            JOIN RUTA_DETALLE RD1 ON RD1.ID_RUTA = A.ID_RUTA AND RD1.ORDEN = 1
            JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
            JOIN RUTA_DETALLE RD2 ON RD2.ID_RUTA = A.ID_RUTA
            JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
            WHERE RD2.ORDEN = (SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = A.ID_RUTA)
              AND H.HORA_SALIDA_PROGRAMADA <= SYSDATE
        """
        viajes = self.db.fetch_all(query)
        if viajes:
            self.tabla_viajes.setRowCount(len(viajes))
            for i, v in enumerate(viajes):
                for j, dato in enumerate(v):
                    self.tabla_viajes.setItem(i, j, QTableWidgetItem(str(dato)))

    def cargar_datos_proximos(self):
        query = """
            SELECT H.ID_HORARIO, 
                   TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), 
                   TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), 
                   R.DURACION_ESTIMADA,
                   E1.NOMBRE AS ORIGEN,
                   E2.NOMBRE AS DESTINO,
                   T.NOMBRE AS NOMBRE_TREN,
                   T.ESTADO
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            JOIN RUTA_DETALLE RD1 ON RD1.ID_RUTA = A.ID_RUTA AND RD1.ORDEN = 1
            JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
            JOIN RUTA_DETALLE RD2 ON RD2.ID_RUTA = A.ID_RUTA
            JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
            WHERE RD2.ORDEN = (SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = A.ID_RUTA)
              AND H.HORA_SALIDA_PROGRAMADA > SYSDATE
        """
        proximos = self.db.fetch_all(query)
        if proximos:
            self.tabla_proximos.setRowCount(len(proximos))
            for i, p in enumerate(proximos):
                for j, dato in enumerate(p):
                    self.tabla_proximos.setItem(i, j, QTableWidgetItem(str(dato)))

    def accion_modificar(self):
        print("Modificar registro...")

    def accion_asignar(self):
        print("Asignar tren...")

    def accion_cancelar(self):
        fila = self.tabla_viajes.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Atención", "Selecciona un registro para cancelar.")
            return
        confirmar = QMessageBox.question(self, "Cancelar", "¿Estás seguro de eliminar este registro?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmar == QMessageBox.StandardButton.Yes:
            cod = self.tabla_viajes.item(fila, 0).text()
            QMessageBox.information(self, "Eliminar", f"(Simulado) Eliminando el horario {cod}.")
