from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QMessageBox, QScrollArea,
                             QStackedWidget, QHeaderView, QFrame, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import Qt

from interfaces.paneles.panel_trenes import InterfazAgregarTren, InterfazEditarTren  # pendiente definir
from interfaces.paneles.panel_estaciones import InterfazAgregarEstacion, InterfazEditarEstacion  # pendiente definir

class GestionInfraestructura(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db

        self.setWindowTitle("Gestión de Infraestructura")
        self.setGeometry(100, 100, 1000, 600)

        self.initUI()
        self.actualizar_datos()

    def initUI(self):
        # Layout principal con scroll (solo para el diseño, sin afectar funcionalidad)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor principal (igual que antes pero con mejor estilo)
        self.main_container = QWidget()
        self.main_container.setFixedWidth(1400)
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Configurar el scroll area
        self.scroll_area.setWidget(self.main_container)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.scroll_area)
        self.layout().setContentsMargins(0, 0, 0, 0)

        # Encabezado con mejor estilo
        header = QLabel("Gestión de Infraestructura")
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 2px solid #3498db;
        """)
        self.main_layout.addWidget(header)

        # === Sección 1: Tablas lado a lado ===
        tablas_container = QWidget()
        tablas_layout = QHBoxLayout(tablas_container)
        tablas_layout.setContentsMargins(0, 0, 0, 0)
        tablas_layout.setSpacing(15)

        # Tabla de Trenes con mejor estilo
        self.trenes_table = QTableWidget()
        self.trenes_table.setColumnCount(4)
        self.trenes_table.setHorizontalHeaderLabels(["ID Tren", "Nombre", "Capacidad", "Estado"])
        self._configurar_tabla(self.trenes_table)
        self.trenes_table.itemSelectionChanged.connect(self._controlar_boton_tren)
        tablas_layout.addWidget(self._con_titulo("Trenes", self.trenes_table))

        # Tabla de Estaciones con mejor estilo
        self.estaciones_table = QTableWidget()
        self.estaciones_table.setColumnCount(2)
        self.estaciones_table.setHorizontalHeaderLabels(["ID Estación", "Nombre"])
        self._configurar_tabla(self.estaciones_table)
        self.estaciones_table.itemSelectionChanged.connect(self._controlar_boton_estacion)
        tablas_layout.addWidget(self._con_titulo("Estaciones", self.estaciones_table))

        self.main_layout.addWidget(tablas_container)

        # === Sección 2: Botones ===
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 0, 0, 0)
        botones_layout.setSpacing(10)

        # Botones con mejor estilo pero misma funcionalidad
        self.btn_agregar_tren = QPushButton("Agregar Tren")
        self.btn_agregar_tren.setStyleSheet(self._estilo_boton("verde"))
        self.btn_agregar_tren.clicked.connect(lambda: self.mostrar_panel(0))

        self.btn_editar_tren = QPushButton("Editar Tren")
        self.btn_editar_tren.setStyleSheet(self._estilo_boton("azul"))
        self.btn_editar_tren.setEnabled(False)
        self.btn_editar_tren.clicked.connect(self.abrir_edicion_tren)

        self.btn_eliminar_tren = QPushButton("Eliminar Tren")
        self.btn_eliminar_tren.setStyleSheet(self._estilo_boton("rojo"))
        self.btn_eliminar_tren.setEnabled(False)
        self.btn_eliminar_tren.clicked.connect(self.eliminar_tren)

        self.btn_agregar_estacion = QPushButton("Agregar Estación")
        self.btn_agregar_estacion.setStyleSheet(self._estilo_boton("verde"))
        self.btn_agregar_estacion.clicked.connect(lambda: self.mostrar_panel(2))

        self.btn_editar_estacion = QPushButton("Editar Estación")
        self.btn_editar_estacion.setStyleSheet(self._estilo_boton("azul"))
        self.btn_editar_estacion.setEnabled(False)
        self.btn_editar_estacion.clicked.connect(self.abrir_edicion_estacion)

        self.btn_eliminar_estacion = QPushButton("Eliminar Estación")
        self.btn_eliminar_estacion.setStyleSheet(self._estilo_boton("rojo"))
        self.btn_eliminar_estacion.setEnabled(False)
        self.btn_eliminar_estacion.clicked.connect(self.eliminar_estacion)

        # Agregar botones al layout (mismo orden que antes)
        botones_layout.addWidget(self.btn_agregar_tren)
        botones_layout.addWidget(self.btn_editar_tren)
        botones_layout.addWidget(self.btn_eliminar_tren)
        botones_layout.addSpacing(30)  # Separador visual
        botones_layout.addWidget(self.btn_agregar_estacion)
        botones_layout.addWidget(self.btn_editar_estacion)
        botones_layout.addWidget(self.btn_eliminar_estacion)

        self.main_layout.addWidget(botones_container)

        # === Panel desplegable === 
        # (MANTENEMOS EXACTAMENTE LA MISMA LÓGICA ORIGINAL)
        self.stacked = QStackedWidget()
        self.stacked.hide()

        # Panel para agregar trenes (igual que antes)
        self.scroll_trenes = QScrollArea()
        self.scroll_trenes.setWidgetResizable(True)
        self.scroll_trenes.hide()
        self.panel_trenes = InterfazAgregarTren(self.main_window, self.db)
        self.panel_trenes.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_trenes.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_trenes.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_trenes.setWidget(self.panel_trenes)

        # Panel para editar trenes (igual que antes)
        self.scroll_trenes2 = QScrollArea()
        self.scroll_trenes2.setWidgetResizable(True)
        self.scroll_trenes2.hide()
        self.panel_trenes2 = InterfazEditarTren(self.main_window, self.db)
        self.panel_trenes2.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_trenes2.btn_cancelar.clicked.connect(self.bloquear_botones_tren)
        self.panel_trenes2.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_trenes2.btn_confirmar.clicked.connect(self.bloquear_botones_tren)
        self.panel_trenes2.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_trenes2.setWidget(self.panel_trenes2)

        # Panel para agregar estaciones (igual que antes)
        self.scroll_estaciones = QScrollArea()
        self.scroll_estaciones.setWidgetResizable(True)
        self.scroll_estaciones.hide()
        self.panel_estaciones = InterfazAgregarEstacion(self.main_window, self.db)
        self.panel_estaciones.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_estaciones.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_estaciones.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_estaciones.setWidget(self.panel_estaciones)

        # Panel para editar estaciones (igual que antes)
        self.scroll_estaciones2 = QScrollArea()
        self.scroll_estaciones2.setWidgetResizable(True)
        self.scroll_estaciones2.hide()
        self.panel_estaciones2 = InterfazEditarEstacion(self.main_window, self.db)
        self.panel_estaciones2.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_estaciones2.btn_cancelar.clicked.connect(self.bloquear_botones_estacion)
        self.panel_estaciones2.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_estaciones2.btn_confirmar.clicked.connect(self.bloquear_botones_estacion)
        self.panel_estaciones2.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_estaciones2.setWidget(self.panel_estaciones2)

        self.stacked.addWidget(self.scroll_trenes)
        self.stacked.addWidget(self.scroll_trenes2)
        self.stacked.addWidget(self.scroll_estaciones)
        self.stacked.addWidget(self.scroll_estaciones2)

        self.main_layout.addWidget(self.stacked)

    def _configurar_tabla(self, tabla):
        """Configura el estilo de las tablas sin afectar su funcionamiento"""
        tabla.verticalHeader().setVisible(False)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setStyleSheet("""
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
        # Mantenemos el modo de redimensionamiento original
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _con_titulo(self, titulo, widget):
        """Envuelve un widget con un título con estilo"""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel(titulo)
        label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 2px solid #3498db;
        """)

        layout.addWidget(label)
        layout.addWidget(widget)

        return contenedor

    def _estilo_boton(self, tipo):
        """Devuelve el estilo para los botones según su tipo"""
        estilos = {
            "verde": """
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
                QPushButton:disabled {
                    background-color: #95a5a6;
                }
            """,
            "azul": """
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
                QPushButton:disabled {
                    background-color: #95a5a6;
                }
            """,
            "rojo": """
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
                QPushButton:disabled {
                    background-color: #95a5a6;
                }
            """
        }
        return estilos.get(tipo, "")

    def bloquear_botones_tren(self):
        self.trenes_table.clearSelection()
        self.trenes_table.clearFocus()
        self.btn_eliminar_tren.setEnabled(False)
        self.btn_editar_tren.setEnabled(False)

    def bloquear_botones_estacion(self):
        self.estaciones_table.clearSelection()
        self.estaciones_table.clearFocus()
        self.btn_eliminar_estacion.setEnabled(False)
        self.btn_editar_estacion.setEnabled(False)

    def _controlar_boton_tren(self):
        if self.trenes_table.currentRow() == -1:
            self.btn_eliminar_tren.setEnabled(False)
            self.btn_editar_tren.setEnabled(False)
        else:
            self.btn_eliminar_tren.setEnabled(True)
            self.btn_editar_tren.setEnabled(True)
            
    def _controlar_boton_estacion(self):
        if self.estaciones_table.currentRow() == -1:
            self.btn_eliminar_estacion.setEnabled(False)
            self.btn_editar_estacion.setEnabled(False)
        else:
            self.btn_eliminar_estacion.setEnabled(True)
            self.btn_editar_estacion.setEnabled(True)

    def mostrar_panel(self, index):
        """Muestra el panel de asignación y el scroll"""
        self.stacked.setCurrentIndex(index)
        self.stacked.show()

    def ocultar_panel(self):
        """Oculta el panel de asignación y el scroll"""
        self.stacked.hide()

    def abrir_edicion_tren(self):
        fila = self.trenes_table.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona un tren para editar.")
            return

        id_tren = self.trenes_table.item(fila, 0).text()
        nombre = self.trenes_table.item(fila, 1).text()
        capacidad = self.trenes_table.item(fila, 2).text()
        estado = self.trenes_table.item(fila, 3).text()

        self.panel_trenes2.cargar_datos(id_tren, nombre, capacidad, estado)
        self.mostrar_panel(1)
        
    def abrir_edicion_estacion(self):
        fila = self.estaciones_table.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona una estación para editar.")
            return
        id_estacion = self.estaciones_table.item(fila, 0).text()
        nombre = self.estaciones_table.item(fila, 1).text()
        self.panel_estaciones2.cargar_datos(id_estacion, nombre)
        self.mostrar_panel(3)

    def _con_titulo(self, titulo, widget):
        contenedor = QVBoxLayout()
        label = QLabel(titulo)
        label.setStyleSheet("font-weight: bold; font-size: 16px;")
        contenedor.addWidget(label)
        contenedor.addWidget(widget)
        widget_container = QWidget()
        widget_container.setLayout(contenedor)
        return widget_container

    def actualizar_datos(self):
        self.load_trenes_data()
        self.load_estaciones_data()

    def load_trenes_data(self):
        query = "SELECT ID_TREN, NOMBRE, CAPACIDAD, ESTADO FROM TREN"
        resultados = self.db.fetch_all(query)
        self.trenes_table.setRowCount(len(resultados))
        for i, fila in enumerate(resultados):
            for j, valor in enumerate(fila):
                self.trenes_table.setItem(i, j, QTableWidgetItem(str(valor)))

    def load_estaciones_data(self):
        query = "SELECT ID_ESTACION, NOMBRE FROM ESTACION"
        resultados = self.db.fetch_all(query)
        self.estaciones_table.setRowCount(len(resultados))
        for i, fila in enumerate(resultados):
            for j, valor in enumerate(fila):
                self.estaciones_table.setItem(i, j, QTableWidgetItem(str(valor)))

    def buscar_tren_disponible(self, id_horario):
        """
        Busca el ID del primer tren activo disponible que no tenga asignaciones solapadas con el horario dado.
        """
        try:
            query_horario = """
                SELECT HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA
                FROM HORARIO
                WHERE ID_HORARIO = :id_horario
            """
            horario = self.db.fetch_one(query_horario, {"id_horario": id_horario})
            if not horario:
                return None

            hora_inicio, hora_fin = horario

            query = """
                SELECT T.ID_TREN
                FROM TREN T
                WHERE T.ESTADO = 'ACTIVO'
                AND NOT EXISTS (
                    SELECT 1
                    FROM ASIGNACION_TREN A
                    JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                    WHERE A.ID_TREN = T.ID_TREN
                    AND (
                        H.HORA_SALIDA_PROGRAMADA < :hora_fin
                        AND H.HORA_LLEGADA_PROGRAMADA > :hora_inicio
                    )
                )
                ORDER BY T.ID_TREN
            """

            params = {
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin
            }

            resultados = self.db.fetch_all(query, params)
            return resultados[0][0] if resultados else None

        except Exception as e:
            print(f"Error al buscar tren disponible: {str(e)}")
            return None
        
    def eliminar_tren(self):
        """Elimina un tren reasignando sus asignaciones si es posible y registrando los cambios en el historial"""
        self.ocultar_panel()
        fila = self.trenes_table.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona un tren para eliminar.")
            return
        id_tren = self.trenes_table.item(fila, 0).text()
        nombre = self.trenes_table.item(fila, 1).text()
    
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar eliminación")
        confirmacion.setText(f"¿Estás seguro de que deseas eliminar el tren #{id_tren}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
    
        if confirmacion.exec() != 2:
            self.bloquear_botones_tren()
            return
    
        try:
            cursor = self.db.connection.cursor()
    
            cursor.execute("""
                SELECT ID_ASIGNACION FROM ASIGNACION_TREN WHERE ID_TREN = :1
            """, (id_tren,))
            asignaciones = cursor.fetchall()
    
            for asignacion in asignaciones:
                id_asignacion = asignacion[0]
    
                cursor.execute("""
                    SELECT ID_RUTA, ID_HORARIO FROM ASIGNACION_TREN WHERE ID_ASIGNACION = :1
                """, (id_asignacion,))
                id_ruta, id_horario = cursor.fetchone()
    
                nuevo_tren = self.buscar_tren_disponible(id_horario)
                if not nuevo_tren:
                    raise Exception("No hay trenes disponibles para reemplazar en todas las asignaciones. Cancelando eliminación.")
    
                # Actualizar la asignación con el nuevo tren
                cursor.execute("""
                    UPDATE ASIGNACION_TREN SET ID_TREN = :1 WHERE ID_ASIGNACION = :2
                """, (nuevo_tren, id_asignacion))
    
                # Obtener datos para historial
                cursor.execute("""
                    SELECT DURACION_ESTIMADA,
                           LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ESTACIONES
                    FROM RUTA R
                    JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
                    JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                    WHERE R.ID_RUTA = :1
                    GROUP BY R.DURACION_ESTIMADA
                """, (id_ruta,))
                duracion, estaciones = cursor.fetchone()
    
                cursor.execute("""
                    SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'),
                           TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
                    FROM HORARIO WHERE ID_HORARIO = :1
                """, (id_horario,))
                hora_inicio, hora_fin = cursor.fetchone()
    
                info = f"Duración: {duracion}; Orden: {estaciones}; Horario: {hora_inicio} - {hora_fin}; Tren reemplazado: {nombre} → Nuevo tren ID: {nuevo_tren}"
    
                cursor.execute("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
                nuevo_id = cursor.fetchone()[0]
    
                cursor.execute("""
                    INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_ASIGNACION, FECHA_REGISTRO)
                    VALUES (:1, :2, :3, :4, SYSDATE)
                """, (nuevo_id, info, self.username, id_asignacion))
    
            # Eliminar el tren
            cursor.execute("DELETE FROM TREN WHERE ID_TREN = :1", (id_tren,))
            self.db.connection.commit()
    
            self.db.event_manager.update_triggered.emit()
            QMessageBox.information(self, "Resultado", "El tren se ha eliminado correctamente y sus asignaciones fueron reasignadas.")
            self.actualizar_datos()
            self.bloquear_botones_tren()
    
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Error al eliminar", f"No se pudo eliminar el tren.\n{str(e)}")
            self.bloquear_botones_tren()

    def eliminar_estacion(self):
        self.ocultar_panel()
        fila = self.estaciones_table.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona una estación para editar.")
            return
        id_estacion = self.estaciones_table.item(fila, 0).text()
        
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar eliminación")
        confirmacion.setText(f"¿Estás seguro de que deseas eliminar la estación #{id_estacion}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
        
        try:
            if confirmacion.exec() == 2:
                cursor = self.db.connection.cursor()
                # Se elimina el tren
                cursor.execute("""
                    DELETE FROM ESTACION WHERE ID_ESTACION = :1
                """, (id_estacion,))
                # Realiza commit
                self.db.connection.commit()
                # Se notifica que el tren se elimino
                self.db.event_manager.update_triggered.emit()
                QMessageBox.information(self, "Resultado", "La estacion se ha eliminado correctamente.")
                self.actualizar_datos()
                self.bloquear_botones_estacion()
            else:
                self.bloquear_botones_estacion()
        except Exception as e:
            QMessageBox.critical(self, "Error al eliminar", str(e))