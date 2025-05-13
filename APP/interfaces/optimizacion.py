from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection

class OptimizacionDinamica(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db

        self.setWindowTitle("Optimización Dinámica")
        self.setGeometry(100, 100, 1100, 600)
        self.initUI()
        self.cargar_datos()

    def initUI(self):
        layout = QVBoxLayout()

        # Título
        header = QLabel("Optimización Dinámica")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Tabla unificada
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(10)
        self.tabla.setHorizontalHeaderLabels([
            "ID Horario", "ID Tren", "Fecha Incidencia", "Tipo Incidencia",
            "Descripción", "Acción", "Horario Original", "Nuevo Horario", "Tren Asignado",
            "Tren Sugerido"
        ])
        layout.addWidget(self.tabla)

        # Botones
        botones = QHBoxLayout()
        self.btn_confirmar_uno = QPushButton("Confirmar Cambio Seleccionado")
        self.btn_confirmar_varios = QPushButton("Confirmar Cambios Seleccionados")
        self.btn_editar_cambio = QPushButton("Editar Cambio")
        botones.addWidget(self.btn_confirmar_uno)
        botones.addWidget(self.btn_confirmar_varios)
        botones.addWidget(self.btn_editar_cambio)
        layout.addLayout(botones)

        self.setLayout(layout)

        # Conexiones
        self.btn_confirmar_uno.clicked.connect(self.confirmar_uno)
        self.btn_confirmar_varios.clicked.connect(self.confirmar_varios)
        self.btn_editar_cambio.clicked.connect(self.editar_cambio)

    def calcular_nuevo_horario(self, id_horario):
        query = """
            SELECT HORA_SALIDA_PROGRAMADA + INTERVAL '30' MINUTE
            FROM HORARIO
            WHERE ID_HORARIO = :1
        """
        resultado = self.db.fetch_one(query, [id_horario])
        if resultado:
            return resultado[0].strftime('%H:%M:%S')
        return "N/A"

    # Función para obtener horario original (salida y llegada)
    def obtener_horario_original(self, id_horario):
        query = """
            SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI'), TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI')
            FROM HORARIO
            WHERE ID_HORARIO = :1
        """
        resultado = self.db.fetch_one(query, [id_horario])
        if resultado:
            return f"{resultado[0]} - {resultado[1]}"
        return "N/A"

    # Función para buscar tren disponible para reasignación
    def buscar_tren_disponible(self, id_horario):
        query_horario = """
            SELECT HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA
            FROM HORARIO
            WHERE ID_HORARIO = :1
        """
        salida_llegada = self.db.fetch_one(query_horario, [id_horario])
        if not salida_llegada:
            return None

        hora_salida, hora_llegada = salida_llegada

        # Buscar trenes que no estén asignados durante ese rango
        query = """
            SELECT T.ID_TREN, T.NOMBRE
            FROM TREN T
            WHERE T.ID_TREN NOT IN (
                SELECT A.ID_TREN
                FROM ASIGNACION_TREN A
                JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                WHERE (
                    (H.HORA_SALIDA_PROGRAMADA <= :2 AND H.HORA_LLEGADA_PROGRAMADA >= :1)
                )
            )
            FETCH FIRST 1 ROWS ONLY
        """
        resultado = self.db.fetch_one(query, [hora_salida, hora_llegada])
        return resultado[1] if resultado else "Ninguno disponible"

    def cargar_datos(self):
        self.tabla.setRowCount(0)

        # 1. Obtener incidencias no resueltas
        query_incidencias = """
            SELECT ID_INCIDENCIA, ID_ASIGNACION, TIPO, FECHA_HORA, DESCRIPCION
            FROM INCIDENCIA
            WHERE ESTADO = 'NO RESUELTO'
        """
        incidencias = self.db.fetch_all(query_incidencias)

        if not incidencias:
            return

        id_asignaciones = [str(row[1]) for row in incidencias]  # ID_ASIGNACION
        placeholders = ','.join([':{}'.format(i + 1) for i in range(len(id_asignaciones))])

        # 2. Obtener información de cada asignación (ID_HORARIO, ID_TREN, ID_RUTA)
        query_asignaciones = f"""
            SELECT ID_ASIGNACION, ID_HORARIO, ID_TREN, ID_RUTA
            FROM ASIGNACION_TREN
            WHERE ID_ASIGNACION IN ({placeholders})
        """
        asignaciones = self.db.fetch_all(query_asignaciones, id_asignaciones)

        mapa_asignaciones = {a[0]: a for a in asignaciones}

        # 3. Obtener info completa de asignaciones futuras con mismos ID_HORARIO e ID_RUTA
        filas_resultantes = []
        for inc in incidencias:
            id_inc, id_asig, tipo, fecha_incidencia, descripcion = inc
            if id_asig not in mapa_asignaciones:
                continue
            
            id_horario, id_tren, id_ruta = mapa_asignaciones[id_asig][1:]
        
            if tipo == 'RETRASO':
                # Buscar asignaciones futuras con la misma ruta
                query_afectadas = """
                    SELECT A.ID_HORARIO, A.ID_TREN, T.NOMBRE
                    FROM ASIGNACION_TREN A
                    LEFT JOIN TREN T ON A.ID_TREN = T.ID_TREN
                    WHERE A.ID_HORARIO > :1 AND A.ID_RUTA = :2
                """
                afectadas = self.db.fetch_all(query_afectadas, [id_horario, id_ruta])
        
            elif tipo == 'AVERIA':
                # Buscar otras asignaciones del mismo tren
                query_afectadas = """
                    SELECT A.ID_HORARIO, A.ID_TREN, T.NOMBRE
                    FROM ASIGNACION_TREN A
                    LEFT JOIN TREN T ON A.ID_TREN = T.ID_TREN
                    WHERE A.ID_TREN = :1 AND A.ID_HORARIO > :2
                """
                afectadas = self.db.fetch_all(query_afectadas, [id_tren, id_horario])
        
            elif tipo == 'EMERGENCIA':
                # Misma lógica que AVERIA
                query_afectadas = """
                    SELECT A.ID_HORARIO, A.ID_TREN, T.NOMBRE
                    FROM ASIGNACION_TREN A
                    LEFT JOIN TREN T ON A.ID_TREN = T.ID_TREN
                    WHERE A.ID_TREN = :1 AND A.ID_HORARIO > :2
                """
                afectadas = self.db.fetch_all(query_afectadas, [id_tren, id_horario])
            
            else:
                afectadas = []
        
            for af in afectadas:
                id_hor, id_tren_af, nombre_tren = af
                horario_original = self.obtener_horario_original(id_hor)
        
                # Acción sugerida según tipo
                if tipo == 'RETRASO':
                    accion = 'REPROGRAMAR'
                    nuevo_horario = self.calcular_nuevo_horario(id_hor)
                    tren_sugerido = ""
                elif tipo == 'AVERIA':
                    accion = 'REASIGNAR TREN'
                    nuevo_horario = ""
                    tren_sugerido = self.buscar_tren_disponible(id_hor)
                elif tipo == 'EMERGENCIA':
                    tren_sugerido = self.buscar_tren_disponible(id_hor)
                    if tren_sugerido != "Ninguno disponible":
                        accion = 'REASIGNAR TREN'
                        nuevo_horario = ""
                    else:
                        accion = 'CANCELAR VIAJE'
                        nuevo_horario = 'N/A'
                else:
                    accion = 'SIN ACCIÓN'
                    nuevo_horario = 'N/A'
                    tren_sugerido = ""
        
                filas_resultantes.append((
                    id_hor,
                    id_tren_af,
                    fecha_incidencia.strftime('%d-%m-%Y %H:%M'),
                    tipo,
                    descripcion,
                    accion,
                    horario_original,
                    nuevo_horario,
                    nombre_tren,
                    tren_sugerido
                ))

        self.tabla.setRowCount(len(filas_resultantes))
        for fila_idx, fila_datos in enumerate(filas_resultantes):
            for col_idx, dato in enumerate(fila_datos):
                self.tabla.setItem(fila_idx, col_idx, QTableWidgetItem(str(dato)))
        
        self.tabla.resizeColumnsToContents()
        self.tabla.resizeRowsToContents()

    def actualizar_datos(self):
        self.cargar_datos()

    def confirmar_uno(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona una fila para confirmar.")
            return
        id_horario = int(self.tabla.item(fila, 0).text())
        self.db.execute("UPDATE INCIDENCIA SET ESTADO = 'RESUELTA' WHERE ID_HORARIO = :1", [id_horario])
        QMessageBox.information(self, "Éxito", f"Cambio para horario {id_horario} confirmado.")
        self.cargar_datos()

    def confirmar_varios(self):
        filas = set(index.row() for index in self.tabla.selectedIndexes())
        if not filas:
            QMessageBox.warning(self, "Advertencia", "Selecciona al menos una fila.")
            return

        for fila in filas:
            id_horario = int(self.tabla.item(fila, 0).text())
            self.db.execute("UPDATE INCIDENCIA SET ESTADO = 'RESUELTA' WHERE ID_HORARIO = :1", [id_horario])

        QMessageBox.information(self, "Éxito", "Cambios confirmados para las filas seleccionadas.")
        self.cargar_datos()

    def editar_cambio(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona una fila para editar.")
            return

        id_horario = int(self.tabla.item(fila, 0).text())
        QMessageBox.information(self, "Función pendiente", f"Aquí podrías abrir una subinterfaz para editar la sugerencia del horario {id_horario}.")
        # Aquí se puede abrir una ventana adicional con campos para cambiar tren o reprogramar horario
