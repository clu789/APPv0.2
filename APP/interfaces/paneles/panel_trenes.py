from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QComboBox, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class InterfazAgregarTren(QWidget):
    """Panel para agregar un nuevo tren."""

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
        titulo = QLabel("Agregar Nuevo Tren")
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
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        # Campo: Nombre
        lbl_nombre = QLabel("Nombre del Tren:")
        lbl_nombre.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.input_nombre)

        # Campo: Capacidad
        lbl_capacidad = QLabel("Capacidad:")
        lbl_capacidad.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_capacidad = QLineEdit()
        self.input_capacidad.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        form_layout.addWidget(lbl_capacidad)
        form_layout.addWidget(self.input_capacidad)

        # Campo: Estado
        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Activo", "En mantenimiento", "Fuera de servicio"])
        self.estado_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        form_layout.addWidget(lbl_estado)
        form_layout.addWidget(self.estado_combo)

        layout.addWidget(form_container)

        # Contenedor para botones
        botones_container = QWidget()
        botones_layout = QHBoxLayout(botones_container)
        botones_layout.setContentsMargins(0, 10, 0, 0)
        botones_layout.setSpacing(15)

        # Botones con estilos
        self.btn_cancelar = QPushButton("Cancelar")
        #self.btn_cancelar.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #e74c3c;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #    }
        #    QPushButton:hover {
        #        background-color: #c0392b;
        #    }
        #""")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 15px;
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

        self.btn_consultar = QPushButton("Consultar")
        #self.btn_consultar.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #3498db;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #    }
        #    QPushButton:hover {
        #        background-color: #2980b9;
        #    }
        #""")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
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

        self.btn_confirmar = QPushButton("Confirmar")
        #self.btn_confirmar.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #    }
        #    QPushButton:hover {
        #        background-color: #27ae60;
        #    }
        #""")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
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

        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)

        layout.addWidget(botones_container)
        layout.addStretch()

        self.setLayout(layout)

        # Conexiones (se mantienen exactamente igual)
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.verificar_nombre)
        self.btn_confirmar.clicked.connect(self.insertar_tren)

    def cancelar(self) -> None:
        self.input_nombre.clear()
        self.input_capacidad.clear()
        self.estado_combo.setCurrentIndex(0)

    def verificar_nombre(self) -> None:
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingresa un nombre.")
            return
        try:
            resultado = self.db.fetch_one(
                "SELECT COUNT(*) FROM TREN WHERE UPPER(NOMBRE) = UPPER(:nombre)",
                {"nombre": nombre},
            )
        except Exception as e:
            logger.exception("Error verificando nombre de tren: %s", e)
            QMessageBox.critical(self, "Error", "No se pudo verificar el nombre del tren.")
            return
        if resultado and resultado[0] > 0:
            QMessageBox.warning(self, "Nombre duplicado", "Ya existe un tren con ese nombre.")
        else:
            QMessageBox.information(self, "Disponible", "El nombre está disponible.")

    def insertar_tren(self) -> None:
        nombre = self.input_nombre.text().strip()
        try:
            capacidad = int(self.input_capacidad.text())
            if capacidad <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Error", "La capacidad debe ser un número mayor a 0.")
            return
        estado = self.estado_combo.currentText()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        
        try:
            # Verificación de duplicado (case-insensitive)
            dup = self.db.fetch_one(
                "SELECT 1 FROM TREN WHERE UPPER(NOMBRE) = UPPER(:nombre)",
                {"nombre": nombre},
            )
            if dup:
                QMessageBox.warning(self, "Nombre duplicado", "Ya existe un tren con ese nombre.")
                return

            row = self.db.fetch_one("SELECT NVL(MAX(ID_TREN), 0) + 1 FROM TREN")
            if not row:
                logger.error("No se pudo obtener el siguiente ID_TREN")
                QMessageBox.critical(self, "Error", "No se pudo obtener un nuevo ID para el tren.")
                return
            id_tren = row[0]

            ok = self.db.execute_query(
                "INSERT INTO TREN (ID_TREN, NOMBRE, CAPACIDAD, ESTADO) "
                "VALUES (:id_tren, :nombre, :capacidad, UPPER(:estado))",
                {"id_tren": id_tren, "nombre": nombre, "capacidad": capacidad, "estado": estado},
            )
            if ok:
                QMessageBox.information(self, "Éxito", "Tren agregado correctamente.")
                # Emitir la señal update_triggered con guardas
                try:
                    if getattr(self.db, "event_manager", None) and hasattr(self.db.event_manager, "update_triggered"):
                        self.db.event_manager.update_triggered.emit()
                except Exception as em:
                    logger.warning("Fallo emitiendo update_triggered: %s", em)
                self.cancelar()
            else:
                logger.error("execute_query devolvió False al insertar tren")
                QMessageBox.critical(self, "Error", "No se pudo agregar el tren.")
        except Exception as e:
            # Errores no esperados (los helpers suelen capturar los de DB)
            logger.exception("Error al insertar tren: %s", e)
            QMessageBox.critical(self, "Error", "Ocurrió un error al agregar el tren.")

class InterfazEditarTren(QWidget):
    """Panel para editar un tren existente."""

    def __init__(self, main_window, db) -> None:
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.id_tren: Optional[int] = None  # Se llena con el ID del tren seleccionado
        self.initUI()

    def initUI(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
    
        # Título del panel
        titulo = QLabel("Editar Tren Existente")
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
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)
    
        # Campo: Nombre
        lbl_nombre = QLabel("Nombre del Tren:")
        lbl_nombre.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.input_nombre)
    
        # Campo: Capacidad
        lbl_capacidad = QLabel("Capacidad:")
        lbl_capacidad.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_capacidad = QLineEdit()
        self.input_capacidad.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        form_layout.addWidget(lbl_capacidad)
        form_layout.addWidget(self.input_capacidad)
    
        # Campo: Estado
        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Activo", "En mantenimiento", "Fuera de servicio"])
        self.estado_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        form_layout.addWidget(lbl_estado)
        form_layout.addWidget(self.estado_combo)
    
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
        #        padding: 8px 15px;
        #        background-color: #e74c3c;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #    }
        #    QPushButton:hover {
        #        background-color: #c0392b;
        #    }
        #""")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 15px;
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
    
        self.btn_consultar = QPushButton("Consultar")
        #self.btn_consultar.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #3498db;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #    }
        #    QPushButton:hover {
        #        background-color: #2980b9;
        #    }
        #""")
        self.btn_consultar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
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
    
        self.btn_confirmar = QPushButton("Confirmar")
        #self.btn_confirmar.setStyleSheet("""
        #    QPushButton {
        #        padding: 8px 15px;
        #        background-color: #2ecc71;
        #        color: white;
        #        border: none;
        #        border-radius: 4px;
        #        min-width: 100px;
        #    }
        #    QPushButton:hover {
        #        background-color: #27ae60;
        #    }
        #""")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
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
    
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)
    
        layout.addWidget(botones_container)
        layout.addStretch()
    
        self.setLayout(layout)
    
        # Conexiones se mantienen exactamente igual
        self.btn_consultar.clicked.connect(self.verificar_nombre)
        self.btn_confirmar.clicked.connect(self.actualizar_tren)

    def cancelar(self) -> None:
        self.input_nombre.clear()
        self.input_capacidad.clear()
        self.estado_combo.setCurrentIndex(0)

    def cargar_datos(self, id_tren: int, nombre: str, capacidad: int, estado: str) -> None:
        """Carga los datos del tren seleccionado para editarlos"""
        self.id_tren = id_tren
        self.input_nombre.setText(nombre)
        self.input_capacidad.setText(str(capacidad))
        self.estado_combo.setCurrentText(estado)

    def verificar_nombre(self) -> None:
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingresa un nombre.")
            return
        try:
            resultado = self.db.fetch_one(
                "SELECT COUNT(*) FROM TREN WHERE UPPER(NOMBRE) = UPPER(:nombre) AND ID_TREN != :id_tren",
                {"nombre": nombre, "id_tren": self.id_tren},
            )
        except Exception as e:
            logger.exception("Error verificando nombre de tren (edición): %s", e)
            QMessageBox.critical(self, "Error", "No se pudo verificar el nombre del tren.")
            return
        if resultado and resultado[0] > 0:
            QMessageBox.warning(self, "Nombre duplicado", "Ya existe otro tren con ese nombre.")
        else:
            QMessageBox.information(self, "Disponible", "El nombre está disponible.")

    def actualizar_tren(self) -> None:
        if self.id_tren is None:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún tren.")
            return

        nombre = self.input_nombre.text().strip()
        try:
            capacidad = int(self.input_capacidad.text())
            if capacidad <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Error", "La capacidad debe ser un número mayor a 0.")
            return
        estado = self.estado_combo.currentText()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        
        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar cambios")
        confirmacion.setText(f"¿Estás seguro de que deseas modificar el tren #{self.id_tren}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
        
        try:
            if confirmacion.exec() == 2:
                # Verificación de duplicado (case-insensitive) excluyendo el propio ID
                dup = self.db.fetch_one(
                    "SELECT 1 FROM TREN WHERE UPPER(NOMBRE) = UPPER(:nombre) AND ID_TREN != :id_tren",
                    {"nombre": nombre, "id_tren": self.id_tren},
                )
                if dup:
                    QMessageBox.warning(self, "Nombre duplicado", "Ya existe otro tren con ese nombre.")
                    return

                ok = self.db.execute_query(
                    "UPDATE TREN SET NOMBRE = :nombre, CAPACIDAD = :capacidad, ESTADO = UPPER(:estado) "
                    "WHERE ID_TREN = :id_tren",
                    {"nombre": nombre, "capacidad": capacidad, "estado": estado, "id_tren": self.id_tren},
                )
                if ok:
                    QMessageBox.information(self, "Éxito", "Tren actualizado correctamente.")
                    # Emitir la señal update_triggered con guardas
                    try:
                        if getattr(self.db, "event_manager", None) and hasattr(self.db.event_manager, "update_triggered"):
                            self.db.event_manager.update_triggered.emit()
                    except Exception as em:
                        logger.warning("Fallo emitiendo update_triggered: %s", em)
                    self.cancelar()
                else:
                    logger.error("execute_query devolvió False al actualizar tren")
                    QMessageBox.critical(self, "Error", "No se pudo actualizar el tren.")
        except Exception as e:
            logger.exception("Error al actualizar tren: %s", e)
            QMessageBox.critical(self, "Error", "Ocurrió un error al actualizar el tren.")
