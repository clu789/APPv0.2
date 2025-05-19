from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDateTimeEdit, QMessageBox, QScrollArea, QFrame, QAbstractItemView, QHeaderView,
    QSizePolicy
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
        # Layout principal con scroll (como en las otras interfaces)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor principal
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Configurar el scroll area
        self.scroll_area.setWidget(self.main_container)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.scroll_area)
        self.layout().setContentsMargins(0, 0, 0, 0)

        # Título
        titulo = QLabel("Agregar Nueva Incidencia")
        titulo.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 2px solid #3498db;
            margin-bottom: 15px;
        """)
        self.main_layout.addWidget(titulo)

        # Contenedor para el contenido con ancho fijo
        self.content_container = QWidget()
        self.content_container.setFixedWidth(1250)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        # --- Tabla de Asignaciones ---
        label_asignaciones = QLabel("Selecciona la asignación:")
        label_asignaciones.setStyleSheet("font-weight: bold; font-size: 14px;")
        content_layout.addWidget(label_asignaciones)

        self.tabla_asignaciones = QTableWidget()
        self.tabla_asignaciones.setColumnCount(4)
        self.tabla_asignaciones.setHorizontalHeaderLabels(["ID", "Tren", "Ruta", "Horario"])
        self.tabla_asignaciones.verticalHeader().setVisible(False)
        self.tabla_asignaciones.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_asignaciones.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_asignaciones.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 5px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
        """)

        # Ajustar tamaño de columnas y filas
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Configurar altura de las filas y tamaño mínimo de la tabla
        self.tabla_asignaciones.verticalHeader().setDefaultSectionSize(35)  # Altura de cada fila
        self.tabla_asignaciones.setMinimumHeight(200)  # Altura mínima para mostrar varias filas
        self.tabla_asignaciones.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

        # Configurar scrollbars
        self.tabla_asignaciones.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_asignaciones.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_layout.addWidget(self.tabla_asignaciones)

        # --- Formulario de incidencia ---
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)

        # Tipo de incidencia
        tipo_label = QLabel("Tipo de incidencia:")
        tipo_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_layout.addWidget(tipo_label)

        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Retraso", "Averia", "Emergencia"])
        self.tipo_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 200px;
            }
        """)
        form_layout.addWidget(self.tipo_combo)

        # Descripción
        desc_label = QLabel("Descripción (máx 150 caracteres):")
        desc_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_layout.addWidget(desc_label)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setMaxLength(150)
        self.descripcion_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(self.descripcion_input)

        # Estado
        estado_label = QLabel("Estado:")
        estado_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_layout.addWidget(estado_label)

        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["No resuelto", "Resuelto"])
        self.estado_combo.setCurrentIndex(0)
        self.estado_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 200px;
            }
        """)
        form_layout.addWidget(self.estado_combo)

        # Fecha
        fecha_label = QLabel("Fecha y hora:")
        fecha_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_layout.addWidget(fecha_label)

        fecha_btn_container = QWidget()
        fecha_btn_layout = QHBoxLayout(fecha_btn_container)
        fecha_btn_layout.setContentsMargins(0, 0, 0, 0)
        fecha_btn_layout.setSpacing(10)

        self.btn_fecha_actual = QPushButton("Usar fecha actual")
        self.btn_elegir_fecha = QPushButton("Elegir fecha")

        # Estilo para botones de fecha
        for btn in [self.btn_fecha_actual, self.btn_elegir_fecha]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 15px;
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)

        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setEnabled(False)
        self.datetime_edit.setStyleSheet("""
            QDateTimeEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)

        fecha_btn_layout.addWidget(self.btn_fecha_actual)
        fecha_btn_layout.addWidget(self.btn_elegir_fecha)
        fecha_btn_layout.addWidget(self.datetime_edit)
        fecha_btn_layout.addStretch()

        form_layout.addWidget(fecha_btn_container)
        content_layout.addWidget(form_container)

        # --- Botones finales ---
        botones_container = QWidget()
        botones_container.setFixedWidth(900)
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 0, 0, 0)
        botones_layout.setSpacing(15)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_confirmar = QPushButton("Confirmar")

        # Estilo para botones principales
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_confirmar)

        content_layout.addWidget(botones_container)
        self.main_layout.addWidget(self.content_container)

        # Conectar señales
        self.btn_fecha_actual.clicked.connect(self.usar_fecha_actual)
        self.btn_elegir_fecha.clicked.connect(self.elegir_fecha)
        self.btn_confirmar.clicked.connect(self.insertar_incidencia)
        self.btn_cancelar.clicked.connect(self.cancelar)

        # Ajustes del scroll area
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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
            SELECT A.ID_ASIGNACION, T.NOMBRE, TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS'), R.ID_RUTA, R.DURACION_ESTIMADA
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