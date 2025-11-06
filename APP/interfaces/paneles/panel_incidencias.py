import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDateTimeEdit, QMessageBox, QScrollArea, QFrame, QAbstractItemView, QHeaderView,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDateTime, QDate, QTimer
from PyQt6.QtGui import QTextCharFormat, QColor
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

        # Logger de módulo
        self.logger = logging.getLogger(__name__)

        # Timer para coalescer recargas de asignaciones
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.cargar_asignaciones)

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
            font-size: 18px;
            font-weight: bold;
            color: white;
            padding: 5px 0;
            margin-bottom: 10px;
        """)
        self.main_layout.addWidget(titulo)

        # Contenedor para el contenido (expansivo a lo ancho)
        self.content_container = QWidget()
        self.content_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        # --- Tabla de Asignaciones ---
        label_asignaciones = QLabel("Selecciona la asignación:")
        label_asignaciones.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        content_layout.addWidget(label_asignaciones)

        self.tabla_asignaciones = QTableWidget()
        self.tabla_asignaciones.setColumnCount(4)
        self.tabla_asignaciones.setHorizontalHeaderLabels(["ID", "Tren", "Ruta", "Horario"])
        self.tabla_asignaciones.verticalHeader().setVisible(False)
        self.tabla_asignaciones.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_asignaciones.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_asignaciones.setStyleSheet("""
            QTableWidget {
                background-color: #0b1522;
                border: 1px solid #0b1522;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #121f30ff;
                color: #55a2e7;
                padding: 5px;
                font-weight: bold;
                border: 1px solid #55a2e7;
            }
            QTableWidget::item {
                background-color: #2a4254ff;
                color: white;
                padding: 8px;
                border-bottom: 1px solid #0b1522;
            }
        """)

        # Ajustar tamaño de columnas y filas
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        # Dar más espacio a la columna de Ruta: tren a tamaño de contenido, ruta en expansión
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_asignaciones.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Configurar altura de las filas y tamaño mínimo de la tabla
        self.tabla_asignaciones.verticalHeader().setDefaultSectionSize(35)  # Altura de cada fila
        self.tabla_asignaciones.setMinimumHeight(200)  # Altura mínima para mostrar varias filas
        self.tabla_asignaciones.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

        # Configurar scrollbars
        self.tabla_asignaciones.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_asignaciones.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_asignaciones.setWordWrap(True)
        # Evitar elipsis en celdas; permitir que el alto de fila crezca con wrap
        try:
            self.tabla_asignaciones.setTextElideMode(Qt.TextElideMode.ElideNone)
        except Exception:
            pass

        content_layout.addWidget(self.tabla_asignaciones)

        # --- Formulario de incidencia ---
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)

        # Tipo de incidencia
        tipo_label = QLabel("Tipo de incidencia:")
        tipo_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        form_layout.addWidget(tipo_label)

        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Retraso", "Averia", "Emergencia"])
        self.tipo_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 200px;
                color: white;
            }
        """)
        form_layout.addWidget(self.tipo_combo)

        # Descripción
        desc_label = QLabel("Descripción (máx 150 caracteres):")
        desc_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        form_layout.addWidget(desc_label)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setMaxLength(150)
        self.descripcion_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                color: white;
            }
        """)
        form_layout.addWidget(self.descripcion_input)

        # Estado
        estado_label = QLabel("Estado:")
        estado_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
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
                color: white;
            }
        """)
        form_layout.addWidget(self.estado_combo)

        # Fecha
        fecha_label = QLabel("Fecha y hora:")
        fecha_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        form_layout.addWidget(fecha_label)

        fecha_btn_container = QWidget()
        fecha_btn_layout = QHBoxLayout(fecha_btn_container)
        fecha_btn_layout.setContentsMargins(0, 0, 0, 0)
        fecha_btn_layout.setSpacing(10)

        self.btn_fecha_actual = QPushButton("Usar fecha actual")
        self.btn_elegir_fecha = QPushButton("Elegir fecha")

        # Estilo para botones de fecha
        for btn in [self.btn_fecha_actual, self.btn_elegir_fecha]:
            #btn.setStyleSheet("""
            #    QPushButton {
            #        padding: 8px 15px;
            #        background-color: #3498db;
            #        color: white;
            #        border: none;
            #        border-radius: 4px;
            #        min-width: 120px;
            #    }
            #    QPushButton:hover {
            #        background-color: #2980b9;
            #    }
            #""")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 8px 15px;
                    border: none;
                    border-radius: 4px;
                    min-width: 120px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #2472a4;
                    padding: 9px 14px 7px 16px;
                }
                QPushButton:disabled {
                    background-color: #95a5a6;
                    color: #7f8c8d;
                }
            """)

        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setEnabled(False)
        self.datetime_edit.setStyleSheet("""
            QDateTimeEdit {
                padding: 8px;
                border: 1px solid #0b1522;
                border-radius: 4px;
                color: white;
            }
            QDateTimeEdit: disabled{
                color: #13243aff;
            }
        """)

        # Colorear NUMEROS de días entre semana (L-V) del mes ACTUAL en blanco en el calendario
        cal = self.datetime_edit.calendarWidget()
        if cal is not None:
            fmt_weekday = QTextCharFormat()
            fmt_weekday.setForeground(QColor("white"))

            current = QDate.currentDate()
            year = current.year()
            month = current.month()
            first = QDate(year, month, 1)
            days_in_month = first.daysInMonth()

            for day in range(1, days_in_month + 1):
                d = QDate(year, month, day)
                # 1 = Lunes ... 7 = Domingo; queremos Lunes(1) a Viernes(5)
                if 1 <= d.dayOfWeek() <= 5:
                    cal.setDateTextFormat(d, fmt_weekday)

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
        #self.btn_cancelar.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #e74c3c;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 120px;
        #    }
        #    QPushButton:hover {
        #        background-color: #c0392b;
        #    }
        #""")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
                padding: 9px 14px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)

        #self.btn_confirmar.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 120px;
        #    }
        #    QPushButton:hover {
        #        background-color: #27ae60;
        #    }
        #""")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219653;
                padding: 9px 14px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
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
        # Solo restablecer el formulario sin recargar asignaciones (evita bloqueos)
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
        # Cargar todas las asignaciones y sus rutas en una sola consulta (evita N+1 queries)
        query = """
            WITH RUTAS_ORDEN AS (
                SELECT RD.ID_RUTA,
                       LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ORDEN_RUTA
                FROM RUTA_DETALLE RD
                JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                GROUP BY RD.ID_RUTA
            )
            SELECT A.ID_ASIGNACION,
                   T.NOMBRE AS TREN,
                   RORD.ORDEN_RUTA AS RUTA,
                   TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS HORA_INI,
                   TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS HORA_FIN
            FROM ASIGNACION_TREN A
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            LEFT JOIN RUTAS_ORDEN RORD ON RORD.ID_RUTA = A.ID_RUTA
            ORDER BY A.ID_ASIGNACION
        """
        try:
            asignaciones = self.db.fetch_all(query) or []
        except Exception:
            self.logger.exception("Error cargando asignaciones para incidencias")
            asignaciones = []

        # Mejorar rendimiento durante la carga de datos
        self.tabla_asignaciones.setUpdatesEnabled(False)
        try:
            self.tabla_asignaciones.setRowCount(len(asignaciones))
            for i, asignacion in enumerate(asignaciones):
                id_asignacion, tren_nombre, ruta_formato, hora_ini, hora_fin = asignacion
                horario_str = f"{hora_ini} - {hora_fin}"

                self.tabla_asignaciones.setItem(i, 0, QTableWidgetItem(str(id_asignacion)))
                self.tabla_asignaciones.setItem(i, 1, QTableWidgetItem(tren_nombre))
                self.tabla_asignaciones.setItem(i, 2, QTableWidgetItem(ruta_formato or "Ruta no disponible"))
                self.tabla_asignaciones.setItem(i, 3, QTableWidgetItem(horario_str))

            self.tabla_asignaciones.resizeColumnsToContents()
            self.tabla_asignaciones.resizeRowsToContents()
        finally:
            self.tabla_asignaciones.setUpdatesEnabled(True)

    def obtener_info(self):
        """Obtiene un resumen de la asignación en un solo roundtrip.
        Devuelve: "Duración: X; Orden: a → b → c; Horario: hh:mm:ss - hh:mm:ss; Tren: Nombre"
        """
        try:
            row = self.db.fetch_one(
                """
                SELECT R.DURACION_ESTIMADA,
                       (SELECT LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                          FROM RUTA_DETALLE RD
                          JOIN ESTACION E ON E.ID_ESTACION = RD.ID_ESTACION
                         WHERE RD.ID_RUTA = A.ID_RUTA) AS ESTACIONES,
                       TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS HORA_INI,
                       TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS HORA_FIN,
                       T.NOMBRE AS NOMBRE_TREN
                  FROM ASIGNACION_TREN A
                  JOIN HORARIO H ON H.ID_HORARIO = A.ID_HORARIO
                  JOIN TREN T ON T.ID_TREN = A.ID_TREN
                  JOIN RUTA R ON R.ID_RUTA = A.ID_RUTA
                 WHERE A.ID_ASIGNACION = :id_asig
                """,
                {"id_asig": self.id_asignacion},
            )
            if not row:
                return ""
            duracion, estaciones, hora_ini, hora_fin, nombre_tren = row
            estaciones = estaciones or ""
            nombre_tren = nombre_tren or ""
            hora_ini = hora_ini or ""
            hora_fin = hora_fin or ""
            return f"Duración: {duracion}; Orden: {estaciones}; Horario: {hora_ini} - {hora_fin}; Tren: {nombre_tren}"
        except Exception:
            self.logger.exception("Error obteniendo información de asignación %s", getattr(self, 'id_asignacion', None))
            return ""

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

        use_sysdate = self.fecha_actual
        if not use_sysdate:
            fecha_qt = self.datetime_edit.dateTime().toPyDateTime()
            fecha_hora = fecha_qt.strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Obtener nuevo ID de incidencia (política vigente: solo MAX+1; no usar secuencias aquí)
            row_max = self.db.fetch_one("SELECT NVL(MAX(ID_INCIDENCIA), 0) + 1 FROM INCIDENCIA")
            nuevo_id = row_max[0] if row_max else 1

            # Insertar la incidencia
            if use_sysdate:
                self.db.execute_query(
                    """
                    INSERT INTO INCIDENCIA (ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION, FECHA_HORA, ESTADO)
                    VALUES (:id, :asig, UPPER(:tipo), :descripcion, SYSDATE, UPPER(:estado))
                    """,
                    {"id": nuevo_id, "asig": self.id_asignacion, "tipo": tipo, "descripcion": descripcion, "estado": estado},
                )
            else:
                self.db.execute_query(
                    """
                    INSERT INTO INCIDENCIA (ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION, FECHA_HORA, ESTADO)
                    VALUES (:id, :asig, UPPER(:tipo), :descripcion, TO_DATE(:fh, 'YYYY-MM-DD HH24:MI:SS'), UPPER(:estado))
                    """,
                    {"id": nuevo_id, "asig": self.id_asignacion, "tipo": tipo, "descripcion": descripcion, "fh": fecha_hora, "estado": estado},
                )

            # Insertar en HISTORIAL (siempre) con secuencia
            info = self.obtener_info()
            self.db.execute_query(
                """
                INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_ASIGNACION, ID_INCIDENCIA, FECHA_REGISTRO)
                VALUES (HISTORIAL_SEQ.NEXTVAL, :info, :usuario, :id_asig, :id_incid, SYSDATE)
                """,
                {"info": info, "usuario": self.username, "id_asig": self.id_asignacion, "id_incid": nuevo_id},
            )

            # Emitir la señal update_triggered de forma segura
            try:
                if hasattr(self.db, "event_manager") and getattr(self.db.event_manager, "update_triggered", None):
                    self.db.event_manager.update_triggered.emit()
            except Exception:
                self.logger.exception("Fallo al emitir update_triggered tras insertar incidencia")

            QMessageBox.information(self, "Éxito", "Incidencia registrada correctamente.")
            # Evitar refresco inmediato local para no duplicar cargas con la vista padre;
            # el padre ya programa su propia recarga coalescida.
            # Restablecer formulario sin recargar la tabla (rápido)
            self.tipo_combo.setCurrentIndex(0)
            self.descripcion_input.clear()
            self.estado_combo.setCurrentIndex(0)
            self.datetime_edit.setDateTime(QDateTime.currentDateTime())
            self.datetime_edit.setEnabled(False)
        except Exception as e:
            self.logger.exception("Error al insertar incidencia para asignación %s", self.id_asignacion)
            QMessageBox.critical(self, "Error al insertar", str(e))

    def actualizar_datos(self):
        # Coalescer recargas para evitar parpadeos en la tabla
        try:
            if self._refresh_timer.isActive():
                self._refresh_timer.stop()
            self._refresh_timer.start(150)
            self.logger.debug("Programada recarga de asignaciones en 150 ms")
        except Exception:
            self.logger.exception("Fallo programando recarga; cargando directamente")
            self.cargar_asignaciones()