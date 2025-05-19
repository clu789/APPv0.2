from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDateTimeEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime
from datetime import datetime

class InterfazAgregarIncidencia(QWidget):
    def __init__(self, main_window, db, username, confirmar_callback=None):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db
        self.confirmar_callback = confirmar_callback  # Para refrescar la tabla padre si se usa
        self.setWindowTitle("Agregar Incidencia")

        self.fecha_actual = True

        self.initUI()
        self.cargar_asignaciones()

    def initUI(self):
        layout = QVBoxLayout()

        # Tabla de Asignaciones
        self.tabla_asignaciones = QTableWidget()
        self.tabla_asignaciones.setColumnCount(4)
        self.tabla_asignaciones.setHorizontalHeaderLabels(["ID", "Tren", "Ruta", "Horario"])
        layout.addWidget(QLabel("Selecciona la asignación:"))
        layout.addWidget(self.tabla_asignaciones)

        # Tipo de incidencia
        layout.addWidget(QLabel("Tipo de incidencia:"))
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Retraso", "Averia", "Emergencia"])
        layout.addWidget(self.tipo_combo)

        # Descripción
        layout.addWidget(QLabel("Descripción (máx 150 caracteres):"))
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setMaxLength(150)
        layout.addWidget(self.descripcion_input)

        # Estado
        layout.addWidget(QLabel("Estado:"))
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["No resuelto", "Resuelto"])
        self.estado_combo.setCurrentIndex(0)
        layout.addWidget(self.estado_combo)

        # Fecha
        fecha_layout = QHBoxLayout()
        self.btn_fecha_actual = QPushButton("Usar fecha actual")
        self.btn_elegir_fecha = QPushButton("Elegir fecha")
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setEnabled(False)

        fecha_layout.addWidget(self.btn_fecha_actual)
        fecha_layout.addWidget(self.btn_elegir_fecha)
        fecha_layout.addWidget(self.datetime_edit)
        layout.addLayout(fecha_layout)

        self.btn_fecha_actual.clicked.connect(self.usar_fecha_actual)
        self.btn_elegir_fecha.clicked.connect(self.elegir_fecha)

        # Botones finales
        botones_layout = QHBoxLayout()
        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_cancelar = QPushButton("Cancelar")
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_confirmar)
        layout.addLayout(botones_layout)

        self.btn_confirmar.clicked.connect(self.insertar_incidencia)
        self.btn_cancelar.clicked.connect(self.cancelar)

        self.setLayout(layout)

    def cancelar(self):
        # Limpiar la tabla y volver a cargar asignaciones
        self.tabla_asignaciones.setRowCount(0)
        self.cargar_asignaciones()  # vuelve a llenar la tabla como al inicio
    
        # Restaurar combo de tipo
        self.tipo_combo.setCurrentIndex(0)  # asume que la opción por defecto está en el índice 0
    
        # Limpiar descripción
        self.descripcion_input.clear()
    
        # Restaurar combo de estado
        self.estado_combo.setCurrentIndex(0)  # por defecto 'No resuelto'
    
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setEnabled(False)

    def usar_fecha_actual(self):
        self.fecha_actual = True
        self.datetime_edit.setEnabled(False)

    def elegir_fecha(self):
        self.fecha_actual = False
        self.datetime_edit.setEnabled(True)

    def cargar_asignaciones(self):
        query = """
            SELECT A.ID_ASIGNACION, T.NOMBRE, H.HORA_SALIDA_PROGRAMADA, H.HORA_LLEGADA_PROGRAMADA, R.ID_RUTA, R.DURACION_ESTIMADA
            FROM ASIGNACION_TREN A
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
        """
        asignaciones = self.db.fetch_all(query)
        self.tabla_asignaciones.setRowCount(0)

        for i, asignacion in enumerate(asignaciones):
            id_asignacion, tren_nombre, hora_ini, hora_fin, id_ruta, duracion = asignacion

            # Obtener estaciones ordenadas
            estaciones_query = """
                SELECT LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                FROM RUTA_DETALLE RD
                JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                WHERE RD.ID_RUTA = :1
            """
            estaciones = self.db.fetch_one(estaciones_query, (id_ruta,))
            ruta_formato = estaciones[0] if estaciones else "Ruta no disponible"
            horario_str = f"{hora_ini} - {hora_fin}"

            self.tabla_asignaciones.insertRow(i)
            self.tabla_asignaciones.setItem(i, 0, QTableWidgetItem(str(id_asignacion)))
            self.tabla_asignaciones.setItem(i, 1, QTableWidgetItem(tren_nombre))
            self.tabla_asignaciones.setItem(i, 2, QTableWidgetItem(ruta_formato))
            self.tabla_asignaciones.setItem(i, 3, QTableWidgetItem(horario_str))
            
            self.tabla_asignaciones.resizeColumnsToContents()
            self.tabla_asignaciones.resizeRowsToContents()

    def obtener_info(self):
        cursor = self.db.connection.cursor()
        # Obtener ID_RUTA e ID_TREN de la asignacion
        cursor.execute("""
            SELECT ID_HORARIO, ID_TREN, ID_RUTA FROM ASIGNACION_TREN WHERE ID_ASIGNACION = :1
        """, (self.id_asignacion,))
        id_horario, id_tren, id_ruta = cursor.fetchone()

        #Obtener duracion estimada y orden de las estaciones
        cursor.execute("""
            SELECT DURACION_ESTIMADA,
                   LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ESTACIONES
            FROM RUTA R
            JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
            JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
            WHERE R.ID_RUTA = :1
            GROUP BY R.DURACION_ESTIMADA
        """, (id_ruta,))
        resultado_ruta = cursor.fetchone()
        duracion = resultado_ruta[0]
        estaciones = resultado_ruta[1]

        # Obtener hora inicio y fin del horario
        cursor.execute("""
            SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'),
            TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
            FROM HORARIO WHERE ID_HORARIO = :1
        """, (id_horario,))
        hora_inicio, hora_fin = cursor.fetchone()

        # Obtener nombre del tren
        cursor.execute("""
            SELECT NOMBRE FROM TREN WHERE ID_TREN = :1
        """, (id_tren,))
        nombre_tren = cursor.fetchone()

        # Construir el string de información
        info = f"Duración: {duracion}; Orden: {estaciones}; Horario: {hora_inicio} - {hora_fin}; Tren: {nombre_tren}"
        return info

    def insertar_incidencia(self):
        fila = self.tabla_asignaciones.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Error", "Selecciona una asignación.")
            return

        self.id_asignacion = int(self.tabla_asignaciones.item(fila, 0).text())
        tipo = self.tipo_combo.currentText()
        descripcion = self.descripcion_input.text().strip()
        estado = self.estado_combo.currentText()

        if not descripcion:
            QMessageBox.warning(self, "Error", "La descripción no puede estar vacía.")
            return

        if self.fecha_actual:
            fecha_hora = "SYSDATE"
            use_sysdate = True
        else:
            fecha_qt = self.datetime_edit.dateTime().toPyDateTime()
            fecha_hora = fecha_qt.strftime("%Y-%m-%d %H:%M:%S")
            use_sysdate = False

        try:
            cursor = self.db.connection.cursor()
            # Obtener nuevo ID
            cursor.execute("SELECT NVL(MAX(ID_INCIDENCIA), 0) + 1 FROM INCIDENCIA")
            nuevo_id = cursor.fetchone()[0]
            if use_sysdate:
                # Inserta en incidencia
                cursor.execute("""
                    INSERT INTO INCIDENCIA (ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION, FECHA_HORA, ESTADO)
                    VALUES (:1, :2, UPPER(:3), :4, SYSDATE, UPPER(:5))
                """, (nuevo_id, self.id_asignacion, tipo, descripcion, estado))
                
                # Obtiene la informacion de la asignacion
                info = self.obtener_info()
                
                #Inserta en historial
                cursor.execute("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
                nuevo_id_his = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_ASIGNACION, ID_INCIDENCIA, FECHA_REGISTRO)
                    VALUES (:1, :2, :3, :4, :5, SYSDATE)
                """, (nuevo_id_his, info, self.username, self.id_asignacion, nuevo_id,))
            else:
                cursor.execute("""
                    INSERT INTO INCIDENCIA (ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION, FECHA_HORA, ESTADO)
                    VALUES (:1, :2, UPPER(:3), :4, TO_DATE(:5, 'YYYY-MM-DD HH24:MI:SS'), UPPER(:6))
                """, (nuevo_id, self.id_asignacion, tipo, descripcion, fecha_hora, estado))
            
            self.db.connection.commit()
            # Emitir la señal update_triggered
            self.db.event_manager.update_triggered.emit()
            QMessageBox.information(self, "Éxito", "Incidencia registrada correctamente.")
            self.cancelar()
            #if self.confirmar_callback:
            #    self.confirmar_callback()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Error al insertar", str(e))

    def actualizar_datos(self):
        self.cargar_asignaciones()