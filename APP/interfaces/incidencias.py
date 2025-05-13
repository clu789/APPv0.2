from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QPushButton, QHBoxLayout, 
                             QSizePolicy, QHeaderView, QStackedWidget, QScrollArea,
                             QMessageBox)
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection
from interfaces.paneles.panel_incidencias import InterfazAgregarIncidencia

class GestionIncidencias(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db

        self.setWindowTitle("Gestión de Incidencias")
        self.setGeometry(100, 100, 1000, 600)

        self.initUI()
        self.load_incidencias()

    def initUI(self):
        layout = QVBoxLayout()

        # --- Encabezado ---
        header = QLabel("Gestión de Incidencias")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        # === Sección 1: Incidencias del día y todas ===
        seccion1_layout = QHBoxLayout()

        # Tabla incidencias del día
        self.tabla_no_resueltas = QTableWidget()
        self.tabla_no_resueltas.setColumnCount(5)
        self.tabla_no_resueltas.setHorizontalHeaderLabels(["ID", "ID Asignacion", "Tipo", "Descripción", "Fecha y Hora"])
        self.tabla_no_resueltas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        seccion1_layout.addWidget(self._con_titulo("Incidencias por Resolver", self.tabla_no_resueltas))

        # Tabla todas las incidencias
        self.tabla_resueltas = QTableWidget()
        self.tabla_resueltas.setColumnCount(5)
        self.tabla_resueltas.setHorizontalHeaderLabels(["ID", "ID Asignacion", "Tipo", "Descripción", "Fecha y Hora"])
        self.tabla_resueltas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        seccion1_layout.addWidget(self._con_titulo("Incidencias Resueltas", self.tabla_resueltas))

        layout.addLayout(seccion1_layout)

        # === Sección 2: Afectaciones ===
        seccion2_layout = QHBoxLayout()

        # Tabla horarios afectados
        self.tabla_horarios_afectados = QTableWidget()
        self.tabla_horarios_afectados.setColumnCount(5)
        self.tabla_horarios_afectados.setHorizontalHeaderLabels([
            "ID Asignación", "Hora Salida", "Hora Llegada", "Ruta", "Tren"
        ])
        self.tabla_horarios_afectados.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        seccion2_layout.addWidget(self._con_titulo("Asignaciones Afectadas", self.tabla_horarios_afectados))
        
        self.tabla_no_resueltas.cellClicked.connect(self.mostrar_afectaciones_no_resuelta)
        self.tabla_resueltas.cellClicked.connect(self.mostrar_afectaciones_resuelta)


        layout.addLayout(seccion2_layout)

        # === Botones de acción ===
        botones_layout = QHBoxLayout()
        self.btn_agregar_incidencia = QPushButton("Agregar Incidencia")
        self.btn_agregar_incidencia.clicked.connect(lambda: self.mostrar_panel(0))
        self.btn_resolver_incidencia = QPushButton("Resolver Incidencia")
        self.btn_resolver_incidencia.clicked.connect(self.resolver_incidencia)
        botones_layout.addWidget(self.btn_agregar_incidencia)
        botones_layout.addWidget(self.btn_resolver_incidencia)

        layout.addLayout(botones_layout)
        
        # Contenedor apilado
        self.stacked = QStackedWidget()
        self.stacked.hide()
        
        # Panel para agregar incidencias
        self.scroll_incidencias = QScrollArea()
        self.scroll_incidencias.setWidgetResizable(True)
        self.scroll_incidencias.hide()
        self.panel_incidencias = InterfazAgregarIncidencia(self.main_window, self.db, self.username)
        self.panel_incidencias.btn_cancelar.clicked.connect(self.ocultar_panel)
        self.panel_incidencias.btn_confirmar.clicked.connect(self.ocultar_panel)
        self.panel_incidencias.btn_confirmar.clicked.connect(self.actualizar_datos)
        self.scroll_incidencias.setWidget(self.panel_incidencias)
        
        # Panel para editar incidencias
        #self.scroll_incidencias2 = QScrollArea()
        #self.scroll_incidencias2.setWidgetResizable(True)
        #self.scroll_incidencias2.hide()
        #self.panel_incidencias2 = InterfazEditarIncidencia(self.main_window, self.db)
        #self.panel_incidencias2.btn_cancelar.clicked.connect(self.ocultar_panel)
        #self.panel_incidencias2.btn_confirmar.clicked.connect(self.ocultar_panel)
        #self.panel_incidencias2.btn_confirmar.clicked.connect(self.actualizar_datos)
        #self.scroll_incidencias2.setWidget(self.panel_incidencias2)
        
        self.stacked.addWidget(self.scroll_incidencias)
        #self.stacked.addWidget(self.scroll_incidencias2)
        layout.addWidget(self.stacked)
        
        self.setLayout(layout)

    def mostrar_panel(self, index):
        """Muestra el panel de asignación y el scroll"""
        self.stacked.setCurrentIndex(index)
        self.stacked.show()

    def ocultar_panel(self):
        """Oculta el panel de asignación y el scroll"""
        self.stacked.hide()

    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de GestionHorariosRutas")
        self.load_incidencias()
    
    def _con_titulo(self, titulo, tabla):
        """Devuelve un widget vertical con título y tabla"""
        contenedor = QVBoxLayout()
        label = QLabel(titulo)
        label.setStyleSheet("font-weight: bold;")
        contenedor.addWidget(label)
        contenedor.addWidget(tabla)
        widget = QWidget()
        widget.setLayout(contenedor)
        return widget

    def mostrar_afectaciones_no_resuelta(self, row, col):
        id_asignacion = self.tabla_no_resueltas.item(row, 1).text()
        cursor = self.db.connection.cursor()

        # Obtener ID_HORARIO e ID_RUTA de la asignación seleccionada
        cursor.execute("""
            SELECT A.ID_HORARIO, A.ID_RUTA
            FROM ASIGNACION_TREN A
            WHERE A.ID_ASIGNACION = :1
        """, (id_asignacion,))
        id_horario, id_ruta = cursor.fetchone()

        # Obtener estaciones ordenadas de la ruta
        cursor.execute("""
            SELECT LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
            FROM RUTA_DETALLE RD
            JOIN ESTACION E ON E.ID_ESTACION = RD.ID_ESTACION
            WHERE RD.ID_RUTA = :1
        """, (id_ruta,))
        orden_ruta = cursor.fetchone()[0]

        # Obtener asignaciones futuras en la misma ruta, con tren incluido
        cursor.execute("""
            SELECT A.ID_ASIGNACION,
                   TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                   TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI'),
                   T.NOMBRE
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            WHERE A.ID_RUTA = :1 AND H.ID_HORARIO > :2
            ORDER BY H.ID_HORARIO
        """, (id_ruta, id_horario))
        filas = cursor.fetchall()

        # Agregar ruta (igual para todas) y tren individual
        afectadas = [(f[0], f[1], f[2], orden_ruta, f[3]) for f in filas]
        self._cargar_tabla(self.tabla_horarios_afectados, afectadas)

    def mostrar_afectaciones_resuelta(self, row, col):
        id_incidencia = self.tabla_resueltas.item(row, 0).text()
        cursor = self.db.connection.cursor()

        # Obtener campo INFORMACION del historial
        cursor.execute("SELECT INFORMACION FROM HISTORIAL WHERE ID_INCIDENCIA = :1", (id_incidencia,))
        resultado = cursor.fetchone()
        if resultado:
            lob = resultado[0]
            info = lob.read() if hasattr(lob, 'read') else str(lob)  # manejar CLOB

            # Extraer datos
            estaciones_objetivo = self._extraer_valor(info, "Orden").strip()
            tren_inicial = self._extraer_valor(info, "Tren").strip()
            horario = self._extraer_valor(info, "Horario")
            hora_inicio = horario.split(" - ")[0]

            # Obtener asignaciones posteriores
            cursor.execute("""
                SELECT A.ID_ASIGNACION,
                       TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                       TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI'),
                       A.ID_RUTA,
                       A.ID_TREN
                FROM ASIGNACION_TREN A
                JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                WHERE TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') >= :1
                ORDER BY H.HORA_SALIDA_PROGRAMADA
            """, (hora_inicio + ":00",))
            filas = cursor.fetchall()

            afectadas = []
            for fila in filas:
                id_asignacion, salida, llegada, id_ruta, id_tren = fila

                # Obtener orden de estaciones de esta ruta
                cursor.execute("""
                    SELECT LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                    FROM RUTA_DETALLE RD
                    JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                    WHERE RD.ID_RUTA = :1
                """, (id_ruta,))
                orden_ruta = cursor.fetchone()[0]

                # Comparar orden
                if orden_ruta.strip() == estaciones_objetivo:
                    # Obtener nombre del tren real de esta asignación
                    cursor.execute("SELECT NOMBRE FROM TREN WHERE ID_TREN = :1", (id_tren,))
                    nombre_tren = cursor.fetchone()[0]
                    afectadas.append((id_asignacion, salida, llegada, orden_ruta, nombre_tren))

            self._cargar_tabla(self.tabla_horarios_afectados, afectadas)

    def _extraer_valor(self, texto, clave):
        partes = texto.split(";")
        for parte in partes:
            if parte.strip().startswith(clave):
                return parte.split(":")[1].strip()
        return ""

    def load_incidencias(self):
        query_no_resueltas = """
            SELECT ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION, TO_CHAR(FECHA_HORA, 'YYYY-MM-DD HH24:MI:SS')
            FROM INCIDENCIA
            WHERE ESTADO = 'NO RESUELTO'
        """
        query_resueltas = """
            SELECT ID_INCIDENCIA, ID_ASIGNACION, TIPO, DESCRIPCION, TO_CHAR(FECHA_HORA, 'YYYY-MM-DD HH24:MI:SS')
            FROM INCIDENCIA
            WHERE ESTADO = 'RESUELTO'
        """
        no_resueltas = self.db.fetch_all(query_no_resueltas)
        resueltas = self.db.fetch_all(query_resueltas)

        self._cargar_tabla(self.tabla_no_resueltas, no_resueltas)
        self._cargar_tabla(self.tabla_resueltas, resueltas)

    def _cargar_tabla(self, tabla, datos):
        tabla.setRowCount(len(datos))
        for i, fila in enumerate(datos):
            for j, valor in enumerate(fila):
                tabla.setItem(i, j, QTableWidgetItem(str(valor)))
        tabla.resizeRowsToContents()

    def resolver_incidencia(self):
        fila = self.tabla_no_resueltas.currentRow()
        id_incidencia = self.tabla_no_resueltas.item(fila, 0).text()
        # Si no hay horario seleccionado manda una advertencia
        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona un horario para eliminar.")
            return
        cursor = self.db.connection.cursor()

        try:
            cursor.execute("""
                UPDATE INCIDENCIA
                SET ESTADO = 'RESUELTO'
                WHERE ID_INCIDENCIA = :1
            """, (id_incidencia,))
            self.db.connection.commit()
            self.db.event_manager.update_triggered.emit()
            QMessageBox.information(self, "Éxito", f"Incidencia {id_incidencia} marcada como resuelta.")
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo resolver la incidencia: {str(e)}")
        finally:
            cursor.close()
