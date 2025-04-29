from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                            QScrollArea, QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QIcon
import oracledb
from base_de_datos.db import DatabaseConnection


class InterfazHome(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db  # Usar la conexión existente

        self.setWindowTitle("Panel de Control - Home")
        self.setGeometry(100, 100, 1200, 700)

        self.initUI()
        self.cargar_datos_viajes()
        self.cargar_datos_proximos()

    def initUI(self):
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()


        # Botón de menú
        # Eliminando el botón de menú y su conexión
        # self.btn_menu = QPushButton("☰")
        # self.btn_menu.setFixedSize(40, 40)
        # top_layout.addWidget(self.btn_menu)

        # Botón de correo
        self.btn_correo = QPushButton()  
        self.btn_correo.setIcon(QIcon("icons/alert.png"))
        self.btn_correo.setFixedSize(40, 40)
        self.btn_correo.clicked.connect(lambda: self.main_window.cambiar_interfaz(3))
        top_layout.addWidget(self.btn_correo)   


        # Reloj
        self.label_reloj = QLabel()
        self.label_reloj.setStyleSheet("font-size: 18px;")
        self.actualizar_reloj()
        timer = QTimer(self)
        timer.timeout.connect(self.actualizar_reloj)
        timer.start(1000)
        top_layout.addWidget(self.label_reloj)

        top_layout.addStretch()
        layout.addLayout(top_layout)

        # VIAJES EN CURSO
        layout.addWidget(QLabel("Viajes en curso"))
        self.tabla_viajes = QTableWidget()
        self.tabla_viajes.setColumnCount(10)
        self.tabla_viajes.setHorizontalHeaderLabels([
            "Código Horario", "Salida Programada", "Llegada Programada",
            "Salida Real", "Llegada Real", "Duración", "Origen", "Destino",
            "Nombre del Tren", "Tipo de Incidencia"
        ])
        layout.addWidget(self.crear_scroll_para_tabla(self.tabla_viajes))

        # PROXIMAMENTE
        layout.addWidget(QLabel("Próximamente"))
        self.tabla_proximos = QTableWidget()
        self.tabla_proximos.setColumnCount(8)
        self.tabla_proximos.setHorizontalHeaderLabels([
            "Código Horario", "Salida Programada", "Llegada Programada",
            "Duración", "Origen", "Destino", "Nombre del Tren", "Estado del Tren"
        ])
        layout.addWidget(self.crear_scroll_para_tabla(self.tabla_proximos))

        botones_layout = QHBoxLayout()
        botones_layout.addStretch()
        self.btn_modificar = QPushButton("Modificar")
        self.btn_modificar.clicked.connect(self.accion_modificar)
        self.btn_asignar = QPushButton("Asignar")
        self.btn_asignar.clicked.connect(self.accion_asignar)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.accion_cancelar)
        botones_layout.addWidget(self.btn_modificar)
        botones_layout.addWidget(self.btn_asignar)
        botones_layout.addWidget(self.btn_cancelar)
        layout.addLayout(botones_layout)

        self.setLayout(layout)

    
    def cargar_datos(self):
        print("[DEBUG] Recargando datos de Viajes en Curso y Próximamente...")
        self.cargar_datos_viajes()
        self.cargar_datos_proximos()


    def crear_scroll_para_tabla(self, tabla):
        tabla.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        scroll_frame = QFrame()
        scroll_layout = QVBoxLayout(scroll_frame)
        scroll_layout.addWidget(tabla)
        return scroll_frame

    def actualizar_reloj(self):
        self.label_reloj.setText(QTime.currentTime().toString("HH:mm:ss"))

    def cargar_datos_viajes(self):
        query = """
            SELECT 
                H.ID_HORARIO, 
                TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS SALIDA_PROG,  -- Fecha + hora
                TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS') AS LLEGADA_PROG,
                TO_CHAR(H.HORA_SALIDA_REAL, 'DD/MM/YYYY HH24:MI') AS SALIDA_REAL,
                TO_CHAR(H.HORA_LLEGADA_REAL, 'DD/MM/YYYY HH24:MI') AS LLEGADA_REAL,
                R.DURACION_ESTIMADA,
                E1.NOMBRE AS ORIGEN,
                E2.NOMBRE AS DESTINO,
                T.NOMBRE AS NOMBRE_TREN,
                I.TIPO AS TIPO_INCIDENCIA
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            LEFT JOIN INCIDENCIA I ON I.ID_HORARIO = H.ID_HORARIO
            JOIN RUTA_DETALLE RD1 ON RD1.ID_RUTA = A.ID_RUTA AND RD1.ORDEN = 1
            JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
            JOIN RUTA_DETALLE RD2 ON RD2.ID_RUTA = A.ID_RUTA
            JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
            WHERE RD2.ORDEN = (SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = A.ID_RUTA)
              AND H.HORA_SALIDA_PROGRAMADA <= SYSDATE  -- Comparación con fecha+hora exacta
        """
        viajes = self.db.fetch_all(query)
        self.tabla_viajes.setRowCount(0)  
        if viajes:
            self.tabla_viajes.setRowCount(len(viajes))
            for i, v in enumerate(viajes):
                for j, dato in enumerate(v):
                    self.tabla_viajes.setItem(i, j, QTableWidgetItem(str(dato if dato is not None else "")))

    def cargar_datos_proximos(self):
        query = """
            SELECT 
                H.ID_HORARIO, 
                TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'DD/MM/YY HH24:MI') AS SALIDA_PROG,  -- Fecha + hora
                TO_CHAR(H.HORA_LLEGADA_PROGRAMADA, 'DD/MM/YY HH24:MI') AS LLEGADA_PROG,
                R.DURACION_ESTIMADA,
                E1.NOMBRE AS ORIGEN,
                E2.NOMBRE AS DESTINO,
                T.NOMBRE AS NOMBRE_TREN,
                T.ESTADO
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN TREN T ON A.ID_TREN = T.ID_TREN
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            JOIN RUTA_DETALLE RD1 ON RD1.ID_RUTA = A.ID_RUTA AND RD1.ORDEN = 1
            JOIN ESTACION E1 ON RD1.ID_ESTACION = E1.ID_ESTACION
            JOIN RUTA_DETALLE RD2 ON RD2.ID_RUTA = A.ID_RUTA
            JOIN ESTACION E2 ON RD2.ID_ESTACION = E2.ID_ESTACION
            WHERE RD2.ORDEN = (SELECT MAX(ORDEN) FROM RUTA_DETALLE WHERE ID_RUTA = A.ID_RUTA)
            AND H.HORA_SALIDA_PROGRAMADA > SYSDATE  -- Comparación con fecha+hora exacta
            ORDER BY H.HORA_SALIDA_PROGRAMADA ASC
        """
        proximos = self.db.fetch_all(query)
        if proximos:
            self.tabla_proximos.setRowCount(len(proximos))
            self.tabla_proximos.setRowCount(0) 
            for i, p in enumerate(proximos):
                for j, dato in enumerate(p):
                    self.tabla_proximos.setItem(i, j, QTableWidgetItem(str(dato if dato is not None else "")))


    def accion_modificar(self):
        print("Modificar registro...")

    def accion_asignar(self):
        print("Asignar tren...")

    def accion_cancelar(self):
        fila = self.tabla_proximos.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Atención", "Selecciona un registro de 'Próximamente' para cancelar.")
            return

        id_horario = self.tabla_proximos.item(fila, 0).text()
        print(f"[DEBUG] Intentando eliminar ID_HORARIO: {id_horario}")

        # Verificar primero si el horario existe
        horario_existe = self.db.fetch_one("SELECT 1 FROM HORARIO WHERE ID_HORARIO = :1", [id_horario])
        if not horario_existe:
            QMessageBox.warning(self, "Error", f"No se encontró el horario {id_horario} en la base de datos.")
            return

        confirmar = QMessageBox.question(
            self, "Confirmar", f"¿Estás seguro de eliminar el horario {id_horario} y todos sus registros relacionados?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmar == QMessageBox.StandardButton.No:
            return

        try:
            # Desactivar autocommit para manejar transacción manualmente
            self.db.connection.autocommit = False

            # 1. Eliminar incidencias primero
            resultado = self.db.execute_query(
                "DELETE FROM INCIDENCIA WHERE ID_HORARIO = :1",
                [id_horario],
                return_rows=True
            )
            print(f"[DEBUG] Filas eliminadas de INCIDENCIA: {resultado}")

            # 2. Eliminar del historial
            resultado = self.db.execute_query(
                "DELETE FROM HISTORIAL WHERE ID_HORARIO = :1",
                [id_horario],
                return_rows=True
            )
            print(f"[DEBUG] Filas eliminadas de HISTORIAL: {resultado}")

            # 3. Eliminar asignación de tren
            resultado = self.db.execute_query(
                "DELETE FROM ASIGNACION_TREN WHERE ID_HORARIO = :1",
                [id_horario],
                return_rows=True
            )
            print(f"[DEBUG] Filas eliminadas de ASIGNACION_TREN: {resultado}")

            # 4. Finalmente eliminar el horario
            resultado = self.db.execute_query(
                "DELETE FROM HORARIO WHERE ID_HORARIO = :1",
                [id_horario],
                return_rows=True
            )
            print(f"[DEBUG] Filas eliminadas de HORARIO: {resultado}")

            if resultado == 0:
                raise Exception("No se eliminó ningún registro de HORARIO")

            # Confirmar todos los cambios
            self.db.connection.commit()

            QMessageBox.information(self, "Éxito", f"Horario {id_horario} eliminado correctamente.")

            # Actualizar las tablas
            self.tabla_proximos.setRowCount(0)
            self.cargar_datos_proximos()
            self.cargar_datos_viajes()

        except oracledb.DatabaseError as e:
            # Revertir en caso de error
            self.db.connection.rollback()
            error_msg = f"Error de base de datos: {e.args[0].message}"
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

        except Exception as e:
            self.db.connection.rollback()
            print(f"[ERROR] {str(e)}")
            QMessageBox.critical(self, "Error", str(e))

        finally:
            # Restaurar autocommit
            self.db.connection.autocommit = True

    def prueba_base_datos(self):
        # Crear una instancia de la conexión a la base de datos
        db = DatabaseConnection("PROYECTO_IS", "123", "localhost", 1521, "XE")
        if db.connect():
            try:
                # Ejemplo de fetch_one
                id_horario = 405  # Cambia este valor según los datos en tu base de datos
                resultado = db.fetch_one("SELECT * FROM HORARIO WHERE ID_HORARIO = :1", [id_horario])
                if resultado:
                    print("Registro encontrado:", resultado)
                else:
                    print(f"No se encontró un registro con ID_HORARIO = {id_horario}")

                # Ejemplo de execute_query con conteo de filas
                filas_eliminadas = db.execute_query(
                    "DELETE FROM INCIDENCIA WHERE ID_HORARIO = :1",
                    [id_horario],
                    return_rows=True
                )
                print(f"Filas eliminadas de INCIDENCIA: {filas_eliminadas}")

            except Exception as e:
                print(f"[ERROR] {e}")
            finally:
                db.close()