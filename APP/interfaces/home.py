from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                            QScrollArea, QPushButton, QFrame, QMessageBox, QHeaderView, QAbstractItemView,
                            QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QTime
from interfaces.asignacion import InterfazAsignacion, InterfazModificarAsignacion
from PyQt6.QtGui import QIcon, QFont
from base_de_datos.db import DatabaseConnection
import oracledb
from utils import obtener_ruta_recurso

class InterfazHome(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db
        self.setGeometry(100, 100, 1000, 600)
        self.init_ui()
        self.cargar_datos()

        # Conectar la señal de asignación exitosa para recargar datos
        self.panel_asignacion.asignacion_exitosa.connect(self.actualizar_datos)

    def init_ui(self):

    # Layout principal con scroll (nuevo)
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

        # Encabezado con botón de menú, mensaje de bienvenida, reloj y boton incidencias
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)
        
        self.btn_correo = QPushButton()
        self.btn_correo.setIcon(QIcon(obtener_ruta_recurso("APP/icons/alert.png")))
        self.btn_correo.setFixedSize(40, 40)
        self.btn_correo.clicked.connect(lambda: self.main_window.cambiar_interfaz(3))
        top_layout.addWidget(self.btn_correo)

        self.label_bienvenida = QLabel()
        self.load_user_name()
        self.label_bienvenida.setStyleSheet("font-weight: bold; font-size: 16px;")
        top_layout.addWidget(self.label_bienvenida)

        self.label_reloj = QLabel()
        self.label_reloj.setStyleSheet("font-size: 18px;")
        self.actualizar_reloj()
        timer = QTimer(self)
        timer.timeout.connect(self.actualizar_reloj)
        timer.start(1000)
        top_layout.addWidget(self.label_reloj)

        top_layout.addStretch()
        self.main_layout.addLayout(top_layout)

        # Contenedor para tablas y panel de asignación
        self.content_container = QWidget()
        self.content_container.setFixedWidth(900)  # Ancho fijo
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(15)

        # Sección "En curso"
        label_curso = QLabel("En curso")
        label_curso.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 2px solid #3498db;
        """)
        self.content_layout.addWidget(label_curso)
                
        self.tabla_viajes = QTableWidget()
        self.tabla_viajes.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.tabla_viajes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_viajes.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabla_viajes.setColumnCount(6)
       # self.tabla_viajes.setFixedWidth(1050)
        #self.tabla_viajes.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.tabla_viajes.setHorizontalHeaderLabels([
            "ID Asignación","Origen-Destino", "Tren", "Horario", "Rastreo", "Num.Horario"
        ])
        self.tabla_viajes.verticalHeader().setVisible(False)
        self.tabla_viajes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_viajes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_viajes.setStyleSheet("""
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
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
        """)
        
        # Configurar scrollbars
        self.tabla_viajes.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_viajes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Ajustar tamaño de columnas
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.tabla_viajes.setColumnWidth(0, 90) 
        self.tabla_viajes.setColumnWidth(1, 90)
        self.tabla_viajes.setColumnWidth(2, 150)
        self.tabla_viajes.setColumnWidth(3, 110)
        self.tabla_viajes.setColumnWidth(4, 110)
        
        self.content_layout.addWidget(self.tabla_viajes)

        # Sección "Próximamente"
        label_proximos = QLabel("Próximamente")
        label_proximos.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 2px solid #3498db;
        """)
        self.content_layout.addWidget(label_proximos)
                
        self.tabla_proximos = QTableWidget()
        self.tabla_proximos.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.tabla_proximos.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_proximos.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabla_proximos.setColumnCount(5)
        #self.tabla_viajes.setFixedWidth(850)
        #self.tabla_viajes.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.tabla_proximos.setHorizontalHeaderLabels([
             "ID Asignación","Origen-Destino", "Num.Horario", "Horario", "Tren"
        ])
        self.tabla_proximos.verticalHeader().setVisible(False)
        self.tabla_proximos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_proximos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_proximos.setStyleSheet("""
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
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
        """)
        
        # Configurar scrollbars
        self.tabla_proximos.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_proximos.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Ajustar tamaño de columnas
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tabla_proximos.setColumnWidth(0, 90)
        self.tabla_proximos.setColumnWidth(1, 90)
        self.tabla_proximos.setColumnWidth(2, 150)
        self.tabla_proximos.setColumnWidth(3, 110)
        self.tabla_proximos.setColumnWidth(4, 190)
        
        self.content_layout.addWidget(self.tabla_proximos)

        # Panel de asignación (oculto por defecto)
        self.panel_asignacion = InterfazAsignacion(self.main_window, self.db)
        self.panel_asignacion.btn_cancelar.clicked.connect(self.ocultar_panel_asignacion)
        self.panel_asignacion.btn_confirmar.clicked.connect(self.ocultar_panel_asignacion)
        self.panel_asignacion.hide()
        self.content_layout.addWidget(self.panel_asignacion)

            # Panel de modificación 
        print(self.username)
        
        self.panel_modificar = InterfazModificarAsignacion(self.main_window, self.db, self.username)
        self.panel_modificar.modificacion_exitosa.connect(self.actualizar_datos)
        self.panel_modificar.hide()
        self.content_layout.addWidget(self.panel_modificar)

        # Añadir contenedor de contenido al layout principal
        self.main_layout.addWidget(self.content_container, 1)  # Factor de estiramiento 1

        # Botones de acción
        
        self.btn_modificar = QPushButton("Modificar")
        self.btn_modificar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_modificar.clicked.connect(self.accion_modificar)
        
        self.btn_asignar = QPushButton("Asignar")
        self.btn_asignar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_asignar.clicked.connect(self.mostrar_panel_asignacion)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_cancelar.clicked.connect(self.accion_cancelar)


        self.botones_container = QWidget()  # Convertir en atributo de clase
        self.botones_container.setFixedWidth(1200)  # Mismo ancho que las tablas
        botones_layout = QHBoxLayout(self.botones_container)
        botones_layout.setContentsMargins(0, 0, 850, 0)

        # Añade los botones normalmente...
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_modificar)
        botones_layout.addWidget(self.btn_asignar)
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addStretch()

        # Luego añade el contenedor al layout principal:
        botones_main_container = QWidget()
        botones_main_layout = QHBoxLayout(botones_main_container)
        botones_main_layout.addWidget(self.botones_container)
        self.main_layout.addWidget(botones_main_container)

        # Ajustes adicionales para el scroll:
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def resizeEvent(self, event):
        # Ajustar el ancho del contenido cuando cambia el tamaño de la ventana
        new_width = min(1250, self.width() - 100)  # 100px de margen
        self.content_container.setFixedWidth(new_width)
        self.botones_container.setFixedWidth(new_width)
        super().resizeEvent(event)

    def mostrar_panel_asignacion(self):
        """Muestra el panel de asignación y ajusta el tamaño de las tablas"""
        self.tabla_viajes.setMaximumHeight(250)
        self.tabla_proximos.setMaximumHeight(250)
        self.panel_asignacion.show()
         # Asegurar que el scroll se mueva al panel
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
        
    
    def ocultar_panel_asignacion(self):
        """Oculta el panel de asignación y restaura el tamaño de las tablas"""
        self.tabla_viajes.setMaximumHeight(16777215)
        self.tabla_proximos.setMaximumHeight(16777215)
        self.panel_asignacion.hide()
        self.panel_asignacion.hide()
        # Restaurar posición del scroll
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(0))

    def mostrar_panel_modificar(self, id_asignacion):
            self.tabla_viajes.setMaximumHeight(250)
            self.tabla_proximos.setMaximumHeight(250)

            self.panel_modificar.set_asignacion(int(id_asignacion))
            self.panel_modificar.show()

            QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ))

    def ocultar_panel_modificar(self):
        """Oculta el panel de modificación"""
        self.tabla_viajes.setMaximumHeight(16777215)
        self.tabla_proximos.setMaximumHeight(16777215)
        self.panel_modificar.hide()
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(0))
    
    def accion_cancelar(self):
        fila = self.tabla_proximos.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Atención", "Selecciona un registro de 'Próximamente' para cancelar.")
            return

        #id_asignacion = self.tabla_proximos.item(fila, 2).text()
        id_horario = self.tabla_proximos.item(fila, 2).text() 
        id_asignacion = self.tabla_proximos.item(fila, 0).text()
        self.mostrar_panel_modificar(id_asignacion) 

        try:
            # Confirmar cancelación
            confirmar = QMessageBox.question(
                self, "Confirmar",
                f"¿Estás seguro de cancelar la asignación del horario {id_horario}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirmar == QMessageBox.StandardButton.No:
                return

            # Obtener ID de asignación
            asignacion = self.db.fetch_one("""
                SELECT ID_ASIGNACION 
                FROM ASIGNACION_TREN 
                WHERE ID_HORARIO = :1
            """, [id_horario])

            if not asignacion:
                QMessageBox.information(self, "Información", "Este horario no tiene una asignación de tren.")
                return

            id_asignacion = asignacion[0]

            # Eliminar asignación
            self.db.execute_query("DELETE FROM ASIGNACION_TREN WHERE ID_ASIGNACION = :1", [id_asignacion])

            # Registrar en historial
            id_historial = self.db.fetch_one("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")[0]
            informacion = f"Se canceló la asignación del horario {id_horario}."
            self.db.execute_query("""
                INSERT INTO HISTORIAL (
                    ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_HORARIO, FECHA_REGISTRO
                ) VALUES (
                    :1, :2, :3, :4, SYSDATE
                )
            """, [id_historial, informacion, self.username, id_horario])
            # Realiza commit
            self.db.connection.commit()
            self.db.event_manager.update_triggered.emit()
            QMessageBox.information(self, "Éxito", f"Asignación del horario {id_horario} cancelada correctamente.")
            self.cargar_datos()

        except oracledb.DatabaseError as e:
            error_msg = f"Error de base de datos: {e.args[0].message}"
            QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de InterfazHome")
        self.cargar_datos()

    def actualizar_reloj(self):
        self.label_reloj.setText(QTime.currentTime().toString("HH:mm:ss"))

    def cargar_datos(self):
        print("[DEBUG] Recargando datos de Viajes en Curso y Próximamente...")
        self.cargar_datos_viajes()
        self.cargar_datos_proximos()

    def cargar_datos_viajes(self):
        query = """
              SELECT
                A.ID_ASIGNACION,  
                H.ID_HORARIO,
                E1.NOMBRE AS ORIGEN,
                E2.NOMBRE AS DESTINO,
                TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI') AS SALIDA_PROG,
                TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI') AS LLEGADA_PROG,
                TO_CHAR(A.HORA_SALIDA_REAL, 'HH24:MI') AS SALIDA_REAL,
                TO_CHAR(A.HORA_LLEGADA_REAL, 'HH24:MI') AS LLEGADA_REAL,
                T.ID_TREN,
                T.NOMBRE AS NOMBRE_TREN
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            JOIN RUTA_DETALLE RD1 ON RD1.ID_RUTA = A.ID_RUTA AND RD1.ORDEN = 1
            JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
            JOIN RUTA_DETALLE RD2 ON RD2.ID_RUTA = A.ID_RUTA
            JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
            WHERE RD2.ORDEN = (SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = A.ID_RUTA)
            AND TO_NUMBER(TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24')) * 60 + TO_NUMBER(TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'MI')) 
                <= TO_NUMBER(TO_CHAR(SYSDATE, 'HH24')) * 60 + TO_NUMBER(TO_CHAR(SYSDATE, 'MI'))
            AND TO_NUMBER(TO_CHAR(SYSDATE, 'HH24')) * 60 + TO_NUMBER(TO_CHAR(SYSDATE, 'MI')) 
                <= TO_NUMBER(TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24')) * 60 + TO_NUMBER(TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'MI'))
            ORDER BY H.HORA_SALIDA_PROGRAMADA ASC
        """
        viajes = self.db.fetch_all(query)

        if not viajes:
            print("[DEBUG] No se encontraron registros en la consulta de viajes.")
            return

        self.tabla_viajes.setRowCount(len(viajes))
        for i, v in enumerate(viajes):
            id_asignacion = str(v[0]) if v[0] is not None else "N/A"
            id_horario = str(v[1]) if v[1] is not None else "N/A"
            origen_destino = f"{v[2]} - {v[3]}" if v[2] and v[3] else "N/A"
            horario = f"{v[4]}-{v[5]}" if v[4] and v[5] else "N/A"
            rastreo = f"{v[6]} - {v[7] if v[7] else '...'}" if v[6] else "... - ..."
            tren = f"{v[8]} - {v[9]}" if v[8] and v[9] else "N/A"

            self.tabla_viajes.setItem(i, 0, QTableWidgetItem(id_asignacion))
            self.tabla_viajes.setItem(i, 5, QTableWidgetItem(id_horario))
            self.tabla_viajes.setItem(i, 1, QTableWidgetItem(origen_destino))
            self.tabla_viajes.setItem(i, 3, QTableWidgetItem(horario))
            self.tabla_viajes.setItem(i, 4, QTableWidgetItem(rastreo))
            self.tabla_viajes.setItem(i, 2, QTableWidgetItem(tren))

    def cargar_datos_proximos(self):
        query = """
                SELECT
                    A.ID_ASIGNACION,
                    H.ID_HORARIO,
                    E1.NOMBRE AS ORIGEN,
                    E2.NOMBRE AS DESTINO,
                    TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI') AS SALIDA_PROG,
                    TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI') AS LLEGADA_PROG,
                    T.ID_TREN,
                    T.NOMBRE AS NOMBRE_TREN
                FROM ASIGNACION_TREN A
                JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                JOIN TREN T ON A.ID_TREN = T.ID_TREN
                JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
                JOIN RUTA_DETALLE RD1 ON RD1.ID_RUTA = A.ID_RUTA AND
                RD1.ORDEN = 1
                JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
                JOIN RUTA_DETALLE RD2 ON RD2.ID_RUTA = A.ID_RUTA
                JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
                WHERE RD2.ORDEN = (SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = A.ID_RUTA)
                AND TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI') > TO_CHAR(SYSDATE, 'HH24:MI')
                ORDER BY H.HORA_SALIDA_PROGRAMADA ASC
        """
        proximos = self.db.fetch_all(query)
        self.tabla_proximos.setRowCount(0)
        if proximos:
            self.tabla_proximos.setRowCount(len(proximos))
            for i, p in enumerate(proximos):
                self.tabla_proximos.setItem(i, 0, QTableWidgetItem(str(p[0])))  # ID Asignación
                self.tabla_proximos.setItem(i, 2, QTableWidgetItem(str(p[1])))  # Num.Horario
                self.tabla_proximos.setItem(i, 1, QTableWidgetItem(f"{p[2]} - {p[3]}"))  # Origen-Destino
                self.tabla_proximos.setItem(i, 3, QTableWidgetItem(f"{p[4]}-{p[5]}"))  # Horario
                self.tabla_proximos.setItem(i, 4, QTableWidgetItem(f"{p[6]} - {p[7]}"))  # Tren

    def accion_modificar(self):
        fila = self.tabla_proximos.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Atención", "Selecciona un registro de 'Próximamente' para modificar.")
            return

        id_asignacion = self.tabla_proximos.item(fila, 0).text()
        self.mostrar_panel_modificar(id_asignacion)

    def load_user_name(self):
        print(self.username)
        query = "SELECT NOMBRE FROM USUARIO WHERE ID_USUARIO = :1"
        result = self.db.fetch_all(query, (self.username,))
        print(result)
        if result:
            nombre_usuario = result[0][0]
            self.label_bienvenida.setText(f"Bienvenido de vuelta, {nombre_usuario}!")