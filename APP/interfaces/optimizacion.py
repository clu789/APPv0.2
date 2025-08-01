from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QPushButton, QMessageBox, QDialog, QLineEdit,
                             QScrollArea, QFrame, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection
import re
from PyQt6.QtGui import QPixmap
from utils import obtener_ruta_recurso

class OptimizacionDinamica(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db

        self.setWindowTitle("Optimización Dinámica")
        self.setGeometry(100, 100, 1200, 600)  # Aumenté el ancho para acomodar más columnas
        self.initUI()
        self.cargar_datos()

    def initUI(self):
        # Layout principal con scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor principal
        self.main_container = QWidget()
        self.main_container.setFixedWidth(1400)
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Configurar el scroll area
        self.scroll_area.setWidget(self.main_container)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.scroll_area)
        self.layout().setContentsMargins(0, 0, 0, 0)

        # --- Encabezado con logo y título ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 15)

        # Título principal centrado
        title_label = QLabel("Optimización Dinámica")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0;
            }
        """)
        header_layout.addWidget(title_label)

        # Contenedor para logo a la derecha
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(20)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Logo
        self.logo = QLabel()
        self.logo.setFixedSize(160, 80)
        self.logo.setPixmap(QPixmap(obtener_ruta_recurso("APP/icons/TRACKSYNC.png")).scaled(
            160, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(self.logo)

        # Título debajo del logo
        self.titulo = QLabel("TRACKSYNC")
        self.titulo.setStyleSheet("""
            font-size: 22px;
            font-style: italic;
        """)
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(self.titulo)

        header_layout.addWidget(logo_container)
        self.main_layout.addLayout(header_layout)

        # Tabla unificada con estilo profesional
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(11)
        self.tabla.setHorizontalHeaderLabels([
            "ID Incidencia",
            "ID Horario", "ID Tren", "Fecha Incidencia", "Tipo Incidencia",
            "Descripción", "Acción", "Horario Original", "Nuevo Horario", 
            "Tren Asignado", "Tren Sugerido"
        ])

        # Configuración de estilo para la tabla
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #eee;
            }
        """)

        # Configuración de comportamiento
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self._controlar_boton_cambios)

        # Ajustar tamaño de columnas
        for i in range(self.tabla.columnCount()):
            if i in [0, 1, 2]:  # Columnas de ID
                self.tabla.setColumnWidth(i, 80)
            elif i == 5:  # Descripción
                self.tabla.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.tabla.setColumnWidth(i, 120)

        self.main_layout.addWidget(self.tabla)

        # Contenedor para botones
        botones_container = QWidget()
        botones = QHBoxLayout(botones_container)
        botones.setContentsMargins(0, 10, 0, 0)
        botones.setSpacing(15)

        # Botón Confirmar
        self.btn_confirmar_cambio = QPushButton("Confirmar Cambio Seleccionado")
        self.btn_confirmar_cambio.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 180px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_confirmar_cambio.setEnabled(False)

        # Botón Editar
        self.btn_editar_cambio = QPushButton("Editar Cambio")
        self.btn_editar_cambio.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_editar_cambio.setEnabled(False)

        # Botón Rechazar
        self.btn_rechazar_cambio = QPushButton("Rechazar Cambio Seleccionado")
        self.btn_rechazar_cambio.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 180px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_rechazar_cambio.setEnabled(False)

        # Agregar botones al layout
        botones.addStretch()
        botones.addWidget(self.btn_confirmar_cambio)
        botones.addWidget(self.btn_editar_cambio)
        botones.addWidget(self.btn_rechazar_cambio)
        botones.addStretch()

        self.main_layout.addWidget(botones_container)

        # Conexiones (se mantienen igual)
        self.btn_confirmar_cambio.clicked.connect(self.confirmar_cambio)
        self.btn_rechazar_cambio.clicked.connect(self.rechazar_cambio)
        self.btn_editar_cambio.clicked.connect(self.editar_cambio)

    def _controlar_boton_cambios(self):
        if self.tabla.currentRow() == -1:
            self.btn_confirmar_cambio.setEnabled(False)
            self.btn_editar_cambio.setEnabled(False)
            self.btn_rechazar_cambio.setEnabled(False)
        else:
            self.btn_confirmar_cambio.setEnabled(True)
            self.btn_editar_cambio.setEnabled(True)
            self.btn_rechazar_cambio.setEnabled(True)

    def ocultar_botones(self):
        self.tabla.clearSelection()
        self.tabla.clearFocus()
        self.btn_confirmar_cambio.setEnabled(False)
        self.btn_editar_cambio.setEnabled(False)
        self.btn_rechazar_cambio.setEnabled(False)

    def actualizar_datos(self):
        self.cargar_datos()

    def calcular_nuevo_horario(self, id_horario):
        query = """
            SELECT 
                HORA_SALIDA_PROGRAMADA + INTERVAL '15' MINUTE,
                HORA_LLEGADA_PROGRAMADA + INTERVAL '15' MINUTE
            FROM HORARIO
            WHERE ID_HORARIO = :1
        """
        resultado = self.db.fetch_one(query, [id_horario])
        if resultado:
            nueva_salida = resultado[0].strftime('%H:%M:%S')
            nueva_llegada = resultado[1].strftime('%H:%M:%S')
            return f"{nueva_salida} - {nueva_llegada}"
        return "N/A - N/A"

    def obtener_horario_original(self, id_horario):
        query = """
            SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'), TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
            FROM HORARIO
            WHERE ID_HORARIO = :1
        """
        resultado = self.db.fetch_one(query, [id_horario])
        if resultado:
            return f"{resultado[0]} - {resultado[1]}"
        return "N/A"

    def buscar_tren_disponible(self, id_horario):
        """
        Busca trenes disponibles para reasignación durante un horario específico.
        Devuelve el nombre del primer tren disponible encontrado o "Ninguno disponible".
        """
        try:
            # 1. Obtener el rango horario que necesitamos cubrir
            query_horario = """
                SELECT HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA
                FROM HORARIO
                WHERE ID_HORARIO = :id_horario
            """
            horario = self.db.fetch_one(query_horario, {"id_horario": id_horario})
            if not horario:
                return "Ninguno disponible"
    
            hora_inicio, hora_fin = horario
    
            # 2. Buscar trenes ACTIVOS que no tengan asignaciones que se solapen
            query = """
                SELECT T.NOMBRE
                FROM TREN T
                WHERE T.ESTADO = 'ACTIVO'
                AND NOT EXISTS (
                    SELECT 1
                    FROM ASIGNACION_TREN A
                    JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                    WHERE A.ID_TREN = T.ID_TREN
                    AND (
                        (H.HORA_SALIDA_PROGRAMADA < :hora_fin AND H.HORA_LLEGADA_PROGRAMADA > :hora_inicio)
                    )
                )
                ORDER BY T.NOMBRE
            """
            
            # Usar parámetros con nombre para evitar confusiones
            params = {
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin
            }
            
            resultados = self.db.fetch_all(query, params)
            
            if resultados:
                return resultados[0][0]  # Devuelve solo el primer tren disponible
            
            return "Ninguno disponible"
            
        except Exception as e:
            print(f"Error al buscar tren disponible: {str(e)}")
            return "Error en búsqueda"

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

        # 3. Obtener info completa de asignaciones futuras afectadas
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
        
            elif tipo in ('AVERIA', 'EMERGENCIA'):
                # Buscar otras asignaciones del mismo tren
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
                    str(id_inc),  # ID_INCIDENCIA como primera columna
                    str(id_hor),
                    str(id_tren_af),
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

    def confirmar_cambio(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona una fila para confirmar.")
            return

        try:
            # Obtener datos de la fila seleccionada
            id_incidencia = self.tabla.item(fila, 0).text()  # ID_INCIDENCIA
            tipo_incidencia = self.tabla.item(fila, 4).text()  # Tipo Incidencia
            descripcion_incidencia = self.tabla.item(fila, 5).text()  # Descripción
    
            # Encontrar todas las filas con la misma incidencia
            filas_afectadas = []
            for i in range(self.tabla.rowCount()):
                if self.tabla.item(i, 0).text() == id_incidencia:
                    filas_afectadas.append(i)
    
            if not filas_afectadas:
                QMessageBox.warning(self, "Error", "No se encontraron horarios afectados.")
                return

            confirmacion = QMessageBox()
            confirmacion.setIcon(QMessageBox.Icon.Question)
            confirmacion.setWindowTitle("Confirmar Cambio")
            confirmacion.setText(f"¿Estás seguro de confirmar los cambios para la incidencia {id_incidencia} (Tipo: {tipo_incidencia})?" +
                                 f"\nSe procesaran {len(filas_afectadas)} registros afectados por la incidencia {id_incidencia}\n")
            confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
            confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
            
            if confirmacion.exec() == 3:
                self.ocultar_botones()
                return
            
            cursor = self.db.connection.cursor()
            bandera_tren = True
    
            # Procesar cada horario afectado según el tipo de incidencia
            for fila_idx in filas_afectadas:
                id_horario = self.tabla.item(fila_idx, 1).text()  # ID_HORARIO
                id_tren = self.tabla.item(fila_idx, 2).text()  # ID_TREN
                accion = self.tabla.item(fila_idx, 6).text()  # Acción sugerida
    
                # Obtener nuevo ID para el historial
                cursor.execute("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
                nuevo_id = cursor.fetchone()[0]
    
                if tipo_incidencia == 'RETRASO':
                    # Procesamiento para RETRASO (cambio de horario)
                    horario_anterior = self.tabla.item(fila_idx, 7).text()  # Horario Original
                    nuevo_horario = self.tabla.item(fila_idx, 8).text()  # Nuevo Horario
    
                    if nuevo_horario != "N/A - N/A":
                        # Registrar cambio de horario en la base de datos
                        cursor.execute("""
                            INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_HORARIO, FECHA_REGISTRO)
                            VALUES (:1, :2, :3, :4, SYSDATE)
                        """, (nuevo_id, horario_anterior, self.username, id_horario,))
    
                        # Actualizar horario
                        nueva_salida, nueva_llegada = nuevo_horario.split(' - ')
                        cursor.execute("""
                            UPDATE HORARIO
                            SET HORA_SALIDA_PROGRAMADA = TO_DATE(:1, 'HH24:MI:SS'),
                                HORA_LLEGADA_PROGRAMADA = TO_DATE(:2, 'HH24:MI:SS')
                            WHERE ID_HORARIO = :3
                        """, [nueva_salida, nueva_llegada, id_horario])
    
                elif tipo_incidencia in ('AVERIA', 'EMERGENCIA'):
                    # Procesamiento para AVERÍA/EMERGENCIA (reasignación de tren)
                    tren_anterior = self.tabla.item(fila_idx, 9).text()  # Tren Asignado
                    tren_sugerido = self.tabla.item(fila_idx, 10).text()  # Tren Sugerido
    
                    if accion == 'REASIGNAR TREN' and tren_sugerido != "Ninguno disponible":
                        if bandera_tren:
                            cursor.execute("""
                                SELECT ID_ASIGNACION FROM INCIDENCIA WHERE ID_INCIDENCIA = :1
                            """, (id_incidencia,))
                            id_asignacion = cursor.fetchone()[0]
                            # Actualizar asignación de tren
                            cursor.execute("""
                                UPDATE ASIGNACION_TREN
                                SET ID_TREN = (SELECT ID_TREN FROM TREN WHERE NOMBRE = :1)
                                WHERE ID_ASIGNACION = :2
                            """, [tren_sugerido, id_asignacion])
                            bandera_tren = False
                        # Obtener id_asignacion
                        cursor.execute("""
                            SELECT ID_ASIGNACION FROM ASIGNACION_TREN
                            WHERE ID_HORARIO = :1
                            AND ID_TREN = :2
                        """, (id_horario, id_tren,))
                        id_asignacion = cursor.fetchone()[0]
                        # Registrar en historial
                        cursor.execute("""
                            INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_ASIGNACION, FECHA_REGISTRO)
                            VALUES (:1, 'Reasignación de tren por ' || :2 || '. Anterior: ' || :3 || ' Nuevo: ' || :4, :5, :6, SYSDATE)
                        """, (nuevo_id, tipo_incidencia, tren_anterior, tren_sugerido, self.username, id_asignacion))
    
                        # Actualizar asignación de tren
                        cursor.execute("""
                            UPDATE ASIGNACION_TREN
                            SET ID_TREN = (SELECT ID_TREN FROM TREN WHERE NOMBRE = :1)
                            WHERE ID_HORARIO = :2
                        """, [tren_sugerido, id_horario])
    
                    elif accion == 'CANCELAR VIAJE':
                        # Obtener id_asignacion
                        cursor.execute("""
                            SELECT ID_ASIGNACION FROM ASIGNACION_TREN
                            WHERE ID_HORARIO = :1
                            AND ID_TREN = :2
                        """, (id_horario, id_tren,))
                        id_asignacion = cursor.fetchone()[0]
                        # Eliminar asignación
                        self.db.execute_query("DELETE FROM ASIGNACION_TREN WHERE ID_ASIGNACION = :1", [id_asignacion])
                        # Registrar cancelación en historial
                        cursor.execute("""
                            INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_ASIGNACION, FECHA_REGISTRO)
                            VALUES (:1, 'Viaje cancelado por ' || :2, :3, :4, SYSDATE)
                        """, (nuevo_id, tipo_incidencia, self.username, id_asignacion))
    
    
            # Marcar incidencia como resuelta
            cursor.execute("""
                UPDATE INCIDENCIA 
                SET ESTADO = 'RESUELTO'
                WHERE ID_INCIDENCIA = :1
            """, [id_incidencia])
    
            self.db.connection.commit()
            self.db.event_manager.update_triggered.emit()
            
            QMessageBox.information(
                self, 
                "Éxito", 
                f"Se procesaron {len(filas_afectadas)} registros afectados por la incidencia {id_incidencia}\n"
                f"Incidencia marcada como RESUELTO."
            )
            self.cargar_datos()
    
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(
                self, 
                "Error", 
                f"No se pudo confirmar el cambio:\n{str(e)}"
            )
            self.cargar_datos()

    def editar_cambio(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona una fila para editar.")
            return

        # Obtener datos de la fila seleccionada
        id_horario = self.tabla.item(fila, 1).text()
        tipo_incidencia = self.tabla.item(fila, 4).text()

        # Crear diálogo de edición
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Editar Sugerencia - {tipo_incidencia}")
        layout = QVBoxLayout()

        if tipo_incidencia == 'RETRASO':
            # Editar horario
            horario_actual = self.tabla.item(fila, 8).text()
            label = QLabel("Nuevo Horario (HH:MM:SS - HH:MM:SS):")
            edit = QLineEdit(horario_actual)
            layout.addWidget(label)
            layout.addWidget(edit)
        else:
            # Editar tren sugerido
            tren_actual = self.tabla.item(fila, 10).text()
            label = QLabel("Nuevo Tren Sugerido:")
            edit = QLineEdit(tren_actual)
            layout.addWidget(label)
            layout.addWidget(edit)

        # Botones
        btn_guardar = QPushButton("Guardar Cambio")
        btn_cancelar = QPushButton("Cancelar")
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_guardar)
        btn_layout.addWidget(btn_cancelar)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)

        def guardar_cambio():
            nuevo_valor = edit.text().strip()

            # Validación básica
            if tipo_incidencia == 'RETRASO':
                if not re.match(r"\d{2}:\d{2}:\d{2} - \d{2}:\d{2}:\d{2}", nuevo_valor):
                    QMessageBox.warning(dialog, "Error", "Formato de horario inválido")
                    return
            elif not nuevo_valor:
                QMessageBox.warning(dialog, "Error", "El tren sugerido no puede estar vacío")
                return

            # Actualizar tabla
            if tipo_incidencia == 'RETRASO':
                self.tabla.item(fila, 8).setText(nuevo_valor)
            else:
                self.tabla.item(fila, 10).setText(nuevo_valor)

            QMessageBox.information(dialog, "Éxito", "Cambio guardado correctamente")
            dialog.close()

        btn_guardar.clicked.connect(guardar_cambio)
        btn_cancelar.clicked.connect(dialog.close)

        dialog.exec()

    def rechazar_cambio(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona una fila para rechazar.")
            return

        id_incidencia = self.tabla.item(fila, 0).text()  # Columna 0 es ID_INCIDENCIA
        tipo_incidencia = self.tabla.item(fila, 4).text()  # Columna 4 es Tipo Incidencia
        
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar Rechazo")
        confirmacion.setText(f"¿Estás seguro de rechazar los cambios para la incidencia {id_incidencia} (Tipo: {tipo_incidencia})?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)

        if confirmacion.exec() == 2:
            try:
                cursor = self.db.connection.cursor()
                cursor.execute("UPDATE INCIDENCIA SET ESTADO = 'RESUELTO' WHERE ID_INCIDENCIA = :1", [id_incidencia])
                self.db.connection.commit()
                # Emitir la señal update_triggered
                self.db.event_manager.update_triggered.emit()
                QMessageBox.information(self, "Éxito", f"Cambios para la incidencia {id_incidencia} rechazados")
                self.cargar_datos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo rechazar el cambio:\n{str(e)}")
            finally:
                cursor.close()
        self.ocultar_botones()