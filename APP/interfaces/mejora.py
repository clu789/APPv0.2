from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection

class MejoraContinua(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db

        self.setWindowTitle("Análisis y Mejora Continua")
        self.setGeometry(100, 100, 1200, 600)
        self.initUI()
        self.cargar_datos()

    def initUI(self):
        layout = QVBoxLayout()

        # Título
        header = QLabel("Historial del Sistema")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Tabla: Historial de Horarios
        self.tabla_horarios = QTableWidget()
        self.tabla_horarios.setColumnCount(3)
        self.tabla_horarios.setHorizontalHeaderLabels(["ID Horario", "Información", "Fecha Registro"])
        layout.addWidget(QLabel("Historial de Horarios:"))
        layout.addWidget(self.tabla_horarios)

        # Tabla: Historial de Rutas
        self.tabla_rutas = QTableWidget()
        self.tabla_rutas.setColumnCount(3)
        self.tabla_rutas.setHorizontalHeaderLabels(["ID Ruta", "Información", "Fecha Registro"])
        layout.addWidget(QLabel("Historial de Rutas:"))
        layout.addWidget(self.tabla_rutas)

        # Tabla: Historial de Asignaciones
        self.tabla_asignaciones = QTableWidget()
        self.tabla_asignaciones.setColumnCount(3)
        self.tabla_asignaciones.setHorizontalHeaderLabels(["ID Asignación", "Información", "Fecha Registro"])
        layout.addWidget(QLabel("Historial de Asignaciones:"))
        layout.addWidget(self.tabla_asignaciones)

        # Botón para actualizar
        btn_actualizar = QPushButton("Actualizar Datos")
        btn_actualizar.clicked.connect(self.cargar_datos)
        layout.addWidget(btn_actualizar)

        self.setLayout(layout)

    def cargar_datos(self):
        self.cargar_historial_horarios()
        self.cargar_historial_rutas()
        self.cargar_historial_asignaciones()

    def actualizar_datos(self):
        self.cargar_datos()
        
    def cargar_historial_horarios(self):
        query = """
            SELECT ID_HORARIO, INFORMACION, FECHA_REGISTRO
            FROM HISTORIAL
            WHERE ID_HORARIO IS NOT NULL
        """
        historial = self.db.fetch_all(query)
        self.tabla_horarios.setRowCount(0)
    
        fila = 0
        horarios_mostrados = set()
    
        for id_horario, info_hist, fecha in historial:
            # Convertir CLOB si es necesario
            if hasattr(info_hist, 'read'):
                info_hist = info_hist.read()
    
            # Mostrar historial (sin filtrar)
            self.tabla_horarios.insertRow(fila)
            self.tabla_horarios.setItem(fila, 0, QTableWidgetItem(str(id_horario)))
            self.tabla_horarios.setItem(fila, 1, QTableWidgetItem(info_hist))
            self.tabla_horarios.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
            fila += 1
    
            # Mostrar horario actual solo una vez por ID_HORARIO
            if id_horario not in horarios_mostrados:
                horarios_mostrados.add(id_horario)
                query_actual = """
                    SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI') || ' - ' || TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI')
                    FROM HORARIO
                    WHERE ID_HORARIO = :1
                """
                resultado = self.db.fetch_one(query_actual, [id_horario])
                if resultado:
                    self.tabla_horarios.insertRow(fila)
                    self.tabla_horarios.setItem(fila, 0, QTableWidgetItem(str(id_horario)))
                    self.tabla_horarios.setItem(fila, 1, QTableWidgetItem("HORARIO ACTUAL: " + resultado[0]))
                    self.tabla_horarios.setItem(fila, 2, QTableWidgetItem(""))
                    fila += 1
    
        self.tabla_horarios.resizeColumnsToContents()
        self.tabla_horarios.resizeRowsToContents()
        self.tabla_horarios.setSortingEnabled(True)
        self.tabla_horarios.sortItems(0, Qt.SortOrder.AscendingOrder)

    def cargar_historial_rutas(self):
        query = """
            SELECT ID_RUTA, INFORMACION, FECHA_REGISTRO
            FROM HISTORIAL
            WHERE ID_RUTA IS NOT NULL
        """
        historial = self.db.fetch_all(query)
        self.tabla_rutas.setRowCount(0)

        fila = 0
        rutas_mostradas = set()

        for id_ruta, info_hist, fecha in historial:
            # Si info_hist es un LOB, conviértelo
            if hasattr(info_hist, 'read'):
                info_hist = info_hist.read()

            # Mostrar entrada de historial
            self.tabla_rutas.insertRow(fila)
            self.tabla_rutas.setItem(fila, 0, QTableWidgetItem(str(id_ruta)))
            self.tabla_rutas.setItem(fila, 1, QTableWidgetItem(info_hist))
            self.tabla_rutas.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
            fila += 1

            # Mostrar info actual solo una vez por ID_RUTA
            if id_ruta not in rutas_mostradas:
                rutas_mostradas.add(id_ruta)

                query_actual = """
                    SELECT R.DURACION_ESTIMADA,
                           LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                    FROM RUTA R
                    JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
                    JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                    WHERE R.ID_RUTA = :1
                    GROUP BY R.DURACION_ESTIMADA
                """
                resultado = self.db.fetch_one(query_actual, [id_ruta])
                if resultado:
                    duracion, estaciones = resultado
                    info_actual = f"RUTA ACTUAL: Duración: {duracion}; Orden: {estaciones}"

                    self.tabla_rutas.insertRow(fila)
                    self.tabla_rutas.setItem(fila, 0, QTableWidgetItem(str(id_ruta)))
                    self.tabla_rutas.setItem(fila, 1, QTableWidgetItem(info_actual))
                    self.tabla_rutas.setItem(fila, 2, QTableWidgetItem(""))
                    fila += 1

        self.tabla_rutas.resizeColumnsToContents()
        self.tabla_rutas.resizeRowsToContents()
        self.tabla_rutas.setSortingEnabled(True)
        self.tabla_rutas.sortItems(0, Qt.SortOrder.AscendingOrder)

    def cargar_historial_asignaciones(self):
        query = """
            SELECT ID_ASIGNACION, INFORMACION, FECHA_REGISTRO
            FROM HISTORIAL
            WHERE ID_ASIGNACION IS NOT NULL AND ID_INCIDENCIA IS NULL AND HORA_REAL IS NULL
            ORDER BY FECHA_REGISTRO DESC
        """
        historial = self.db.fetch_all(query)
        self.tabla_asignaciones.setRowCount(0)

        fila = 0
        asignaciones_mostradas = set()

        for id_asignacion, info_hist, fecha in historial:
            # Convertir LOB si aplica
            if hasattr(info_hist, 'read'):
                info_hist = info_hist.read()

            # Mostrar registro de historial
            self.tabla_asignaciones.insertRow(fila)
            self.tabla_asignaciones.setItem(fila, 0, QTableWidgetItem(str(id_asignacion)))
            self.tabla_asignaciones.setItem(fila, 1, QTableWidgetItem(info_hist))
            self.tabla_asignaciones.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
            fila += 1

            # Mostrar "asignación actual" solo una vez
            if id_asignacion not in asignaciones_mostradas:
                asignaciones_mostradas.add(id_asignacion)

                # Obtener ID_RUTA, ID_HORARIO, ID_TREN
                query_datos = """
                    SELECT ID_RUTA, ID_HORARIO, ID_TREN
                    FROM ASIGNACION_TREN
                    WHERE ID_ASIGNACION = :1
                """
                resultado = self.db.fetch_one(query_datos, [id_asignacion])
                if not resultado:
                    continue
                id_ruta, id_horario, id_tren = resultado

                # Obtener horario
                horario = self.db.fetch_one("""
                    SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                           TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI')
                    FROM HORARIO WHERE ID_HORARIO = :1
                """, [id_horario])
                hora_inicio, hora_fin = horario if horario else ("?", "?")

                # Obtener ruta
                ruta = self.db.fetch_one("""
                    SELECT R.DURACION_ESTIMADA,
                           LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                    FROM RUTA R
                    JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
                    JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                    WHERE R.ID_RUTA = :1
                    GROUP BY R.DURACION_ESTIMADA
                """, [id_ruta])
                duracion, estaciones = ruta if ruta else ("?", "?")

                # Obtener tren
                tren = self.db.fetch_one("SELECT NOMBRE FROM TREN WHERE ID_TREN = :1", [id_tren])
                nombre_tren = tren[0] if tren else "?"

                # Mostrar información actual
                info = (
                    f"HORARIO ACTUAL: Duración: {duracion}; Orden: {estaciones}; "
                    f"Horario: {hora_inicio} - {hora_fin}; Tren: {nombre_tren}"
                )
                self.tabla_asignaciones.insertRow(fila)
                self.tabla_asignaciones.setItem(fila, 0, QTableWidgetItem(str(id_asignacion)))
                self.tabla_asignaciones.setItem(fila, 1, QTableWidgetItem(info))
                self.tabla_asignaciones.setItem(fila, 2, QTableWidgetItem(""))
                fila += 1

        self.tabla_asignaciones.resizeColumnsToContents()
        self.tabla_asignaciones.resizeRowsToContents()
        self.tabla_asignaciones.setSortingEnabled(True)
        self.tabla_asignaciones.sortItems(0, Qt.SortOrder.AscendingOrder)
