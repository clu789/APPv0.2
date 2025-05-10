from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog, QListWidget, QComboBox, QAbstractItemView
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os
from PyQt6.QtCore import Qt, QEvent, QMimeData, QItemSelectionModel, QAbstractItemModel
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QEvent, QMimeData, QItemSelectionModel, QAbstractItemModel, QCoreApplication
from PyQt6.QtCore import Qt, QEvent, QMimeData, QItemSelectionModel, QAbstractItemModel, QCoreApplication, QTimer


class InterfazAgregarRuta(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.estaciones_agregadas = []
        self.ruta_imagen = None

        self.init_ui()
        self.cargar_estaciones_existentes()

    def init_ui(self):
        layout = QVBoxLayout()

        # Duración estimada
        self.lbl_duracion = QLabel("Duración estimada (en minutos):")
        self.input_duracion = QLineEdit()
        layout.addWidget(self.lbl_duracion)
        layout.addWidget(self.input_duracion)

        # Selección de estaciones
        self.lbl_estaciones = QLabel("Seleccionar estación:")
        self.combo_estaciones = QComboBox()
        self.btn_agregar_estacion = QPushButton("Agregar a ruta")
        self.btn_agregar_estacion.clicked.connect(self.agregar_estacion_a_ruta)

        estaciones_layout = QHBoxLayout()
        estaciones_layout.addWidget(self.combo_estaciones)
        estaciones_layout.addWidget(self.btn_agregar_estacion)
        layout.addWidget(self.lbl_estaciones)
        layout.addLayout(estaciones_layout)

        # Lista de estaciones agregadas
        self.lista_estaciones = QListWidget()
        self.lista_estaciones.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lista_estaciones.setDefaultDropAction(Qt.DropAction.MoveAction)
        layout.addWidget(QLabel("Estaciones en orden:"))
        layout.addWidget(self.lista_estaciones)
        self.btn_eliminar_estacion = QPushButton("Eliminar estación seleccionada")
        self.btn_eliminar_estacion.clicked.connect(self.eliminar_estacion_agregada)
        layout.addWidget(self.btn_eliminar_estacion)

        # Imagen de la ruta
        self.btn_seleccionar_imagen = QPushButton("Seleccionar imagen")
        self.btn_seleccionar_imagen.clicked.connect(self.seleccionar_imagen)
        self.lbl_imagen_ruta = QLabel("No se ha seleccionado imagen")
        layout.addWidget(self.btn_seleccionar_imagen)
        layout.addWidget(self.lbl_imagen_ruta)

        # Crear nueva estación
        self.input_nueva_estacion = QLineEdit()
        self.btn_crear_estacion = QPushButton("Crear estación")
        self.btn_crear_estacion.clicked.connect(self.crear_estacion)
        crear_estacion_layout = QHBoxLayout()
        crear_estacion_layout.addWidget(self.input_nueva_estacion)
        crear_estacion_layout.addWidget(self.btn_crear_estacion)
        layout.addWidget(QLabel("Crear nueva estación:"))
        layout.addLayout(crear_estacion_layout)

        # Botones principales
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_consultar = QPushButton("Consultar")
        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.consultar)
        self.btn_confirmar.clicked.connect(self.confirmar)

        botones_layout = QHBoxLayout()
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)
        layout.addLayout(botones_layout)

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
            QMessageBox.information(self, "Éxito", f"Ruta agregada con ID {nuevo_id_ruta}.")
            self.cancelar()
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Error", str(e))
