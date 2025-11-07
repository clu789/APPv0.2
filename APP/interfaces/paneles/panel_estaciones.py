from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class InterfazAgregarEstacion(QWidget):
    """Panel para agregar una nueva estación."""

    def __init__(self, main_window, db) -> None:
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.initUI()

    def initUI(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título del panel
        titulo = QLabel("Agregar Nueva Estación")
        titulo.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            padding: 5px;
        """)
        layout.addWidget(titulo)

        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 20, 10, 20)  # Más espacio vertical
        form_layout.setSpacing(15)

        # Campo: Nombre
        lbl_nombre = QLabel("Nombre de la Estación:")
        lbl_nombre.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        self.input_nombre.setMinimumHeight(35)  # Altura aumentada
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.input_nombre)

        layout.addWidget(form_container)

        # Contenedor para botones
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 10, 0, 0)
        botones_layout.setSpacing(15)

        # Botones con estilos consistentes
        self.btn_cancelar = QPushButton("Cancelar")
        #self.btn_cancelar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #e74c3c;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 120px;
        #        font-size: 14px;
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
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
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

        self.btn_consultar = QPushButton("Consultar")
        #self.btn_consultar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #3498db;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 120px;
        #        font-size: 14px;
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
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
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

        self.btn_confirmar = QPushButton("Confirmar")
        #self.btn_confirmar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 120px;
        #        font-size: 14px;
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
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
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

        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)

        layout.addWidget(botones_container)
        layout.addStretch()

        self.setLayout(layout)

        # Conexiones se mantienen exactamente igual
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.verificar_nombre)
        self.btn_confirmar.clicked.connect(self.insertar_estacion)

    def cancelar(self) -> None:
        self.input_nombre.clear()

    def verificar_nombre(self) -> None:
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingresa un nombre.")
            return
        try:
            resultado = self.db.fetch_one(
                "SELECT COUNT(*) FROM ESTACION WHERE UPPER(NOMBRE) = UPPER(:nombre)",
                {"nombre": nombre},
            )
        except Exception as e:
            logger.exception("Error verificando nombre de estación: %s", e)
            QMessageBox.critical(self, "Error", "No se pudo verificar el nombre de la estación.")
            return
        if resultado and resultado[0] > 0:
            QMessageBox.warning(self, "Nombre duplicado", "Ya existe una estación con ese nombre.")
        else:
            QMessageBox.information(self, "Disponible", "El nombre está disponible.")

    def insertar_estacion(self) -> None:
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        
        try:
            # Verificación de duplicado (case-insensitive) antes de insertar
            dup = self.db.fetch_one(
                "SELECT 1 FROM ESTACION WHERE UPPER(NOMBRE) = UPPER(:nombre)",
                {"nombre": nombre},
            )
            if dup:
                QMessageBox.warning(self, "Nombre duplicado", "Ya existe una estación con ese nombre.")
                return

            row = self.db.fetch_one("SELECT NVL(MAX(ID_ESTACION), 0) + 1 FROM ESTACION")
            if not row:
                logger.error("No se pudo obtener el siguiente ID_ESTACION")
                QMessageBox.critical(self, "Error", "No se pudo generar un nuevo ID para la estación.")
                return
            id_estacion = row[0]

            ok = self.db.execute_query(
                "INSERT INTO ESTACION (ID_ESTACION, NOMBRE) VALUES (:id_estacion, :nombre)",
                {"id_estacion": id_estacion, "nombre": nombre},
            )
            if not ok:
                logger.error("execute_query devolvió False al insertar estación")
                QMessageBox.critical(self, "Error", "No se pudo agregar la estación.")
                return
            QMessageBox.information(self, "Éxito", "Estación agregado correctamente.")
            # Emitir la señal update_triggered
            try:
                if getattr(self.db, "event_manager", None) and hasattr(self.db.event_manager, "update_triggered"):
                    self.db.event_manager.update_triggered.emit()
            except Exception as em:
                logger.warning("Fallo emitiendo update_triggered: %s", em)
            self.cancelar()
        except Exception as e:
            logger.exception("Error al insertar estación: %s", e)
            QMessageBox.critical(self, "Error", "Ya existe una estación con ese nombre.")

class InterfazEditarEstacion(QWidget):
    """Panel para editar una estación existente."""

    def __init__(self, main_window, db) -> None:
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.id_estacion: Optional[int] = None  # Se asigna desde la tabla principal
        self.initUI()

    def initUI(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
    
        # Título del panel
        titulo = QLabel("Editar Estación Existente")
        titulo.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            padding: 5px;
        """)
        layout.addWidget(titulo)
    
        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 20, 10, 20)  # Más espacio vertical
        form_layout.setSpacing(15)
    
        # Campo: Nombre
        lbl_nombre = QLabel("Nombre de la Estación:")
        lbl_nombre.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        self.input_nombre.setMinimumHeight(35)  # Altura aumentada
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.input_nombre)
    
        layout.addWidget(form_container)
    
        # Contenedor para botones
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 10, 0, 0)
        botones_layout.setSpacing(15)
    
        # Botones con estilos consistentes
        self.btn_cancelar = QPushButton("Cancelar")
        #self.btn_cancelar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #e74c3c;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 120px;
        #        font-size: 14px;
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
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
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
    
        self.btn_consultar = QPushButton("Consultar")
        #self.btn_consultar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #3498db;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 120px;
        #        font-size: 14px;
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
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
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
    
        self.btn_confirmar = QPushButton("Confirmar")
        #self.btn_confirmar.setStyleSheet("""
        #    QPushButton {
        #        padding: 10px 20px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 120px;
        #        font-size: 14px;
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
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
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
    
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)
    
        layout.addWidget(botones_container)
        layout.addStretch()
    
        self.setLayout(layout)
    
        # Conexiones se mantienen exactamente igual
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.verificar_nombre)
        self.btn_confirmar.clicked.connect(self.actualizar_estacion)

    def cancelar(self) -> None:
        self.input_nombre.clear()

    def cargar_datos(self, id_estacion: int, nombre: str) -> None:
        """Carga los datos de la estación seleccionada"""
        self.id_estacion = id_estacion
        self.input_nombre.setText(nombre)

    def verificar_nombre(self) -> None:
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingresa un nombre.")
            return
        try:
            resultado = self.db.fetch_one(
                "SELECT COUNT(*) FROM ESTACION WHERE UPPER(NOMBRE) = UPPER(:nombre) AND ID_ESTACION != :id_estacion",
                {"nombre": nombre, "id_estacion": self.id_estacion},
            )
        except Exception as e:
            logger.exception("Error verificando nombre de estación (edición): %s", e)
            QMessageBox.critical(self, "Error", "No se pudo verificar el nombre de la estación.")
            return
        if resultado and resultado[0] > 0:
            QMessageBox.warning(self, "Nombre duplicado", "Ya existe otra estación con ese nombre.")
        else:
            QMessageBox.information(self, "Disponible", "El nombre está disponible.")

    def actualizar_estacion(self) -> None:
        if self.id_estacion is None:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ninguna estación.")
            return

        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar cambios")
        confirmacion.setText(f"¿Estás seguro de que deseas modificar la estación #{self.id_estacion}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
        
        try:
            if confirmacion.exec() == 2:
                # Verificación de duplicado (case-insensitive) excluyendo el propio ID antes de actualizar
                dup = self.db.fetch_one(
                    "SELECT 1 FROM ESTACION WHERE UPPER(NOMBRE) = UPPER(:nombre) AND ID_ESTACION != :id_estacion",
                    {"nombre": nombre, "id_estacion": self.id_estacion},
                )
                if dup:
                    QMessageBox.warning(self, "Nombre duplicado", "Ya existe otra estación con ese nombre.")
                    return

                ok = self.db.execute_query(
                    "UPDATE ESTACION SET NOMBRE = :nombre WHERE ID_ESTACION = :id_estacion",
                    {"nombre": nombre, "id_estacion": self.id_estacion},
                )
                if not ok:
                    logger.error("execute_query devolvió False al actualizar estación")
                    QMessageBox.critical(self, "Error", "No se pudo actualizar la estación.")
                    return
                QMessageBox.information(self, "Éxito", "Estación actualizada correctamente.")
                # Emitir la señal update_triggered
                try:
                    if getattr(self.db, "event_manager", None) and hasattr(self.db.event_manager, "update_triggered"):
                        self.db.event_manager.update_triggered.emit()
                except Exception as em:
                    logger.warning("Fallo emitiendo update_triggered: %s", em)
                self.cancelar()
        except Exception as e:
            logger.exception("Error al actualizar estación: %s", e)
            QMessageBox.critical(self, "Error", "Ya existe una estación con ese nombre.")
