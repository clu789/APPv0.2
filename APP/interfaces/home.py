from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                            QScrollArea, QPushButton, QFrame, QMessageBox, QHeaderView, QAbstractItemView,
                            QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QTime
from interfaces.asignacion import InterfazAsignacion  
from PyQt6.QtGui import QIcon, QFont
from base_de_datos.db import DatabaseConnection
import oracledb

class InterfazHome(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db
        self.setGeometry(100, 100, 1000, 600)
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        # Layout principal con scroll
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Widget contenedor para el layout principal
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #f5f5f5;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Encabezado con botón de menú, mensaje de bienvenida, reloj y boton incidencias
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)
        
        self.btn_correo = QPushButton()
        self.btn_correo.setIcon(QIcon("APP/icons/alert.png"))
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
        self.layout.addLayout(top_layout)

        # Contenedor para tablas y panel de asignación
        self.content_container = QWidget()
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
        self.tabla_viajes.setColumnCount(5)
        self.tabla_viajes.setHorizontalHeaderLabels([
            "Num.Horario", "Origen-Destino", "Horario", "Rastreo", "Tren"
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
        
        # Ajustar tamaño de columnas con proporciones específicas
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tabla_viajes.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.tabla_viajes.setColumnWidth(0, 100)  # Num.Horario
        self.tabla_viajes.setColumnWidth(2, 120)  # Horario
        self.tabla_viajes.setColumnWidth(3, 120)  # Rastreo
        self.tabla_viajes.setColumnWidth(4, 150)  # Tren
        
        scroll_viajes = QScrollArea()
        scroll_viajes.setWidgetResizable(True)
        scroll_viajes.setWidget(self.tabla_viajes)
        scroll_viajes.setFrameShape(QFrame.Shape.NoFrame)
        self.content_layout.addWidget(scroll_viajes)

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
        self.tabla_proximos.setColumnCount(4)
        self.tabla_proximos.setHorizontalHeaderLabels([
            "Num.Horario", "Origen-Destino", "Horario", "Tren"
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
        
        # Ajustar tamaño de columnas con proporciones específicas
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tabla_proximos.setColumnWidth(0, 100)  # Num.Horario
        self.tabla_proximos.setColumnWidth(2, 120)  # Horario
        self.tabla_proximos.setColumnWidth(3, 150)  # Tren
        
        scroll_proximos = QScrollArea()
        scroll_proximos.setWidgetResizable(True)
        scroll_proximos.setWidget(self.tabla_proximos)
        scroll_proximos.setFrameShape(QFrame.Shape.NoFrame)
        self.content_layout.addWidget(scroll_proximos)

        # Panel de asignación (oculto por defecto)
        self.panel_asignacion = InterfazAsignacion(self.main_window, self.db)
        self.panel_asignacion.btn_cancelar.clicked.connect(self.ocultar_panel_asignacion)
        self.panel_asignacion.btn_confirmar.clicked.connect(self.ocultar_panel_asignacion)
        self.panel_asignacion.hide()
        self.content_layout.addWidget(self.panel_asignacion)

        # Añadir contenedor de contenido al layout principal
        self.layout.addWidget(self.content_container, 1)  # Factor de estiramiento 1

        # Botones de acción
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()
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
        
        botones_layout.addWidget(self.btn_modificar)
        botones_layout.addWidget(self.btn_asignar)
        botones_layout.addWidget(self.btn_cancelar)
        self.layout.addLayout(botones_layout)

        # Configurar el scroll principal
        self.main_scroll.setWidget(self.container)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.main_scroll)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # Guardar alturas originales para restaurarlas después
        self.original_table_heights = {
            'viajes': self.tabla_viajes.sizeHint().height(),
            'proximos': self.tabla_proximos.sizeHint().height()
        }

    def mostrar_panel_asignacion(self):
        """Muestra el panel de asignación y ajusta el tamaño de las tablas"""
        # Reducir altura de las tablas para hacer espacio
        self.tabla_viajes.setMaximumHeight(150)
        self.tabla_proximos.setMaximumHeight(150)
        
        # Mostrar panel de asignación
        self.panel_asignacion.show()
        
        # Ajustar scroll
        self.main_scroll.verticalScrollBar().setValue(0)
        self.main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def ocultar_panel_asignacion(self):
        """Oculta el panel de asignación y restaura el tamaño de las tablas"""
        # Restaurar altura original de las tablas
        self.tabla_viajes.setMaximumHeight(self.original_table_heights['viajes'])
        self.tabla_proximos.setMaximumHeight(self.original_table_heights['proximos'])
        
        # Ocultar panel de asignación
        self.panel_asignacion.hide()
        
        # Ajustar scroll
        self.main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    # ... (resto de los métodos permanecen iguales)
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
              AND A.HORA_SALIDA_REAL IS NOT NULL
              AND A.HORA_LLEGADA_REAL IS NULL
              ORDER BY H.HORA_SALIDA_PROGRAMADA ASC
            ---ORDER BY A.HORA_SALIDA_REAL ASC
        """
        viajes = self.db.fetch_all(query)

        if not viajes:
            print("[DEBUG] No se encontraron registros en la consulta de viajes.")
            return  # Salir si no hay datos

        self.tabla_viajes.setRowCount(len(viajes))
        for i, v in enumerate(viajes):
            # Manejar valores nulos en las columnas
            id_horario = str(v[0]) if v[0] is not None else "N/A"
            origen_destino = f"{v[1]} - {v[2]}" if v[1] and v[2] else "N/A"
            horario = f"{v[3]}-{v[4]}" if v[3] and v[4] else "N/A"
            rastreo = f"{v[5]}-..." if v[5] else "...-..."
            tren = f"{v[7]} - {v[8]}" if v[7] and v[8] else "N/A"

            self.tabla_viajes.setItem(i, 0, QTableWidgetItem(id_horario))
            self.tabla_viajes.setItem(i, 1, QTableWidgetItem(origen_destino))
            self.tabla_viajes.setItem(i, 2, QTableWidgetItem(horario))
            self.tabla_viajes.setItem(i, 3, QTableWidgetItem(rastreo))
            self.tabla_viajes.setItem(i, 4, QTableWidgetItem(tren))

    def cargar_datos_proximos(self):
        query = """
            SELECT 
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
            JOIN RUTA_DETALLE RD1 ON RD1.ID_RUTA = A.ID_RUTA AND RD1.ORDEN = 1
            JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
            JOIN RUTA_DETALLE RD2 ON RD2.ID_RUTA = A.ID_RUTA
            JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
            WHERE RD2.ORDEN = (SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = A.ID_RUTA)
              AND A.HORA_SALIDA_REAL IS NULL
            ORDER BY H.HORA_SALIDA_PROGRAMADA ASC
        """
        proximos = self.db.fetch_all(query)
        self.tabla_proximos.setRowCount(0)
        if proximos:
            self.tabla_proximos.setRowCount(len(proximos))
            for i, p in enumerate(proximos):
                # Num.Horario
                self.tabla_proximos.setItem(i, 0, QTableWidgetItem(str(p[0])))
                
                # Origen-Destino
                self.tabla_proximos.setItem(i, 1, QTableWidgetItem(f"{p[1]} - {p[2]}"))
                
                # Horario (Salida-Llegada programada)
                self.tabla_proximos.setItem(i, 2, QTableWidgetItem(f"{p[3]}-{p[4]}"))
                
                # Tren (ID - Nombre)
                self.tabla_proximos.setItem(i, 3, QTableWidgetItem(f"{p[5]} - {p[6]}"))

    def accion_modificar(self):
        print("Modificar registro...")

    def accion_asignar(self):
        print("Asignar tren...")

    def accion_cancelar(self):
        fila = self.tabla_proximos.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Atención", "Selecciona un registro de 'Próximamente' para cancelar.")
            return

        id_horario = self.tabla_proximos.item(fila, 0).text()
        print(f"[DEBUG] Intentando eliminar ID_HORARIO: {id_horario}")

        # Verificar primero si el horario existe
        horario_existe = self.db.fetch_one("SELECT 1 FROM HORARIO WHERE ID_HORARIO = :1", [id_horario])
        if not horario_existe:
            QMessageBox.warning(self, "Error", f"No se encontró el horario {id_horario} en la base de datos.")
            return

        confirmar = QMessageBox.question(
            self, "Confirmar", 
            f"¿Estás seguro de eliminar el horario {id_horario} y todos sus registros relacionados?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmar == QMessageBox.StandardButton.No:
            return

        try:
            # Desactivar autocommit para manejar transacción manualmente
            self.db.connection.autocommit = False

            # 1. Eliminar incidencias primero
            #self.db.execute_query("DELETE FROM INCIDENCIA WHERE ID_HORARIO = :1", [id_horario])
            
            # 2. Eliminar del historial
            #self.db.execute_query("DELETE FROM HISTORIAL WHERE ID_HORARIO = :1", [id_horario])
            
            # 3. Eliminar asignación de tren
            #self.db.execute_query("DELETE FROM ASIGNACION_TREN WHERE ID_HORARIO = :1", [id_horario])
            
            # 4. Finalmente eliminar el horario
            resultado = self.db.execute_query("DELETE FROM HORARIO WHERE ID_HORARIO = :1", [id_horario])
            
            if resultado == 0:
                raise Exception("No se eliminó ningún registro de HORARIO")

            # Confirmar todos los cambios
            self.db.connection.commit()

            QMessageBox.information(self, "Éxito", f"Horario {id_horario} eliminado correctamente.")

            # Actualizar las tablas
            self.cargar_datos()  # Esto actualiza ambas tablas (viajes y próximos)

             # Emitir señal para actualizar las interfaces
            self.db.event_manager.update_triggered.emit()

        except oracledb.DatabaseError as e:
            # Revertir en caso de error
            self.db.connection.rollback()
            error_msg = f"Error de base de datos: {e.args[0].message}"
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

        except Exception as e:
            self.db.connection.rollback()
            print(f"[ERROR] {str(e)}")
            QMessageBox.critical(self, "Error", str(e))

        finally:
            # Restaurar autocommit
            self.db.connection.autocommit = True

    def load_user_name(self):
        print(self.username)
        query = "SELECT NOMBRE FROM USUARIO WHERE ID_USUARIO = :1"
        result = self.db.fetch_all(query, (self.username,))
        print(result)
        if result:
            nombre_usuario = result[0][0]
            self.label_bienvenida.setText(f"Bienvenido de vuelta, {nombre_usuario}!")