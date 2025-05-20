from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class InterfazGestionUsuarios(QWidget):
    cerrar_sesion = pyqtSignal()  # Señal para volver al login

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Administración de Usuarios")
        self.setMinimumSize(800, 600)

        self.initUI()
        self.cargar_usuarios()

    def initUI(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)

        # Título
        titulo = QLabel("Administración de Usuarios")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                border-bottom: 2px solid #2980b9;
                padding-bottom: 10px;
            }
        """)
        layout_principal.addWidget(titulo)

        # Tabla de usuarios
        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setColumnCount(4)
        self.tabla_usuarios.setHorizontalHeaderLabels(["ID Usuario", "Nombre", "Contraseña", "Registros en Historial"])
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_usuarios.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                font-size: 14px;
            }
        """)
        # Selección por fila completa y solo una fila a la vez
        self.tabla_usuarios.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_usuarios.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        layout_principal.addWidget(self.tabla_usuarios)

        # Botones de acción (Agregar, Modificar, Eliminar)
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)

        self.btn_agregar = QPushButton("Agregar Usuario")
        self.btn_modificar = QPushButton("Modificar Usuario")
        self.btn_eliminar = QPushButton("Eliminar Usuario")
        
        self.btn_modificar.setEnabled(False)
        self.btn_eliminar.setEnabled(False)

        self.btn_agregar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_modificar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_eliminar.setStyleSheet("""
            QPushButton {
            padding: 10px 20px;
            background-color: #e74c3c;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
            min-width: 200px;
        }
        QPushButton:hover {
            background-color: #c0392b;
        }QPushButton:disabled {
            background-color: #95a5a6;
        }
        """)
        botones_layout.addWidget(self.btn_agregar)
        botones_layout.addWidget(self.btn_modificar)
        botones_layout.addWidget(self.btn_eliminar)

        layout_principal.addLayout(botones_layout)

        # Botón de cerrar sesión
        self.btn_cerrar_sesion = QPushButton("Cerrar sesión")
        self.btn_cerrar_sesion.setStyleSheet("""
            QPushButton {
                margin-top: 30px;
                padding: 10px;
                font-size: 14px;
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_cerrar_sesion.clicked.connect(self.cerrar_sesion.emit)
        self.btn_agregar.clicked.connect(self.abrir_dialogo_agregar_usuario)
        self.btn_modificar.clicked.connect(self.abrir_dialogo_modificar_usuario)
        self.btn_eliminar.clicked.connect(self.eliminar_usuario)
        layout_principal.addWidget(self.btn_cerrar_sesion, alignment=Qt.AlignmentFlag.AlignRight)

    def bloquear_botones(self):
        self.tabla_usuarios.clearSelection()
        self.tabla_usuarios.clearFocus()
        self.btn_modificar.setEnabled(False)
        self.btn_eliminar.setEnabled(False)
        
    def controlar_botones(self):
        if self.tabla_usuarios.currentRow() == -1:
            self.btn_eliminar.setEnabled(False)
            self.btn_modificar.setEnabled(False)
        else:
            self.btn_eliminar.setEnabled(True)
            self.btn_modificar.setEnabled(True)

    def cargar_usuarios(self):
        cursor = self.db.connection.cursor()
        try:
            cursor.execute("""
                SELECT ID_USUARIO, NOMBRE, APELLIDO_PATERNO, APELLIDO_MATERNO,
                CONTRASENA FROM USUARIO
                WHERE ID_USUARIO <> 9999
            """)
            resultados = cursor.fetchall()

            self.tabla_usuarios.setRowCount(len(resultados))
            # Limpia selección completamente
            self.tabla_usuarios.clearSelection()
            self.tabla_usuarios.setCurrentItem(None)
            for fila, usuario in enumerate(resultados):
                id_usuario = QTableWidgetItem(str(usuario[0]))
                nombre_completo = f"{usuario[1]} {usuario[2]} {usuario[3]}"
                nombre_item = QTableWidgetItem(nombre_completo)
                contrasena = QTableWidgetItem(usuario[4])

                self.tabla_usuarios.setItem(fila, 0, id_usuario)
                self.tabla_usuarios.setItem(fila, 1, nombre_item)
                self.tabla_usuarios.setItem(fila, 2, contrasena)
                
                # Obtener la cantidad de registros en HISTORIAL para este usuario
                cursor.execute("SELECT COUNT(*) FROM HISTORIAL WHERE ID_USUARIO = :1", [usuario[0]])
                cantidad = cursor.fetchone()[0]
                self.tabla_usuarios.setItem(fila, 3, QTableWidgetItem(str(cantidad)))
            # Conectar solo una vez fuera del ciclo
            self.tabla_usuarios.clearSelection()
            try:
                self.tabla_usuarios.selectionModel().selectionChanged.disconnect()
            except Exception:
                pass  # Ignora si no estaba conectado

            self.tabla_usuarios.selectionModel().selectionChanged.connect(self.controlar_botones)
            self.controlar_botones()


        except Exception as e:
            print("Error al cargar usuarios:", e)
        finally:
            cursor.close()

    def abrir_dialogo_agregar_usuario(self):
        dialogo = DialogoAgregarUsuario(self.db, self)
        if dialogo.exec():
            self.cargar_usuarios()  # Recarga la tabla tras agregar un nuevo usuario

    def abrir_dialogo_modificar_usuario(self):
        fila = self.tabla_usuarios.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Selecciona un usuario", "Selecciona un usuario de la tabla para modificar.")
            return

        id_usuario_item = self.tabla_usuarios.item(fila, 0)
        if not id_usuario_item:
            return

        id_usuario = int(id_usuario_item.text())
        if id_usuario == 9999:
            QMessageBox.warning(self, "Acción no permitida", "No puedes modificar al usuario administrador.")
            return

        nombre_completo = self.tabla_usuarios.item(fila, 1).text().split()
        nombre = nombre_completo[0]
        apellido_paterno = nombre_completo[1] if len(nombre_completo) > 1 else ""
        apellido_materno = nombre_completo[2] if len(nombre_completo) > 2 else ""
        contrasena = self.tabla_usuarios.item(fila, 2).text()

        dialogo = DialogoModificarUsuario(self.db, id_usuario, nombre, apellido_paterno, apellido_materno, contrasena)
        if dialogo.exec():
            self.cargar_usuarios()
        self.bloquear_botones()

    def eliminar_usuario(self):
        fila = self.tabla_usuarios.currentRow()

        if fila == -1:
            QMessageBox.warning(self, "Advertencia", "Selecciona un usuario para eliminar.")
            return

        id_usuario = self.tabla_usuarios.item(fila, 0).text()
        cantidad = int(self.tabla_usuarios.item(fila, 3).text())

        if cantidad > 0:
            QMessageBox.warning(self, "No se puede eliminar", "Este usuario tiene registros en el historial.")
            self.bloquear_botones()
            return

        confirmacion = QMessageBox()
        confirmacion.setIcon(QMessageBox.Icon.Question)
        confirmacion.setWindowTitle("Confirmar eliminación")
        confirmacion.setText(f"¿Estás seguro de que deseas eliminar al usuario con ID {id_usuario}?")
        confirmacion.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        confirmacion.addButton("No", QMessageBox.ButtonRole.NoRole)

        if confirmacion.exec() == 2:
            try:
                cursor = self.db.connection.cursor()
                cursor.execute("DELETE FROM USUARIO WHERE ID_USUARIO = :1", [id_usuario])
                self.db.connection.commit()
                cursor.close()
                QMessageBox.information(self, "Éxito", "Usuario eliminado correctamente.")
                self.cargar_usuarios()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el usuario.\nError: {e}")
        self.bloquear_botones()


from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

class DialogoAgregarUsuario(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Agregar Usuario")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre")

        self.input_apellido_paterno = QLineEdit()
        self.input_apellido_paterno.setPlaceholderText("Apellido paterno")

        self.input_apellido_materno = QLineEdit()
        self.input_apellido_materno.setPlaceholderText("Apellido materno")

        self.input_contrasena = QLineEdit()
        self.input_contrasena.setPlaceholderText("Contraseña")

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self.guardar_usuario)

        layout.addWidget(QLabel("Nombre:"))
        layout.addWidget(self.input_nombre)
        layout.addWidget(QLabel("Apellido Paterno:"))
        layout.addWidget(self.input_apellido_paterno)
        layout.addWidget(QLabel("Apellido Materno:"))
        layout.addWidget(self.input_apellido_materno)
        layout.addWidget(QLabel("Contraseña:"))
        layout.addWidget(self.input_contrasena)
        layout.addWidget(self.btn_guardar)

    def guardar_usuario(self):
        nombre = self.input_nombre.text().strip()
        apellido_paterno = self.input_apellido_paterno.text().strip()
        apellido_materno = self.input_apellido_materno.text().strip()
        contrasena = self.input_contrasena.text().strip()

        if not all([nombre, apellido_paterno, apellido_materno, contrasena]):
            QMessageBox.warning(self, "Campos incompletos", "Por favor completa todos los campos.")
            return

        if any(len(campo) > 50 for campo in [nombre, apellido_paterno, apellido_materno]) or len(contrasena) > 100:
            QMessageBox.warning(self, "Longitud excedida", "Nombre y apellidos deben tener máximo 50 caracteres.\nLa contraseña debe tener máximo 100.")
            return

        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT MAX(ID_USUARIO)
                FROM USUARIO
                WHERE ID_USUARIO <> 9999
            """)
            max_id = cursor.fetchone()[0] or 0
            id_usuario = max_id + 1

            cursor.execute("""
                INSERT INTO USUARIO (ID_USUARIO, NOMBRE, APELLIDO_PATERNO, APELLIDO_MATERNO, CONTRASENA)
                VALUES (:1, :2, :3, :4, :5)
            """, (id_usuario, nombre, apellido_paterno, apellido_materno, contrasena))
            self.db.connection.commit()
            cursor.close()
            QMessageBox.information(self, "Éxito", "Usuario agregado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo agregar el usuario:\n{e}")


class DialogoModificarUsuario(QDialog):
    def __init__(self, db, id_usuario, nombre, apellido_paterno, apellido_materno, contrasena, parent=None):
        super().__init__(parent)
        self.db = db
        self.id_usuario = id_usuario
        self.setWindowTitle("Modificar Usuario")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        self.input_nombre = QLineEdit(nombre)
        self.input_apellido_paterno = QLineEdit(apellido_paterno)
        self.input_apellido_materno = QLineEdit(apellido_materno)
        self.input_contrasena = QLineEdit(contrasena)

        self.btn_guardar = QPushButton("Guardar cambios")
        self.btn_guardar.clicked.connect(self.modificar_usuario)

        layout.addWidget(QLabel("Nombre:"))
        layout.addWidget(self.input_nombre)
        layout.addWidget(QLabel("Apellido Paterno:"))
        layout.addWidget(self.input_apellido_paterno)
        layout.addWidget(QLabel("Apellido Materno:"))
        layout.addWidget(self.input_apellido_materno)
        layout.addWidget(QLabel("Contraseña:"))
        layout.addWidget(self.input_contrasena)
        layout.addWidget(self.btn_guardar)

    def modificar_usuario(self):
        nombre = self.input_nombre.text().strip()
        apellido_paterno = self.input_apellido_paterno.text().strip()
        apellido_materno = self.input_apellido_materno.text().strip()
        contrasena = self.input_contrasena.text().strip()

        if not all([nombre, apellido_paterno, apellido_materno, contrasena]):
            QMessageBox.warning(self, "Campos incompletos", "Por favor completa todos los campos.")
            return

        if any(len(campo) > 50 for campo in [nombre, apellido_paterno, apellido_materno]) or len(contrasena) > 100:
            QMessageBox.warning(self, "Longitud excedida", "Nombre y apellidos deben tener máximo 50 caracteres.\nLa contraseña debe tener máximo 100.")
            return

        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                UPDATE USUARIO
                SET NOMBRE = :1,
                    APELLIDO_PATERNO = :2,
                    APELLIDO_MATERNO = :3,
                    CONTRASENA = :4
                WHERE ID_USUARIO = :5
            """, (nombre, apellido_paterno, apellido_materno, contrasena, self.id_usuario))
            self.db.connection.commit()
            cursor.close()
            QMessageBox.information(self, "Éxito", "Usuario modificado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo modificar el usuario:\n{e}")
