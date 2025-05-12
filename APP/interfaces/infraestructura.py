from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QMessageBox, QScrollArea,
                             QStackedWidget, QHeaderView)
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
        layout = QVBoxLayout()

        # Encabezado
        header = QLabel("Gestión de Infraestructura")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        # === Sección 1: Tablas lado a lado ===
        tablas_layout = QHBoxLayout()

        self.trenes_table = QTableWidget()
        self.trenes_table.setColumnCount(4)
        self.trenes_table.setHorizontalHeaderLabels(["ID Tren", "Nombre", "Capacidad", "Estado"])
        self.trenes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tablas_layout.addWidget(self._con_titulo("Trenes", self.trenes_table))

        self.estaciones_table = QTableWidget()
        self.estaciones_table.setColumnCount(2)
        self.estaciones_table.setHorizontalHeaderLabels(["ID Estación", "Nombre"])
        self.estaciones_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tablas_layout.addWidget(self._con_titulo("Estaciones", self.estaciones_table))

        layout.addLayout(tablas_layout)

        # === Sección 2: Botones ===
        botones_layout = QHBoxLayout()

        self.btn_agregar_tren = QPushButton("Agregar Tren")
        self.btn_agregar_tren.clicked.connect(lambda: self.mostrar_panel(0))

        self.btn_editar_tren = QPushButton("Editar Tren")
        self.btn_editar_tren.clicked.connect(self.abrir_edicion_tren)

        self.btn_eliminar_tren = QPushButton("Eliminar Tren")
        self.btn_eliminar_tren.clicked.connect(self.eliminar_tren)

        self.btn_agregar_estacion = QPushButton("Agregar Estación")
        self.btn_agregar_estacion.clicked.connect(lambda: self.mostrar_panel(2))

        self.btn_editar_estacion = QPushButton("Editar Estación")
        self.btn_editar_estacion.clicked.connect(self.abrir_edicion_estacion)

        self.btn_eliminar_estacion = QPushButton("Eliminar Estación")
        self.btn_eliminar_estacion.clicked.connect(self.eliminar_estacion)

        botones = [
            self.btn_agregar_tren, self.btn_editar_tren, self.btn_eliminar_tren,
            self.btn_agregar_estacion, self.btn_editar_estacion, self.btn_eliminar_estacion
        ]
        for btn in botones:
            botones_layout.addWidget(btn)

        layout.addLayout(botones_layout)

        # === Panel desplegable ===
        self.stacked = QStackedWidget()
        self.stacked.hide()

        # Panel para agregar trenes
        self.scroll_trenes = QScrollArea()
        self.scroll_trenes.setWidgetResizable(True)
        self.scroll_trenes.hide()
        self.panel_trenes = InterfazAgregarTren(self.main_window, self.db)
        self.panel_trenes.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_trenes.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_trenes.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_trenes.setWidget(self.panel_trenes)
        
        # Panel para agregar trenes
        self.scroll_trenes2 = QScrollArea()
        self.scroll_trenes2.setWidgetResizable(True)
        self.scroll_trenes2.hide()
        self.panel_trenes2 = InterfazEditarTren(self.main_window, self.db)
        self.panel_trenes2.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_trenes2.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_trenes2.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_trenes2.setWidget(self.panel_trenes2)

        # Panel para agregar trenes
        self.scroll_estaciones = QScrollArea()
        self.scroll_estaciones.setWidgetResizable(True)
        self.scroll_estaciones.hide()
        self.panel_estaciones = InterfazAgregarEstacion(self.main_window, self.db)
        self.panel_estaciones.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_estaciones.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_estaciones.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_estaciones.setWidget(self.panel_estaciones)
        
        # Panel para agregar trenes
        self.scroll_estaciones2 = QScrollArea()
        self.scroll_estaciones2.setWidgetResizable(True)
        self.scroll_estaciones2.hide()
        self.panel_estaciones2 = InterfazEditarEstacion(self.main_window, self.db)
        self.panel_estaciones2.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_estaciones2.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_estaciones2.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_estaciones2.setWidget(self.panel_estaciones2)
        
        self.stacked.addWidget(self.scroll_trenes)
        self.stacked.addWidget(self.scroll_trenes2)
        self.stacked.addWidget(self.scroll_estaciones)
        self.stacked.addWidget(self.scroll_estaciones2)

        layout.addWidget(self.stacked)

        self.setLayout(layout)

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

    def eliminar_tren(self):
        """Elimina un tren seleccionado
            guarda en historial todas las asignaciones que tenia ese tren antes de eliminarlo"""
        fila = self.trenes_table.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona un tren para eliminar.")
            return
        id_tren = self.trenes_table.item(fila, 0).text()
        nombre = self.trenes_table.item(fila, 1).text()
        
        try:
            cursor = self.db.connection.cursor()
            # Se busca todas las asignaciones que tengan ese horario para insertarlas en el historial
            cursor.execute("""
                SELECT ID_ASIGNACION FROM ASIGNACION_TREN WHERE ID_TREN = :1
            """, (id_tren,))
            asignaciones = cursor.fetchall()
            for asignacion in asignaciones:
                id_asignacion = asignacion[0]
                # Obtener ID_RUTA e ID_TREN de la asignacion
                cursor.execute("""
                    SELECT ID_RUTA, ID_HORARIO FROM ASIGNACION_TREN WHERE ID_ASIGNACION = :1
                """, (id_asignacion,))
                id_ruta, id_horario = cursor.fetchone()
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
                    SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
                    FROM HORARIO WHERE ID_HORARIO = :1
                """, (id_horario,))
                hora_inicio, hora_fin = cursor.fetchone()


                # Construir el string de información
                info = f"Duración: {duracion}; Orden: {estaciones}; Horario: {hora_inicio} - {hora_fin}; Tren: {nombre}"

                # Se genera el id del nuevo registro del historial
                cursor.execute("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
                nuevo_id = cursor.fetchone()[0]

                # Se inserta el registro de la asignacion que se va a eliminar
                cursor.execute("""
                    INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_ASIGNACION, FECHA_REGISTRO)
                    VALUES (:1, :2, :3, :4, SYSDATE)
                """, (nuevo_id, info, self.username, id_asignacion,))

            # Se elimina el tren
            cursor.execute("""
                DELETE FROM TREN WHERE ID_TREN = :1
            """, (id_tren,))
            # Realiza commit
            self.db.connection.commit()
            # Se notifica que el tren se elimino
            self.db.event_manager.update_triggered.emit()
            QMessageBox.information(self, "Resultado", "El tren se ha eliminado correctamente.")
            self.actualizar_datos()
        except Exception as e:
            QMessageBox.critical(self, "Error al eliminar", str(e))

    def eliminar_estacion(self):
        fila = self.estaciones_table.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona una estación para editar.")
            return
        id_estacion = self.estaciones_table.item(fila, 0).text()
        
        try:
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
        except Exception as e:
            QMessageBox.critical(self, "Error al eliminar", str(e))