from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt

class InterfazAgregarHorario(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Etiquetas y campos de entrada
        self.lbl_salida = QLabel("Hora de salida programada (HH:MM):")
        self.input_salida = QLineEdit()
        self.lbl_llegada = QLabel("Hora de llegada programada (HH:MM):")
        self.input_llegada = QLineEdit()

        layout.addWidget(self.lbl_salida)
        layout.addWidget(self.input_salida)
        layout.addWidget(self.lbl_llegada)
        layout.addWidget(self.input_llegada)

        # Botones
        botones_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_consultar = QPushButton("Consultar")
        self.btn_confirmar = QPushButton("Confirmar")

        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.consultar)
        self.btn_confirmar.clicked.connect(self.confirmar)

        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)

        layout.addLayout(botones_layout)
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
            cursor = self.db.connection.cursor()
            query = """
                SELECT COUNT(*) FROM HORARIO
                WHERE HORA_SALIDA_PROGRAMADA = TO_DATE(:1, 'HH24:MI:SS')
                  AND HORA_LLEGADA_PROGRAMADA = TO_DATE(:2, 'HH24:MI:SS')
            """
            cursor.execute(query, (salida + ":00", llegada + ":00"))
            count = cursor.fetchone()[0]

            if count > 0:
                QMessageBox.information(self, "Resultado", "El horario ya existe en la base de datos.")
            else:
                QMessageBox.information(self, "Resultado", "El horario está disponible.")
        except Exception as e:
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
            cursor = self.db.connection.cursor()
            query = """
                SELECT COUNT(*) FROM HORARIO
                WHERE HORA_SALIDA_PROGRAMADA = TO_DATE(:1, 'HH24:MI:SS')
                  AND HORA_LLEGADA_PROGRAMADA = TO_DATE(:2, 'HH24:MI:SS')
            """
            cursor.execute(query, (salida + ":00", llegada + ":00"))
            count = cursor.fetchone()[0]
            if count > 0:
                QMessageBox.information(self, "Resultado", "El horario ya existe en la base de datos.")
                return
            cursor.execute("SELECT NVL(MAX(ID_HORARIO), 0) + 1 FROM HORARIO")
            nuevo_id = cursor.fetchone()[0]
    
            insert = f"""
                INSERT INTO HORARIO (ID_HORARIO, HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA)
                VALUES (:1, TO_DATE(:2, 'HH24:MI:SS'), TO_DATE(:3, 'HH24:MI:SS'))
            """
            # Se agregan segundos ':00' para cumplir con HH24:MI:SS
            cursor.execute(insert, (nuevo_id, salida + ":00", llegada + ":00"))
            self.db.connection.commit()
    
            QMessageBox.information(self, "Éxito", f"Horario agregado con ID {nuevo_id}.")
            self.cancelar()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Error al insertar", str(e))
            
class InterfazEditarHorario(QWidget):
    def __init__(self, main_window, db, username):
        super().__init__()
        self.username = username
        self.main_window = main_window
        self.db = db
        self.id_horario_a_editar = None  # Se usará para almacenar el ID del horario seleccionado

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Etiquetas y campos de entrada
        self.lbl_info = QLabel("Selecciona el horario a editar de la lista superior.")
        self.lbl_salida = QLabel("Hora de salida programada (HH:MM):")
        self.input_salida = QLineEdit()
        self.lbl_llegada = QLabel("Hora de llegada programada (HH:MM):")
        self.input_llegada = QLineEdit()

        layout.addWidget(self.lbl_info)
        layout.addWidget(self.lbl_salida)
        layout.addWidget(self.input_salida)
        layout.addWidget(self.lbl_llegada)
        layout.addWidget(self.input_llegada)

        # Botones
        botones_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_consultar = QPushButton("Consultar")
        self.btn_confirmar = QPushButton("Actualizar")

        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_consultar.clicked.connect(self.consultar)
        self.btn_confirmar.clicked.connect(self.confirmar)

        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_consultar)
        botones_layout.addWidget(self.btn_confirmar)

        layout.addLayout(botones_layout)
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
            cursor = self.db.connection.cursor()
            query = """
                SELECT COUNT(*) FROM HORARIO
                WHERE HORA_SALIDA_PROGRAMADA = TO_DATE(:1, 'HH24:MI:SS')
                  AND HORA_LLEGADA_PROGRAMADA = TO_DATE(:2, 'HH24:MI:SS')
            """
            cursor.execute(query, (salida + ":00", llegada + ":00"))
            count = cursor.fetchone()[0]

            if count > 0:
                QMessageBox.information(self, "Resultado", "El horario ya existe en la base de datos.")
            else:
                QMessageBox.information(self, "Resultado", "El horario está disponible.")
        except Exception as e:
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
    
        try:
            cursor = self.db.connection.cursor()
            query = """
                SELECT COUNT(*) FROM HORARIO
                WHERE HORA_SALIDA_PROGRAMADA = TO_DATE(:1, 'HH24:MI:SS')
                  AND HORA_LLEGADA_PROGRAMADA = TO_DATE(:2, 'HH24:MI:SS')
            """
            cursor.execute(query, (salida + ":00", llegada + ":00"))
            count = cursor.fetchone()[0]
            if count > 0:
                QMessageBox.information(self, "Resultado", "El horario ya existe en la base de datos.")
                return
            
            cursor.execute("SELECT NVL(MAX(ID_HISTORIAL), 0) + 1 FROM HISTORIAL")
            nuevo_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO HISTORIAL (ID_HISTORIAL, INFORMACION, ID_USUARIO, ID_HORARIO, FECHA_REGISTRO)
                VALUES (:1, :2, :3, :4, SYSDATE)
            """, (nuevo_id, self.horario_anterior, self.username, self.id_horario_a_editar,))
            
            update = """
                UPDATE HORARIO
                SET HORA_SALIDA_PROGRAMADA = TO_DATE(:1, 'HH24:MI:SS'),
                    HORA_LLEGADA_PROGRAMADA = TO_DATE(:2, 'HH24:MI:SS')
                WHERE ID_HORARIO = :3
            """
            # Se agregan segundos ':00' para cumplir con HH24:MI:SS
            cursor.execute(update, (salida + ":00", llegada + ":00", self.id_horario_a_editar))
            self.db.connection.commit()
    
            QMessageBox.information(self, "Éxito", f"Horario actualizado correctamente..")
            self.cancelar()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Error al actualizar", str(e))