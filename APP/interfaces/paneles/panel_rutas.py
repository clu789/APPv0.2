from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog, QListWidget, QComboBox, QAbstractItemView, QFrame
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt ,pyqtSignal
import os
from PyQt6.QtCore import Qt, QEvent, QMimeData, QItemSelectionModel, QAbstractItemModel
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QEvent, QMimeData, QItemSelectionModel, QAbstractItemModel, QCoreApplication
from PyQt6.QtCore import Qt, QEvent, QMimeData, QItemSelectionModel, QAbstractItemModel, QCoreApplication, QTimer


class InterfazAgregarRuta(QWidget):
    asignacion_exitosa = pyqtSignal()  # Recargar rutas
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.estaciones_agregadas = []
        self.ruta_imagen = None

        self.init_ui()
        self.cargar_estaciones_existentes()

    def init_ui(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título del panel
        titulo = QLabel("Agregar Nueva Ruta")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0;
                border-bottom: 2px solid #3498db;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(titulo)

        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        # Campo Duración estimada
        self.lbl_duracion = QLabel("Duración estimada (en minutos):")
        self.lbl_duracion.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.input_duracion = QLineEdit()
        self.input_duracion.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        form_layout.addWidget(self.lbl_duracion)
        form_layout.addWidget(self.input_duracion)

        # Separador
        separador1 = QFrame()
        separador1.setFrameShape(QFrame.Shape.HLine)
        separador1.setStyleSheet("color: #eee;")
        form_layout.addWidget(separador1)

        # Selección de estaciones
        self.lbl_estaciones = QLabel("Seleccionar estación:")
        self.lbl_estaciones.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.combo_estaciones = QComboBox()
        self.combo_estaciones.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        self.btn_agregar_estacion = QPushButton("Agregar a ruta")
        self.btn_agregar_estacion.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_agregar_estacion.clicked.connect(self.agregar_estacion_a_ruta)

        estaciones_layout = QHBoxLayout()
        estaciones_layout.addWidget(self.combo_estaciones, 4)
        estaciones_layout.addWidget(self.btn_agregar_estacion, 1)
        form_layout.addWidget(self.lbl_estaciones)
        form_layout.addLayout(estaciones_layout)

        # Lista de estaciones agregadas
        form_layout.addWidget(QLabel("Estaciones en orden:"))

        self.lista_estaciones = QListWidget()
        self.lista_estaciones.setStyleSheet("""
            QListWidget {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.lista_estaciones.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lista_estaciones.setDefaultDropAction(Qt.DropAction.MoveAction)
        form_layout.addWidget(self.lista_estaciones)

        self.btn_eliminar_estacion = QPushButton("Eliminar estación seleccionada")
        self.btn_eliminar_estacion.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_eliminar_estacion.clicked.connect(self.eliminar_estacion_agregada)
        form_layout.addWidget(self.btn_eliminar_estacion)

        # Separador
        separador2 = QFrame()
        separador2.setFrameShape(QFrame.Shape.HLine)
        separador2.setStyleSheet("color: #eee;")
        form_layout.addWidget(separador2)

        # Imagen de la ruta
        self.btn_seleccionar_imagen = QPushButton("Seleccionar imagen")
        self.btn_seleccionar_imagen.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.btn_seleccionar_imagen.clicked.connect(self.seleccionar_imagen)

        self.lbl_imagen_ruta = QLabel("No se ha seleccionado imagen")
        self.lbl_imagen_ruta.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        form_layout.addWidget(self.btn_seleccionar_imagen)
        form_layout.addWidget(self.lbl_imagen_ruta)

        # Separador
        separador3 = QFrame()
        separador3.setFrameShape(QFrame.Shape.HLine)
        separador3.setStyleSheet("color: #eee;")
        form_layout.addWidget(separador3)

        # Crear nueva estación
        form_layout.addWidget(QLabel("Crear nueva estación:"))

        self.input_nueva_estacion = QLineEdit()
        self.input_nueva_estacion.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        self.btn_crear_estacion = QPushButton("Crear estación")
        self.btn_crear_estacion.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_crear_estacion.clicked.connect(self.crear_estacion)

        crear_estacion_layout = QHBoxLayout()
        crear_estacion_layout.addWidget(self.input_nueva_estacion, 4)
        crear_estacion_layout.addWidget(self.btn_crear_estacion, 1)
        form_layout.addLayout(crear_estacion_layout)

        layout.addWidget(form_container)

        # Contenedor para botones
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 10, 0, 0)
        botones_layout.setSpacing(15)

        # Botón Cancelar
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        # Botón Consultar
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        # Botón Confirmar
        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        # Centrar botones
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)
        botones_layout.addStretch()

        layout.addWidget(botones_container)

        # Conexiones (se mantienen igual)
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.consultar)
        self.btn_confirmar.clicked.connect(self.confirmar)

        self.setLayout(layout)

    def cargar_estaciones_existentes(self):
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT ID_ESTACION, NOMBRE FROM ESTACION ORDER BY NOMBRE")
            self.estaciones = cursor.fetchall()
            self.combo_estaciones.clear()
            for id_estacion, nombre in self.estaciones:
                self.combo_estaciones.addItem(nombre, id_estacion)
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar estaciones", str(e))

    def agregar_estacion_a_ruta(self):
        nombre = self.combo_estaciones.currentText()
        id_estacion = self.combo_estaciones.currentData()
        if id_estacion not in [e[0] for e in self.estaciones_agregadas]:
            self.estaciones_agregadas.append((id_estacion, nombre))
            self.lista_estaciones.addItem(nombre)
        else:
            QMessageBox.warning(self, "Duplicado", "La estación ya ha sido agregada.")

    def eliminar_estacion_agregada(self):
        item = self.lista_estaciones.currentItem()
        if not item:
            QMessageBox.warning(self, "Sin selección", "Selecciona una estación para eliminar.")
            return

        nombre_estacion = item.text()

        # Buscar por nombre y quitar de la lista interna
        for i, estacion in enumerate(self.estaciones_agregadas):
            if estacion[1] == nombre_estacion:
                del self.estaciones_agregadas[i]
                break

        # Eliminar del QListWidget
        row = self.lista_estaciones.row(item)
        self.lista_estaciones.takeItem(row)

    def sincronizar_estaciones_agregadas(self):
        nuevo_orden = []
        for i in range(self.lista_estaciones.count()):
            nombre = self.lista_estaciones.item(i).text()
            for estacion in self.estaciones_agregadas:
                if estacion[1] == nombre:
                    nuevo_orden.append(estacion)
                    break
        self.estaciones_agregadas = nuevo_orden

    def seleccionar_imagen(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imagenes (*.png *.jpg *.jpeg)")
        if archivo:
            self.ruta_imagen = archivo
            self.lbl_imagen_ruta.setText(os.path.basename(archivo))

    def crear_estacion(self):
        nombre = self.input_nueva_estacion.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Nombre vacío", "Escribe un nombre para la estación.")
            return
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT NVL(MAX(ID_ESTACION), 0) + 1 FROM ESTACION")
            nuevo_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO ESTACION (ID_ESTACION, NOMBRE) VALUES (:1, :2)", (nuevo_id, nombre))
            self.db.connection.commit()
            QMessageBox.information(self, "Éxito", f"Estación '{nombre}' agregada.")
            self.input_nueva_estacion.clear()
            self.cargar_estaciones_existentes()
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Error", str(e))

    def cancelar(self):
        self.input_duracion.clear()
        self.input_nueva_estacion.clear()
        self.estaciones_agregadas.clear()
        self.lista_estaciones.clear()
        self.ruta_imagen = None
        self.lbl_imagen_ruta.setText("No se ha seleccionado imagen")

    def validar_campos_ruta(self):
        duracion_texto = self.input_duracion.text().strip()
        if not duracion_texto.isdigit():
            QMessageBox.warning(self, "Duración inválida", "Escribe una duración en minutos válida.")
            return None

        duracion = int(duracion_texto)
        if duracion < 1:
            QMessageBox.warning(self, "Duración inválida", "La duración debe ser mayor a 0.")
            return None

        if not self.estaciones_agregadas:
            QMessageBox.warning(self, "Ruta vacía", "Agrega al menos dos estaciones.")
            return None

        if len(self.estaciones_agregadas) < 2:
            QMessageBox.warning(self, "Estaciones insuficientes", "Debes seleccionar al menos dos estaciones.")
            return None

        return duracion

    def consultar(self):
        self.sincronizar_estaciones_agregadas()
        validacion = self.validar_campos_ruta()
        if validacion is None:
            return
        
        try:
            cursor = self.db.connection.cursor()
            # Verifica si ya existe la misma ruta mediante cantidad de estaciones
            # y orden de estaciones
            query = """
                SELECT ID_RUTA FROM RUTA
                WHERE ID_RUTA IN (
                    SELECT ID_RUTA
                    FROM RUTA_DETALLE
                    GROUP BY ID_RUTA
                    HAVING COUNT(*) = :1
                )
            """
            cursor.execute(query, (len(self.estaciones_agregadas),))
            posibles = cursor.fetchall()

            for (id_ruta,) in posibles:
                cursor.execute("""
                    SELECT ID_ESTACION
                    FROM RUTA_DETALLE
                    WHERE ID_RUTA = :1
                    ORDER BY ORDEN
                """, (id_ruta,))
                ids = [row[0] for row in cursor.fetchall()]
                if ids == [e[0] for e in self.estaciones_agregadas]:
                    QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                    return
            QMessageBox.information(self, "Resultado", "La ruta no existe, puedes usarla.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def confirmar(self):
        self.sincronizar_estaciones_agregadas()
        validacion = self.validar_campos_ruta()
        if validacion is None:
            return
        
        duracion = self.input_duracion.text().strip()
        try:
            cursor = self.db.connection.cursor()
            # Verifica si ya existe la misma ruta mediante cantidad de estaciones
            # y orden de estaciones
            query = """
                SELECT ID_RUTA FROM RUTA
                WHERE ID_RUTA IN (
                    SELECT ID_RUTA
                    FROM RUTA_DETALLE
                    GROUP BY ID_RUTA
                    HAVING COUNT(*) = :1
                )
            """
            cursor.execute(query, (len(self.estaciones_agregadas),))
            posibles = cursor.fetchall()
            for (id_ruta,) in posibles:
                cursor.execute("""
                    SELECT ID_ESTACION
                    FROM RUTA_DETALLE
                    WHERE ID_RUTA = :1
                    ORDER BY ORDEN
                """, (id_ruta,))
                ids = [row[0] for row in cursor.fetchall()]
                if ids == [e[0] for e in self.estaciones_agregadas]:
                    QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                    return
            cursor.execute("SELECT NVL(MAX(ID_RUTA), 0) + 1 FROM RUTA")
            nuevo_id_ruta = cursor.fetchone()[0]

            # Cargar imagen (opcional)
            if self.ruta_imagen:
                with open(self.ruta_imagen, "rb") as f:
                    imagen_data = f.read()
                cursor.execute("INSERT INTO RUTA (ID_RUTA, DURACION_ESTIMADA, IMAGEN) VALUES (:1, :2, :3)",
                               (nuevo_id_ruta, int(duracion), imagen_data))
            else:
                cursor.execute("INSERT INTO RUTA (ID_RUTA, DURACION_ESTIMADA) VALUES (:1, :2)",
                               (nuevo_id_ruta, int(duracion)))

            # Insertar detalles
            for i, (id_estacion, _) in enumerate(self.estaciones_agregadas):
                cursor.execute("SELECT NVL(MAX(ID_RUTA_DETALLE), 0) + 1 FROM RUTA_DETALLE")
                id_detalle = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO RUTA_DETALLE (ID_RUTA_DETALLE, ID_RUTA, ID_ESTACION)
                    VALUES (:1, :2, :3)
                """, (id_detalle, nuevo_id_ruta, id_estacion))

            self.db.connection.commit()
            self.db.event_manager.update_triggered.emit()
            QMessageBox.information(self, "Éxito", f"Ruta agregada con ID {nuevo_id_ruta}.")
            self.cancelar()
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Error", str(e))

class InterfazEditarRuta(QWidget):
    asignacion_exitosa = pyqtSignal()  # Recargar rutas
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db
        self.estaciones_agregadas = []
        self.ruta_imagen = None
        self.id_ruta_a_editar = None

        self.init_ui()
        self.cargar_estaciones_existentes()

    def init_ui(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título del panel
        titulo = QLabel("Editar Ruta Existente")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0;
                border-bottom: 2px solid #3498db;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(titulo)

        # Mensaje informativo
        self.lbl_info = QLabel("Selecciona la ruta a editar de la lista superior.")
        self.lbl_info.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        layout.addWidget(self.lbl_info)

        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        # Campo Duración estimada
        self.lbl_duracion = QLabel("Duración estimada (en minutos):")
        self.lbl_duracion.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.input_duracion = QLineEdit()
        self.input_duracion.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        form_layout.addWidget(self.lbl_duracion)
        form_layout.addWidget(self.input_duracion)

        # Separador
        separador1 = QFrame()
        separador1.setFrameShape(QFrame.Shape.HLine)
        separador1.setStyleSheet("color: #eee;")
        form_layout.addWidget(separador1)

        # Selección de estaciones
        self.lbl_estaciones = QLabel("Seleccionar estación:")
        self.lbl_estaciones.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.combo_estaciones = QComboBox()
        self.combo_estaciones.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        self.btn_agregar_estacion = QPushButton("Agregar a ruta")
        self.btn_agregar_estacion.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_agregar_estacion.clicked.connect(self.agregar_estacion_a_ruta)

        estaciones_layout = QHBoxLayout()
        estaciones_layout.addWidget(self.combo_estaciones, 4)
        estaciones_layout.addWidget(self.btn_agregar_estacion, 1)
        form_layout.addWidget(self.lbl_estaciones)
        form_layout.addLayout(estaciones_layout)

        # Lista de estaciones agregadas
        form_layout.addWidget(QLabel("Estaciones en orden:"))

        self.lista_estaciones = QListWidget()
        self.lista_estaciones.setStyleSheet("""
            QListWidget {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.lista_estaciones.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lista_estaciones.setDefaultDropAction(Qt.DropAction.MoveAction)
        form_layout.addWidget(self.lista_estaciones)

        self.btn_eliminar_estacion = QPushButton("Eliminar estación seleccionada")
        self.btn_eliminar_estacion.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_eliminar_estacion.clicked.connect(self.eliminar_estacion_agregada)
        form_layout.addWidget(self.btn_eliminar_estacion)

        # Separador
        separador2 = QFrame()
        separador2.setFrameShape(QFrame.Shape.HLine)
        separador2.setStyleSheet("color: #eee;")
        form_layout.addWidget(separador2)

        # Imagen de la ruta
        self.btn_seleccionar_imagen = QPushButton("Seleccionar imagen")
        self.btn_seleccionar_imagen.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.btn_seleccionar_imagen.clicked.connect(self.seleccionar_imagen)

        self.lbl_imagen_ruta = QLabel("No se ha seleccionado imagen")
        self.lbl_imagen_ruta.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        form_layout.addWidget(self.btn_seleccionar_imagen)
        form_layout.addWidget(self.lbl_imagen_ruta)

        # Separador
        separador3 = QFrame()
        separador3.setFrameShape(QFrame.Shape.HLine)
        separador3.setStyleSheet("color: #eee;")
        form_layout.addWidget(separador3)

        # Crear nueva estación
        form_layout.addWidget(QLabel("Crear nueva estación:"))

        self.input_nueva_estacion = QLineEdit()
        self.input_nueva_estacion.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        self.btn_crear_estacion = QPushButton("Crear estación")
        self.btn_crear_estacion.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_crear_estacion.clicked.connect(self.crear_estacion)

        crear_estacion_layout = QHBoxLayout()
        crear_estacion_layout.addWidget(self.input_nueva_estacion, 4)
        crear_estacion_layout.addWidget(self.btn_crear_estacion, 1)
        form_layout.addLayout(crear_estacion_layout)

        layout.addWidget(form_container)

        # Contenedor para botones
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 10, 0, 0)
        botones_layout.setSpacing(15)

        # Botón Cancelar
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        # Botón Consultar
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        # Botón Actualizar (en lugar de Confirmar)
        self.btn_confirmar = QPushButton("Actualizar")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        # Centrar botones
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)
        botones_layout.addStretch()

        layout.addWidget(botones_container)

        # Conexiones (se mantienen igual)
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.consultar)
        self.btn_confirmar.clicked.connect(self.confirmar)

        self.setLayout(layout)

    def cargar_ruta(self, datos):
        self.id_ruta_a_editar = datos["id"]
        self.input_duracion.setText(datos["duracion"])
        self.ruta_anterior = "Duracion: " + datos["duracion"] + "; Orden: " + datos["estaciones"]

        # Limpiar lista de la interfaz y la lista interna
        self.lista_estaciones.clear()
        self.estaciones_agregadas = []

        # Separar las estaciones y limpiar espacios
        nombres_estaciones = [nombre.strip() for nombre in datos["estaciones"].split("→")]

        # Consulta para obtener ID y nombre de las estaciones
        placeholders = ','.join([':{}'.format(i + 1) for i in range(len(nombres_estaciones))])
        query = f"""
            SELECT ID_ESTACION, NOMBRE FROM ESTACION
            WHERE NOMBRE IN ({placeholders})
        """
        resultados = self.db.fetch_all(query, nombres_estaciones)

        # Asociar nombre con ID
        mapa_estaciones = {nombre: id_ for id_, nombre in resultados}

        # Insertar en el QListWidget y en estaciones_agregadas
        for nombre in nombres_estaciones:
            id_estacion = mapa_estaciones.get(nombre)
            if id_estacion:
                self.lista_estaciones.addItem(nombre)
                self.estaciones_agregadas.append((id_estacion, nombre))
            else:
                print(f"⚠️ Estación no encontrada: {nombre}")


    def cargar_estaciones_existentes(self):
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT ID_ESTACION, NOMBRE FROM ESTACION ORDER BY NOMBRE")
            self.estaciones = cursor.fetchall()
            self.combo_estaciones.clear()
            for id_estacion, nombre in self.estaciones:
                self.combo_estaciones.addItem(nombre, id_estacion)
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar estaciones", str(e))

    def agregar_estacion_a_ruta(self):
        nombre = self.combo_estaciones.currentText()
        id_estacion = self.combo_estaciones.currentData()
        if id_estacion not in [e[0] for e in self.estaciones_agregadas]:
            self.estaciones_agregadas.append((id_estacion, nombre))
            self.lista_estaciones.addItem(nombre)
        else:
            QMessageBox.warning(self, "Duplicado", "La estación ya ha sido agregada.")

    def eliminar_estacion_agregada(self):
        item = self.lista_estaciones.currentItem()
        if not item:
            QMessageBox.warning(self, "Sin selección", "Selecciona una estación para eliminar.")
            return

        nombre_estacion = item.text()

        # Buscar por nombre y quitar de la lista interna
        for i, estacion in enumerate(self.estaciones_agregadas):
            if estacion[1] == nombre_estacion:
                del self.estaciones_agregadas[i]
                break

        # Eliminar del QListWidget
        row = self.lista_estaciones.row(item)
        self.lista_estaciones.takeItem(row)

    def sincronizar_estaciones_agregadas(self):
        nuevo_orden = []
        for i in range(self.lista_estaciones.count()):
            nombre = self.lista_estaciones.item(i).text()
            for estacion in self.estaciones_agregadas:
                if estacion[1] == nombre:
                    nuevo_orden.append(estacion)
                    break
        self.estaciones_agregadas = nuevo_orden

    def seleccionar_imagen(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imagenes (*.png *.jpg *.jpeg)")
        if archivo:
            self.ruta_imagen = archivo
            self.lbl_imagen_ruta.setText(os.path.basename(archivo))

    def crear_estacion(self):
        nombre = self.input_nueva_estacion.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Nombre vacío", "Escribe un nombre para la estación.")
            return
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT NVL(MAX(ID_ESTACION), 0) + 1 FROM ESTACION")
            nuevo_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO ESTACION (ID_ESTACION, NOMBRE) VALUES (:1, :2)", (nuevo_id, nombre))
            self.db.connection.commit()
            QMessageBox.information(self, "Éxito", f"Estación '{nombre}' agregada.")
            self.input_nueva_estacion.clear()
            self.cargar_estaciones_existentes()
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Error", str(e))

    def cancelar(self):
        self.input_duracion.clear()
        self.input_nueva_estacion.clear()
        self.estaciones_agregadas.clear()
        self.lista_estaciones.clear()
        self.ruta_imagen = None
        self.lbl_imagen_ruta.setText("No se ha seleccionado imagen")

    def validar_campos_ruta(self):
        duracion_texto = self.input_duracion.text().strip()
        if not duracion_texto.isdigit():
            QMessageBox.warning(self, "Duración inválida", "Escribe una duración en minutos válida.")
            return None

        duracion = int(duracion_texto)
        if duracion < 1:
            QMessageBox.warning(self, "Duración inválida", "La duración debe ser mayor a 0.")
            return None

        if not self.estaciones_agregadas:
            QMessageBox.warning(self, "Ruta vacía", "Agrega al menos dos estaciones.")
            return None

        if len(self.estaciones_agregadas) < 2:
            QMessageBox.warning(self, "Estaciones insuficientes", "Debes seleccionar al menos dos estaciones.")
            return None

        return duracion

    def consultar(self):
        self.sincronizar_estaciones_agregadas()
        validacion = self.validar_campos_ruta()
        if validacion is None:
            return
        
        try:
            cursor = self.db.connection.cursor()
            # Verifica si ya existe la misma ruta mediante cantidad de estaciones
            # y orden de estaciones
            query = """
                SELECT ID_RUTA FROM RUTA
                WHERE ID_RUTA IN (
                    SELECT ID_RUTA
                    FROM RUTA_DETALLE
                    GROUP BY ID_RUTA
                    HAVING COUNT(*) = :1
                )
            """
            cursor.execute(query, (len(self.estaciones_agregadas),))
            posibles = cursor.fetchall()

            for (id_ruta,) in posibles:
                cursor.execute("""
                    SELECT ID_ESTACION
                    FROM RUTA_DETALLE
                    WHERE ID_RUTA = :1
                    ORDER BY ORDEN
                """, (id_ruta,))
                ids = [row[0] for row in cursor.fetchall()]
                if ids == [e[0] for e in self.estaciones_agregadas]:
                    QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                    return
            QMessageBox.information(self, "Resultado", "La ruta no existe, puedes usarla.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def confirmar(self):
        self.sincronizar_estaciones_agregadas()
        validacion = self.validar_campos_ruta()
        if validacion is None:
            return
        
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar cambios")
        confirmacion.setText(f"¿Estás seguro de que deseas modificar la ruta #{self.id_ruta_a_editar}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)

        duracion = self.input_duracion.text().strip()
        try:
            if confirmacion.exec() == 2:
                cursor = self.db.connection.cursor()
                # Verifica si ya existe la misma ruta mediante cantidad de estaciones
                # y orden de estaciones
                query = """
                    SELECT ID_RUTA FROM RUTA
                    WHERE ID_RUTA IN (
                        SELECT ID_RUTA
                        FROM RUTA_DETALLE
                        GROUP BY ID_RUTA
                        HAVING COUNT(*) = :1
                    )
                """
                cursor.execute(query, (len(self.estaciones_agregadas),))
                posibles = cursor.fetchall()
                for (id_ruta,) in posibles:
                    cursor.execute("""
                        SELECT ID_ESTACION
                        FROM RUTA_DETALLE
                        WHERE ID_RUTA = :1
                        ORDER BY ORDEN
                    """, (id_ruta,))
                    ids = [row[0] for row in cursor.fetchall()]
                    if ids == [e[0] for e in self.estaciones_agregadas]:
                        QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                        return
                #Insertar en HISTORIAL
                cursor.execute("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
                nuevo_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_RUTA, FECHA_REGISTRO)
                    VALUES (:1, :2, :3, :4, SYSDATE)
                """, (nuevo_id, self.ruta_anterior, self.username, self.id_ruta_a_editar,))
                            
                # Actualizar la duración
                if self.ruta_imagen:
                    with open(self.ruta_imagen, "rb") as f:
                        imagen_data = f.read()
                    cursor.execute("""
                        UPDATE RUTA SET DURACION_ESTIMADA = :1, IMAGEN = :2 WHERE ID_RUTA = :3
                    """, (int(duracion), imagen_data, self.id_ruta_a_editar))
                else:
                    cursor.execute("""
                        UPDATE RUTA SET DURACION_ESTIMADA = :1 WHERE ID_RUTA = :2
                    """, (int(duracion), self.id_ruta_a_editar))
                # Eliminar detalles existentes de la ruta
                cursor.execute("DELETE FROM RUTA_DETALLE WHERE ID_RUTA = :1", (self.id_ruta_a_editar,))
                # Insertar nuevos detalles con orden
                for orden, (id_estacion, _) in enumerate(self.estaciones_agregadas, start=1):
                    cursor.execute("SELECT NVL(MAX(ID_RUTA_DETALLE), 0) + 1 FROM RUTA_DETALLE")
                    id_detalle = cursor.fetchone()[0]
                    cursor.execute("""
                        INSERT INTO RUTA_DETALLE (ID_RUTA_DETALLE, ID_RUTA, ID_ESTACION)
                        VALUES (:1, :2, :3)
                    """, (id_detalle, self.id_ruta_a_editar, id_estacion))
                self.db.connection.commit()
                self.db.event_manager.update_triggered.emit()
                QMessageBox.information(self, "Éxito", f"Ruta actualizada correctamente.")
                self.cancelar()
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Error", str(e))
