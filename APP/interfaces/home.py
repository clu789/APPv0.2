from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                            QScrollArea, QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QIcon
from base_de_datos.db import DatabaseConnection
import oracledb

class InterfazHome(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        self.btn_correo = QPushButton()
        self.btn_correo.setIcon(QIcon("APP/icons/alert.png"))
        self.btn_correo.setFixedSize(40, 40)
        self.btn_correo.clicked.connect(lambda: self.main_window.cambiar_interfaz(3))
        top_layout.addWidget(self.btn_correo)

        self.label_reloj = QLabel()
        self.label_reloj.setStyleSheet("font-size: 18px;")
        self.actualizar_reloj()
        timer = QTimer(self)
        timer.timeout.connect(self.actualizar_reloj)
        timer.start(1000)
        top_layout.addWidget(self.label_reloj)

        top_layout.addStretch()
        layout.addLayout(top_layout)

        layout.addWidget(QLabel("Viajes en curso"))
        self.tabla_viajes = QTableWidget()
        self.tabla_viajes.setColumnCount(10)
        self.tabla_viajes.setHorizontalHeaderLabels([
            "Código Horario", "Salida Programada", "Llegada Programada",
            "Salida Real", "Llegada Real", "Duración", "Origen", "Destino",
            "Nombre del Tren", "Tipo de Incidencia"
        ])
        layout.addWidget(self.crear_scroll_para_tabla(self.tabla_viajes))

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
        self.btn_asignar.clicked.connect(lambda: self.main_window.cambiar_interfaz(6))
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.accion_cancelar)
        botones_layout.addWidget(self.btn_modificar)
        botones_layout.addWidget(self.btn_asignar)
        botones_layout.addWidget(self.btn_cancelar)
        layout.addLayout(botones_layout)

        self.setLayout(layout)

        # Recargar los datos necesarios para esta interfaz

    def actualizar_datos(self):
        """Recarga los datos de la interfaz"""
        print("Actualizando datos de InterfazHome")
        self.cargar_datos()

    
    def crear_scroll_para_tabla(self, tabla):
        tabla.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        scroll_frame = QFrame()
        scroll_layout = QVBoxLayout(scroll_frame)
        scroll_layout.addWidget(tabla)
        return scroll_frame

    def actualizar_reloj(self):
        self.label_reloj.setText(QTime.currentTime().toString("HH:mm:ss"))

    def cargar_datos(self):
        print("[DEBUG] Recargando datos de Viajes en Curso y Próximamente...")
        self.cargar_datos_viajes()
        self.cargar_datos_proximos()

    def cargar_datos_viajes(self):
        query = """
            SELECT 
                H.ID_HORARIO, 
                TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS') AS SALIDA_PROG,
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
              AND H.HORA_SALIDA_REAL IS NOT NULL
              AND H.HORA_LLEGADA_REAL IS NULL
            ORDER BY H.HORA_SALIDA_PROGRAMADA ASC
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
                TO_CHAR(H.HORA_SALIDA_PROGRAMADA, 'DD/MM/YY HH24:MI') AS SALIDA_PROG,
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
              AND H.HORA_SALIDA_REAL IS NULL
            ORDER BY H.HORA_SALIDA_PROGRAMADA ASC
        """
        proximos = self.db.fetch_all(query)
        self.tabla_proximos.setRowCount(0)
        if proximos:
            self.tabla_proximos.setRowCount(len(proximos))
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
            self, "Confirmar", 
            f"¿Estás seguro de eliminar el horario {id_horario} y todos sus registros relacionados?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmar == QMessageBox.StandardButton.No:
            return

        try:
            # Desactivar autocommit para manejar transacción manualmente
            self.db.connection.autocommit = False

            # 1. Eliminar incidencias primero
            self.db.execute_query("DELETE FROM INCIDENCIA WHERE ID_HORARIO = :1", [id_horario])
            
            # 2. Eliminar del historial
            self.db.execute_query("DELETE FROM HISTORIAL WHERE ID_HORARIO = :1", [id_horario])
            
            # 3. Eliminar asignación de tren
            self.db.execute_query("DELETE FROM ASIGNACION_TREN WHERE ID_HORARIO = :1", [id_horario])
            
            # 4. Finalmente eliminar el horario
            resultado = self.db.execute_query("DELETE FROM HORARIO WHERE ID_HORARIO = :1", [id_horario])
            
            if resultado == 0:
                raise Exception("No se eliminó ningún registro de HORARIO")

            # Confirmar todos los cambios
            self.db.connection.commit()

            QMessageBox.information(self, "Éxito", f"Horario {id_horario} eliminado correctamente.")

            # Actualizar las tablas
            self.cargar_datos()  # Esto actualiza ambas tablas (viajes y próximos)

             # Emitir señal para actualizar las interfaces
            self.db.event_manager.update_triggered.emit()

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
