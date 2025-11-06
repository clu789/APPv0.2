from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

class InterfazAgregarHorario(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self._logger = logging.getLogger(__name__)

        self.init_ui()

    def init_ui(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
    
        # Título del panel
        titulo = QLabel("Agregar Nuevo Horario")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 5px 0;
                margin-bottom: 10px;
                color: white;
            }
        """)
        layout.addWidget(titulo)
    
        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)
    
        # Campo Hora de Salida
        self.lbl_salida = QLabel("Hora de salida programada (HH:MM):")
        self.lbl_salida.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc")
        self.input_salida = QLineEdit()
        self.input_salida.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        self.input_salida.setPlaceholderText("Ejemplo: 08:30")
        form_layout.addWidget(self.lbl_salida)
        form_layout.addWidget(self.input_salida)
    
        # Campo Hora de Llegada
        self.lbl_llegada = QLabel("Hora de llegada programada (HH:MM):")
        self.lbl_llegada.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_llegada = QLineEdit()
        self.input_llegada.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        self.input_llegada.setPlaceholderText("Ejemplo: 10:15")
        form_layout.addWidget(self.lbl_llegada)
        form_layout.addWidget(self.input_llegada)
    
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

    def cancelar(self):
        self.input_salida.clear()
        self.input_llegada.clear()

    def validar_horas(self, salida, llegada):
        try:
            from datetime import datetime

            hora_salida = datetime.strptime(salida, "%H:%M")
            hora_llegada = datetime.strptime(llegada, "%H:%M")

            if hora_salida >= hora_llegada:
                return False, "La hora de salida debe ser menor que la de llegada."

            return True, ""
        except ValueError:
            return False, "Formato de hora incorrecto. Usa el formato HH:MM."

    def consultar(self):
        salida = self.input_salida.text().strip()
        llegada = self.input_llegada.text().strip()

        if not salida or not llegada:
            QMessageBox.warning(self, "Campos vacíos", "Por favor, llena ambos campos.")
            return
        
        es_valido, mensaje = self.validar_horas(salida, llegada)
        if not es_valido:
            QMessageBox.warning(self, "Hora inválida", mensaje)
            return

        try:
            self._logger.debug("Consultando disponibilidad de horario %s -> %s", salida, llegada)
            row = self.db.fetch_one(
                """
                SELECT CASE WHEN EXISTS (
                        SELECT 1 FROM HORARIO
                        WHERE HORA_SALIDA_PROGRAMADA = TO_DATE(:salida, 'HH24:MI:SS')
                          AND HORA_LLEGADA_PROGRAMADA = TO_DATE(:llegada, 'HH24:MI:SS')
                ) THEN 1 ELSE 0 END AS existe
                FROM DUAL
                """,
                {"salida": salida + ":00", "llegada": llegada + ":00"},
            )
            count = int(row[0]) if row else 0
            if count > 0:
                QMessageBox.information(self, "Resultado", "El horario ya existe en la base de datos.")
            else:
                QMessageBox.information(self, "Resultado", "El horario está disponible.")
        except Exception as e:
            self._logger.error("Error al consultar horario: %s", e)
            QMessageBox.critical(self, "Error al consultar", str(e))

    def confirmar(self):
        salida = self.input_salida.text().strip()
        llegada = self.input_llegada.text().strip()
    
        if not salida or not llegada:
            QMessageBox.warning(self, "Campos vacíos", "Por favor, llena ambos campos.")
            return
    
        es_valido, mensaje = self.validar_horas(salida, llegada)
        if not es_valido:
            QMessageBox.warning(self, "Hora inválida", mensaje)
            return
    
        try:
            # Validar duplicado
            row = self.db.fetch_one(
                """
                SELECT CASE WHEN EXISTS (
                        SELECT 1 FROM HORARIO
                        WHERE HORA_SALIDA_PROGRAMADA = TO_DATE(:salida, 'HH24:MI:SS')
                          AND HORA_LLEGADA_PROGRAMADA = TO_DATE(:llegada, 'HH24:MI:SS')
                ) THEN 1 ELSE 0 END AS existe
                FROM DUAL
                """,
                {"salida": salida + ":00", "llegada": llegada + ":00"},
            )
            count = int(row[0]) if row else 0
            if count > 0:
                QMessageBox.information(self, "Resultado", "El horario ya existe en la base de datos.")
                self.cancelar()
                return

            # Obtener nuevo ID (no atómico, mantenemos estrategia actual)
            row_id = self.db.fetch_one("SELECT NVL(MAX(ID_HORARIO), 0) + 1 FROM HORARIO")
            nuevo_id = row_id[0] if row_id else None
            if nuevo_id is None:
                raise RuntimeError("No se pudo generar un nuevo ID_HORARIO")

            # Insertar
            self.db.execute_query(
                """
                INSERT INTO HORARIO (ID_HORARIO, HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA)
                VALUES (:id_horario, TO_DATE(:salida, 'HH24:MI:SS'), TO_DATE(:llegada, 'HH24:MI:SS'))
                """,
                {"id_horario": nuevo_id, "salida": salida + ":00", "llegada": llegada + ":00"},
            )

            # Emitir señal solo tras éxito
            if hasattr(self.db, 'event_manager') and self.db.event_manager and hasattr(self.db.event_manager, 'update_triggered'):
                try:
                    self.db.event_manager.update_triggered.emit()
                except Exception:
                    pass
            QMessageBox.information(self, "Éxito", f"Horario agregado con ID {nuevo_id}.")
            self._logger.info("Horario agregado id=%s (%s -> %s)", nuevo_id, salida, llegada)
            self.cancelar()
        except Exception as e:
            self._logger.error("Error al insertar horario: %s", e)
            QMessageBox.critical(self, "Error al insertar", str(e))
            
class InterfazEditarHorario(QWidget):
    asignacion_exitosa = pyqtSignal() 
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db
        self._logger = logging.getLogger(__name__)
        self.id_horario_a_editar = None  # Se usará para almacenar el ID del horario seleccionado

        self.init_ui()

    def init_ui(self):
        # Layout principal con márgenes y espaciado
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título del panel
        titulo = QLabel("Editar Horario Existente")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 5px 0;
                margin-bottom: 10px;
                color: white;
            }
        """)
        layout.addWidget(titulo)

        # Mensaje informativo
        self.lbl_info = QLabel("Selecciona el horario a editar de la lista superior.")
        self.lbl_info.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: white;
                padding: 5px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.lbl_info)

        # Contenedor para el formulario
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        # Campo Hora de Salida
        self.lbl_salida = QLabel("Hora de salida programada (HH:MM):")
        self.lbl_salida.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc")
        self.input_salida = QLineEdit()
        self.input_salida.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        self.input_salida.setPlaceholderText("Ejemplo: 08:30")
        form_layout.addWidget(self.lbl_salida)
        form_layout.addWidget(self.input_salida)

        # Campo Hora de Llegada
        self.lbl_llegada = QLabel("Hora de llegada programada (HH:MM):")
        self.lbl_llegada.setStyleSheet("font-weight: bold; font-size: 14px; color: #197fbc;")
        self.input_llegada = QLineEdit()
        self.input_llegada.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                color: white;
            }
        """)
        self.input_llegada.setPlaceholderText("Ejemplo: 10:15")
        form_layout.addWidget(self.lbl_llegada)
        form_layout.addWidget(self.input_llegada)

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

    def cargar_horario(self, datos):
        self.id_horario_a_editar = datos["id"]
        self.input_salida.setText(datos["salida"][:5])
        self.input_llegada.setText(datos["llegada"][:5])
        self.horario_anterior = datos["salida"] + " - " + datos["llegada"]

    def cancelar(self):
        self.input_salida.clear()
        self.input_llegada.clear()

    def validar_horas(self, salida, llegada):
        try:
            from datetime import datetime

            hora_salida = datetime.strptime(salida, "%H:%M")
            hora_llegada = datetime.strptime(llegada, "%H:%M")

            if hora_salida >= hora_llegada:
                return False, "La hora de salida debe ser menor que la de llegada."

            return True, ""
        except ValueError:
            return False, "Formato de hora incorrecto. Usa el formato HH:MM."

    def consultar(self):
        salida = self.input_salida.text().strip()
        llegada = self.input_llegada.text().strip()

        if not salida or not llegada:
            QMessageBox.warning(self, "Campos vacíos", "Por favor, llena ambos campos.")
            return
        
        es_valido, mensaje = self.validar_horas(salida, llegada)
        if not es_valido:
            QMessageBox.warning(self, "Hora inválida", mensaje)
            return

        try:
            self._logger.debug("Consultando duplicado para actualización %s -> %s", salida, llegada)
            row = self.db.fetch_one(
                """
                SELECT CASE WHEN EXISTS (
                        SELECT 1 FROM HORARIO
                        WHERE HORA_SALIDA_PROGRAMADA = TO_DATE(:salida, 'HH24:MI:SS')
                          AND HORA_LLEGADA_PROGRAMADA = TO_DATE(:llegada, 'HH24:MI:SS')
                ) THEN 1 ELSE 0 END AS existe
                FROM DUAL
                """,
                {"salida": salida + ":00", "llegada": llegada + ":00"},
            )
            count = int(row[0]) if row else 0
            if count > 0:
                QMessageBox.information(self, "Resultado", "El horario ya existe en la base de datos.")
            else:
                QMessageBox.information(self, "Resultado", "El horario está disponible.")
        except Exception as e:
            self._logger.error("Error al consultar horario (edición): %s", e)
            QMessageBox.critical(self, "Error al consultar", str(e))

    def confirmar(self):
        salida = self.input_salida.text().strip()
        llegada = self.input_llegada.text().strip()
    
        if not salida or not llegada:
            QMessageBox.warning(self, "Campos vacíos", "Por favor, llena ambos campos.")
            return
    
        es_valido, mensaje = self.validar_horas(salida, llegada)
        if not es_valido:
            QMessageBox.warning(self, "Hora inválida", mensaje)
            return
        
        if self.id_horario_a_editar is None:
            QMessageBox.warning(self, "Error", "No se ha cargado ningún horario para editar.")
            return

        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar cambios")
        confirmacion.setText(f"¿Estás seguro de que deseas modificar el horario #{self.id_horario_a_editar}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)
        
        try:
            if confirmacion.exec() == 2:
                # Validar duplicado
                row = self.db.fetch_one(
                    """
                    SELECT CASE WHEN EXISTS (
                            SELECT 1 FROM HORARIO
                            WHERE HORA_SALIDA_PROGRAMADA = TO_DATE(:salida, 'HH24:MI:SS')
                              AND HORA_LLEGADA_PROGRAMADA = TO_DATE(:llegada, 'HH24:MI:SS')
                    ) THEN 1 ELSE 0 END AS existe
                    FROM DUAL
                    """,
                    {"salida": salida + ":00", "llegada": llegada + ":00"},
                )
                count = int(row[0]) if row else 0
                if count > 0:
                    QMessageBox.information(self, "Resultado", "El horario ya existe en la base de datos.")
                    return

                # Insertar en historial usando secuencia
                self.db.execute_query(
                    """
                    INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_HORARIO, FECHA_REGISTRO)
                    VALUES (HISTORIAL_SEQ.NEXTVAL, :info, :id_usuario, :id_horario, SYSDATE)
                    """,
                    {
                        "info": self.horario_anterior,
                        "id_usuario": self.username,
                        "id_horario": self.id_horario_a_editar,
                    },
                )

                # Actualizar horario
                self.db.execute_query(
                    """
                    UPDATE HORARIO
                    SET HORA_SALIDA_PROGRAMADA = TO_DATE(:salida, 'HH24:MI:SS'),
                        HORA_LLEGADA_PROGRAMADA = TO_DATE(:llegada, 'HH24:MI:SS')
                    WHERE ID_HORARIO = :id_horario
                    """,
                    {
                        "salida": salida + ":00",
                        "llegada": llegada + ":00",
                        "id_horario": self.id_horario_a_editar,
                    },
                )

                # Emitir señales solo tras éxito
                self.asignacion_exitosa.emit()
                if hasattr(self.db, 'event_manager') and self.db.event_manager and hasattr(self.db.event_manager, 'update_triggered'):
                    try:
                        self.db.event_manager.update_triggered.emit()
                    except Exception:
                        pass
                QMessageBox.information(self, "Éxito", "Horario actualizado correctamente.")
                self._logger.info(
                    "Horario actualizado id=%s (%s)", self.id_horario_a_editar, self.horario_anterior
                )
                self.cancelar()
        except Exception as e:
            self._logger.error("Error al actualizar horario id=%s: %s", self.id_horario_a_editar, e)
            QMessageBox.critical(self, "Error al actualizar", str(e))