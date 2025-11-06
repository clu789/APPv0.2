import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog, QListWidget, QComboBox, QAbstractItemView, QFrame
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal


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
                color: white;
                padding: 5px 0;
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
        self.lbl_duracion.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_duracion = QLineEdit()
        self.input_duracion.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        form_layout.addWidget(self.lbl_duracion)
        form_layout.addWidget(self.input_duracion)

        # Separador
        #separador1 = QFrame()
        #separador1.setFrameShape(QFrame.Shape.HLine)
        #separador1.setStyleSheet("color: #eee;")
        #form_layout.addWidget(separador1)

        # Selección de estaciones
        self.lbl_estaciones = QLabel("Seleccionar estación:")
        self.lbl_estaciones.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")

        self.combo_estaciones = QComboBox()
        self.combo_estaciones.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
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
        self.lbl_estaciones_orden = QLabel("Estaciones en orden:")
        self.lbl_estaciones_orden.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        form_layout.addWidget(self.lbl_estaciones_orden)

        self.lista_estaciones = QListWidget()
        self.lista_estaciones.setStyleSheet("""
            QListWidget {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
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
        #separador2 = QFrame()
        #separador2.setFrameShape(QFrame.Shape.HLine)
        #separador2.setStyleSheet("color: #eee;")
        #form_layout.addWidget(separador2)

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
        self.lbl_imagen_ruta.setStyleSheet("font-size: 13px; color: white;")
        form_layout.addWidget(self.btn_seleccionar_imagen)
        form_layout.addWidget(self.lbl_imagen_ruta)

        # Separador
        separador3 = QFrame()
        separador3.setFrameShape(QFrame.Shape.HLine)
        separador3.setStyleSheet("color: #eee;")
        form_layout.addWidget(separador3)

        # Crear nueva estacion
        self.lbl_crear_estacion = QLabel("Crear nueva estación:")
        self.lbl_crear_estacion.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        form_layout.addWidget(self.lbl_crear_estacion)

        self.input_nueva_estacion = QLineEdit()
        self.input_nueva_estacion.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
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
        #self.btn_cancelar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #e74c3c;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #        font-weight: bold;
        #    }
        #    QPushButton:hover {
        #        background-color: #c0392b;
        #    }
        #""")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
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

        # Botón Consultar
        self.btn_consultar = QPushButton("Consultar")
        #self.btn_consultar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #3498db;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #        font-weight: bold;
        #    }
        #    QPushButton:hover {
        #        background-color: #2980b9;
        #    }
        #""")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
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

        # Botón Confirmar
        self.btn_confirmar = QPushButton("Confirmar")
        #self.btn_confirmar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #        font-weight: bold;
        #    }
        #    QPushButton:hover {
        #        background-color: #27ae60;
        #    }
        #""")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
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
            rows = self.db.fetch_all(
                "SELECT ID_ESTACION, NOMBRE FROM ESTACION ORDER BY NOMBRE",
                None,
            )
            self.estaciones = rows or []
            self.combo_estaciones.clear()
            for id_estacion, nombre in self.estaciones:
                self.combo_estaciones.addItem(nombre, id_estacion)
        except Exception as e:
            logging.getLogger(__name__).exception("Error al cargar estaciones")
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
            # Unicidad por nombre (insensible a mayúsculas)
            existe = self.db.fetch_one(
                "SELECT 1 FROM ESTACION WHERE UPPER(NOMBRE) = :nombre",
                {"nombre": nombre.upper()},
            )
            if existe:
                QMessageBox.information(self, "Duplicado", f"La estación '{nombre}' ya existe.")
                return

            nuevo_id_row = self.db.fetch_one("SELECT NVL(MAX(ID_ESTACION), 0) + 1 AS ID FROM ESTACION", None)
            nuevo_id = nuevo_id_row[0] if nuevo_id_row else 1

            self.db.execute_query(
                "INSERT INTO ESTACION (ID_ESTACION, NOMBRE) VALUES (:id, :nombre)",
                {"id": nuevo_id, "nombre": nombre},
            )
            QMessageBox.information(self, "Éxito", f"Estación '{nombre}' agregada.")
            self.input_nueva_estacion.clear()
            self.cargar_estaciones_existentes()
        except Exception as e:
            logging.getLogger(__name__).exception("Error al crear estación")
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
            # Verifica si ya existe la misma ruta mediante cantidad de estaciones
            # y orden de estaciones
            query = (
                "SELECT ID_RUTA FROM RUTA WHERE ID_RUTA IN ("
                "    SELECT ID_RUTA FROM RUTA_DETALLE GROUP BY ID_RUTA HAVING COUNT(*) = :count_est"
                ")"
            )
            posibles = self.db.fetch_all(query, {"count_est": len(self.estaciones_agregadas)}) or []

            for (id_ruta,) in posibles:
                ids_rows = self.db.fetch_all(
                    """
                        SELECT ID_ESTACION
                        FROM RUTA_DETALLE
                        WHERE ID_RUTA = :id_ruta
                        ORDER BY ORDEN
                    """,
                    {"id_ruta": id_ruta},
                ) or []
                ids = [row[0] for row in ids_rows]
                if ids == [e[0] for e in self.estaciones_agregadas]:
                    QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                    return
            QMessageBox.information(self, "Resultado", "La ruta no existe, puedes usarla.")
        except Exception as e:
            logging.getLogger(__name__).exception("Error en consulta de duplicados de ruta")
            QMessageBox.critical(self, "Error", str(e))

    def confirmar(self):
        self.sincronizar_estaciones_agregadas()
        validacion = self.validar_campos_ruta()
        if validacion is None:
            return
        
        duracion = self.input_duracion.text().strip()
        try:
            # Verifica si ya existe la misma ruta mediante cantidad de estaciones
            # y orden de estaciones
            query = (
                "SELECT ID_RUTA FROM RUTA WHERE ID_RUTA IN ("
                "    SELECT ID_RUTA FROM RUTA_DETALLE GROUP BY ID_RUTA HAVING COUNT(*) = :count_est"
                ")"
            )
            posibles = self.db.fetch_all(query, {"count_est": len(self.estaciones_agregadas)}) or []
            for (id_ruta,) in posibles:
                ids_rows = self.db.fetch_all(
                    """
                        SELECT ID_ESTACION
                        FROM RUTA_DETALLE
                        WHERE ID_RUTA = :id_ruta
                        ORDER BY ORDEN
                    """,
                    {"id_ruta": id_ruta},
                ) or []
                ids = [row[0] for row in ids_rows]
                if ids == [e[0] for e in self.estaciones_agregadas]:
                    QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                    return

            nuevo_id_row = self.db.fetch_one("SELECT NVL(MAX(ID_RUTA), 0) + 1 AS ID FROM RUTA", None)
            nuevo_id_ruta = nuevo_id_row[0] if nuevo_id_row else 1

            # Cargar imagen (opcional)
            if self.ruta_imagen:
                try:
                    with open(self.ruta_imagen, "rb") as f:
                        imagen_data = f.read()
                except Exception as img_err:
                    logging.getLogger(__name__).exception("No se pudo leer la imagen de ruta")
                    QMessageBox.warning(self, "Imagen", "No se pudo leer la imagen seleccionada. Se guardará sin imagen.")
                    imagen_data = None
                if imagen_data is not None:
                    self.db.execute_query(
                        "INSERT INTO RUTA (ID_RUTA, DURACION_ESTIMADA, IMAGEN) VALUES (:id, :dur, :img)",
                        {"id": nuevo_id_ruta, "dur": int(duracion), "img": imagen_data},
                    )
                else:
                    self.db.execute_query(
                        "INSERT INTO RUTA (ID_RUTA, DURACION_ESTIMADA) VALUES (:id, :dur)",
                        {"id": nuevo_id_ruta, "dur": int(duracion)},
                    )
            else:
                self.db.execute_query(
                    "INSERT INTO RUTA (ID_RUTA, DURACION_ESTIMADA) VALUES (:id, :dur)",
                    {"id": nuevo_id_ruta, "dur": int(duracion)},
                )

            # Insertar detalles
            for i, (id_estacion, _) in enumerate(self.estaciones_agregadas):
                id_det_row = self.db.fetch_one("SELECT NVL(MAX(ID_RUTA_DETALLE), 0) + 1 AS ID FROM RUTA_DETALLE", None)
                id_detalle = id_det_row[0] if id_det_row else 1
                self.db.execute_query(
                    """
                        INSERT INTO RUTA_DETALLE (ID_RUTA_DETALLE, ID_RUTA, ID_ESTACION)
                        VALUES (:id_det, :id_ruta, :id_est)
                    """,
                    {"id_det": id_detalle, "id_ruta": nuevo_id_ruta, "id_est": id_estacion},
                )

            # Emitir señales solo si existen
            if hasattr(self.db, "event_manager") and getattr(self.db.event_manager, "update_triggered", None):
                self.db.event_manager.update_triggered.emit()
            if hasattr(self, "asignacion_exitosa"):
                try:
                    self.asignacion_exitosa.emit()
                except Exception:
                    pass
            QMessageBox.information(self, "Éxito", f"Ruta agregada con ID {nuevo_id_ruta}.")
            self.cancelar()
        except Exception as e:
            logging.getLogger(__name__).exception("Error al confirmar creación de ruta")
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
        self.logger = logging.getLogger(__name__)

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
                color: white;
                padding: 5px 0;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(titulo)

        # Mensaje informativo
        self.lbl_info = QLabel("Selecciona la ruta a editar de la lista superior.")
        self.lbl_info.setStyleSheet("font-size: 14px; color: white;")
        layout.addWidget(self.lbl_info)

        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        # Campo Duración estimada
        self.lbl_duracion = QLabel("Duración estimada (en minutos):")
        self.lbl_duracion.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_duracion = QLineEdit()
        self.input_duracion.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        form_layout.addWidget(self.lbl_duracion)
        form_layout.addWidget(self.input_duracion)

        # Separador
        #separador1 = QFrame()
        #separador1.setFrameShape(QFrame.Shape.HLine)
        #separador1.setStyleSheet("color: #eee;")
        #form_layout.addWidget(separador1)

        # Selección de estaciones
        self.lbl_estaciones = QLabel("Seleccionar estación:")
        self.lbl_estaciones.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")

        self.combo_estaciones = QComboBox()
        self.combo_estaciones.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
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
        self.lbl_estaciones_orden = QLabel("Estaciones en orden:")
        self.lbl_estaciones_orden.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        form_layout.addWidget(self.lbl_estaciones_orden)

        self.lista_estaciones = QListWidget()
        self.lista_estaciones.setStyleSheet("""
            QListWidget {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
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
        #separador2 = QFrame()
        #separador2.setFrameShape(QFrame.Shape.HLine)
        #separador2.setStyleSheet("color: #eee;")
        #form_layout.addWidget(separador2)

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
        self.lbl_imagen_ruta.setStyleSheet("font-size: 13px; color: white;")
        form_layout.addWidget(self.btn_seleccionar_imagen)
        form_layout.addWidget(self.lbl_imagen_ruta)

        # Separador
        separador3 = QFrame()
        separador3.setFrameShape(QFrame.Shape.HLine)
        separador3.setStyleSheet("color: #eee;")
        form_layout.addWidget(separador3)

        # Crear nueva estacion
        self.lbl_crear_estacion = QLabel("Crear nueva estación:")
        self.lbl_crear_estacion.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        form_layout.addWidget(self.lbl_crear_estacion)

        self.input_nueva_estacion = QLineEdit()
        self.input_nueva_estacion.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
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
        #self.btn_cancelar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #e74c3c;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #        font-weight: bold;
        #    }
        #    QPushButton:hover {
        #        background-color: #c0392b;
        #    }
        #""")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
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

        # Botón Consultar
        self.btn_consultar = QPushButton("Consultar")
        #self.btn_consultar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #3498db;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #        font-weight: bold;
        #    }
        #    QPushButton:hover {
        #        background-color: #2980b9;
        #    }
        #""")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
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

        # Botón Actualizar (en lugar de Confirmar)
        self.btn_confirmar = QPushButton("Actualizar")
        #self.btn_confirmar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #        font-weight: bold;
        #    }
        #    QPushButton:hover {
        #        background-color: #27ae60;
        #    }
        #""")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
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
                self.logger.warning("Estación no encontrada al cargar ruta: %s", nombre)


    def cargar_estaciones_existentes(self):
        try:
            rows = self.db.fetch_all(
                "SELECT ID_ESTACION, NOMBRE FROM ESTACION ORDER BY NOMBRE",
                None,
            )
            self.estaciones = rows or []
            self.combo_estaciones.clear()
            for id_estacion, nombre in self.estaciones:
                self.combo_estaciones.addItem(nombre, id_estacion)
        except Exception as e:
            self.logger.exception("Error al cargar estaciones")
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
            existe = self.db.fetch_one(
                "SELECT 1 FROM ESTACION WHERE UPPER(NOMBRE) = :nombre",
                {"nombre": nombre.upper()},
            )
            if existe:
                QMessageBox.information(self, "Duplicado", f"La estación '{nombre}' ya existe.")
                return

            nuevo_id_row = self.db.fetch_one("SELECT NVL(MAX(ID_ESTACION), 0) + 1 AS ID FROM ESTACION", None)
            nuevo_id = nuevo_id_row[0] if nuevo_id_row else 1
            self.db.execute_query(
                "INSERT INTO ESTACION (ID_ESTACION, NOMBRE) VALUES (:id, :nombre)",
                {"id": nuevo_id, "nombre": nombre},
            )
            QMessageBox.information(self, "Éxito", f"Estación '{nombre}' agregada.")
            self.input_nueva_estacion.clear()
            self.cargar_estaciones_existentes()
        except Exception as e:
            self.logger.exception("Error al crear estación")
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
            # 1) Buscar otra ruta (distinto ID) con exactamente la misma secuencia de estaciones
            query = (
                "SELECT ID_RUTA FROM RUTA WHERE ID_RUTA IN ("
                "    SELECT ID_RUTA FROM RUTA_DETALLE GROUP BY ID_RUTA HAVING COUNT(*) = :count_est"
                ") AND ID_RUTA <> :id_actual"
            )
            posibles = self.db.fetch_all(
                query,
                {"count_est": len(self.estaciones_agregadas), "id_actual": self.id_ruta_a_editar},
            ) or []

            propuesta_ids = [e[0] for e in self.estaciones_agregadas]
            for (id_ruta,) in posibles:
                ids_rows = self.db.fetch_all(
                    """
                        SELECT ID_ESTACION
                        FROM RUTA_DETALLE
                        WHERE ID_RUTA = :id_ruta
                        ORDER BY ORDEN
                    """,
                    {"id_ruta": id_ruta},
                ) or []
                ids = [row[0] for row in ids_rows]
                if ids == propuesta_ids:
                    QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                    return

            # 2) Comparar contra la propia ruta actual: si el orden es idéntico
            actuales_rows = self.db.fetch_all(
                "SELECT ID_ESTACION FROM RUTA_DETALLE WHERE ID_RUTA = :id ORDER BY ORDEN",
                {"id": self.id_ruta_a_editar},
            ) or []
            actuales_ids = [r[0] for r in actuales_rows]

            if propuesta_ids == actuales_ids:
                # Si solo varía la duración, informar de ese cambio
                duracion_nueva = int(self.input_duracion.text().strip())
                dur_actual_row = self.db.fetch_one(
                    "SELECT DURACION_ESTIMADA FROM RUTA WHERE ID_RUTA = :id",
                    {"id": self.id_ruta_a_editar},
                )
                duracion_actual = int(dur_actual_row[0]) if dur_actual_row and dur_actual_row[0] is not None else None
                if duracion_actual is not None and duracion_actual != duracion_nueva:
                    QMessageBox.information(
                        self,
                        "Resultado",
                        f"La ruta es idéntica en estaciones; se actualizaría la duración de {duracion_actual} a {duracion_nueva}.",
                    )
                    return
                # Si no cambia la duración, realmente no hay cambios que aplicar
                QMessageBox.information(self, "Resultado", "La ruta es idéntica; no hay cambios por aplicar.")
                return

            # 3) Si el orden propuesto es diferente al actual y no hay duplicados externos, está disponible
            QMessageBox.information(self, "Resultado", "La ruta no existe, puedes usarla.")
        except Exception as e:
            self.logger.exception("Error en consulta de duplicados de ruta (editar)")
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
                # Verifica si ya existe la misma ruta mediante cantidad de estaciones
                # y orden de estaciones
                query = (
                    "SELECT ID_RUTA FROM RUTA WHERE ID_RUTA IN ("
                    "    SELECT ID_RUTA FROM RUTA_DETALLE GROUP BY ID_RUTA HAVING COUNT(*) = :count_est"
                    ") AND ID_RUTA <> :id_actual"
                )
                posibles = self.db.fetch_all(
                    query,
                    {"count_est": len(self.estaciones_agregadas), "id_actual": self.id_ruta_a_editar},
                ) or []
                for (id_ruta,) in posibles:
                    ids_rows = self.db.fetch_all(
                        """
                            SELECT ID_ESTACION
                            FROM RUTA_DETALLE
                            WHERE ID_RUTA = :id_ruta
                            ORDER BY ORDEN
                        """,
                        {"id_ruta": id_ruta},
                    ) or []
                    ids = [row[0] for row in ids_rows]
                    if ids == [e[0] for e in self.estaciones_agregadas]:
                        QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                        return
                # En este punto no hay otra ruta idéntica. Comprobar si la ruta propuesta es idéntica
                # a la misma ruta actual (mismo ID) y solo cambia la duración.
                duracion_int = int(duracion)
                propuesta_ids = [e[0] for e in self.estaciones_agregadas]
                actuales_rows = self.db.fetch_all(
                    "SELECT ID_ESTACION FROM RUTA_DETALLE WHERE ID_RUTA = :id ORDER BY ORDEN",
                    {"id": self.id_ruta_a_editar},
                ) or []
                actuales_ids = [r[0] for r in actuales_rows]
                dur_actual_row = self.db.fetch_one(
                    "SELECT DURACION_ESTIMADA FROM RUTA WHERE ID_RUTA = :id",
                    {"id": self.id_ruta_a_editar},
                )
                dur_actual = int(dur_actual_row[0]) if dur_actual_row and dur_actual_row[0] is not None else None

                if propuesta_ids == actuales_ids:
                    # Si también la duración es igual, no hacer nada y avisar
                    if dur_actual == duracion_int:
                        QMessageBox.information(self, "Resultado", "Una ruta idéntica ya existe.")
                        return
                    # Solo actualizar duración (y opcionalmente imagen) y registrar historial
                    self.db.execute_query(
                        """
                            INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_RUTA, FECHA_REGISTRO)
                            VALUES (HISTORIAL_SEQ.NEXTVAL, :info, :usuario, :id_ruta, SYSDATE)
                        """,
                        {"info": self.ruta_anterior, "usuario": self.username, "id_ruta": self.id_ruta_a_editar},
                    )
                    if self.ruta_imagen:
                        try:
                            with open(self.ruta_imagen, "rb") as f:
                                imagen_data = f.read()
                            self.db.execute_query(
                                "UPDATE RUTA SET DURACION_ESTIMADA = :dur, IMAGEN = :img WHERE ID_RUTA = :id",
                                {"dur": duracion_int, "img": imagen_data, "id": self.id_ruta_a_editar},
                            )
                        except Exception:
                            self.logger.exception("No se pudo leer la imagen seleccionada para actualizar la ruta")
                            QMessageBox.warning(self, "Imagen", "No se pudo leer la imagen seleccionada. Se actualizará sin imagen.")
                            self.db.execute_query(
                                "UPDATE RUTA SET DURACION_ESTIMADA = :dur WHERE ID_RUTA = :id",
                                {"dur": duracion_int, "id": self.id_ruta_a_editar},
                            )
                    else:
                        self.db.execute_query(
                            "UPDATE RUTA SET DURACION_ESTIMADA = :dur WHERE ID_RUTA = :id",
                            {"dur": duracion_int, "id": self.id_ruta_a_editar},
                        )
                    # Emitir señales solo si existen
                    if hasattr(self.db, "event_manager") and getattr(self.db.event_manager, "update_triggered", None):
                        self.db.event_manager.update_triggered.emit()
                    if hasattr(self, "asignacion_exitosa"):
                        try:
                            self.asignacion_exitosa.emit()
                        except Exception:
                            pass
                    QMessageBox.information(self, "Éxito", "Ruta actualizada correctamente.")
                    self.cancelar()
                    return

                # Ruta propuesta distinta a la actual: registrar historial, actualizar ruta y reemplazar detalles
                self.db.execute_query(
                    """
                        INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_RUTA, FECHA_REGISTRO)
                        VALUES (HISTORIAL_SEQ.NEXTVAL, :info, :usuario, :id_ruta, SYSDATE)
                    """,
                    {"info": self.ruta_anterior, "usuario": self.username, "id_ruta": self.id_ruta_a_editar},
                )
                if self.ruta_imagen:
                    try:
                        with open(self.ruta_imagen, "rb") as f:
                            imagen_data = f.read()
                        self.db.execute_query(
                            "UPDATE RUTA SET DURACION_ESTIMADA = :dur, IMAGEN = :img WHERE ID_RUTA = :id",
                            {"dur": duracion_int, "img": imagen_data, "id": self.id_ruta_a_editar},
                        )
                    except Exception:
                        self.logger.exception("No se pudo leer la imagen seleccionada para actualizar la ruta")
                        QMessageBox.warning(self, "Imagen", "No se pudo leer la imagen seleccionada. Se actualizará sin imagen.")
                        self.db.execute_query(
                            "UPDATE RUTA SET DURACION_ESTIMADA = :dur WHERE ID_RUTA = :id",
                            {"dur": duracion_int, "id": self.id_ruta_a_editar},
                        )
                else:
                    self.db.execute_query(
                        "UPDATE RUTA SET DURACION_ESTIMADA = :dur WHERE ID_RUTA = :id",
                        {"dur": duracion_int, "id": self.id_ruta_a_editar},
                    )
                self.db.execute_query(
                    "DELETE FROM RUTA_DETALLE WHERE ID_RUTA = :id",
                    {"id": self.id_ruta_a_editar},
                )
                for orden, (id_estacion, _) in enumerate(self.estaciones_agregadas, start=1):
                    id_det_row = self.db.fetch_one("SELECT NVL(MAX(ID_RUTA_DETALLE), 0) + 1 AS ID FROM RUTA_DETALLE", None)
                    id_detalle = id_det_row[0] if id_det_row else 1
                    self.db.execute_query(
                        """
                            INSERT INTO RUTA_DETALLE (ID_RUTA_DETALLE, ID_RUTA, ID_ESTACION)
                            VALUES (:id_det, :id_ruta, :id_est)
                        """,
                        {"id_det": id_detalle, "id_ruta": self.id_ruta_a_editar, "id_est": id_estacion},
                    )
                if hasattr(self.db, "event_manager") and getattr(self.db.event_manager, "update_triggered", None):
                    self.db.event_manager.update_triggered.emit()
                if hasattr(self, "asignacion_exitosa"):
                    try:
                        self.asignacion_exitosa.emit()
                    except Exception:
                        pass
                QMessageBox.information(self, "Éxito", f"Ruta actualizada correctamente.")
                self.cancelar()
        except Exception as e:
            self.logger.exception("Error al actualizar ruta")
            QMessageBox.critical(self, "Error", str(e))
