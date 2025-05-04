from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                            QDateEdit, QPushButton, QMessageBox, QSizePolicy, 
                            QSpacerItem, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QDate, QDateTime, QTime, QSize
from PyQt6.QtGui import QPixmap
import oracledb
from datetime import datetime, timedelta

class InterfazAsignacion(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.TIEMPO_ABORDAJE = 5  # minutos entre viajes
        self.TIEMPO_TRANSFERENCIA = 30  # minutos para cambiar de ruta
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Panel izquierdo con controles (60% del espacio)
        panel_controles = QFrame()
        panel_controles.setFrameShape(QFrame.Shape.StyledPanel)
        controles_layout = QVBoxLayout(panel_controles)
        controles_layout.setSpacing(8)
        
        # Sección de fecha
        fecha_layout = QHBoxLayout()
        fecha_layout.addWidget(QLabel("Fecha:"))
        self.calendario = QDateEdit()
        self.calendario.setDisplayFormat("dd/MM/yyyy")
        self.calendario.setDate(QDate.currentDate())
        self.calendario.setCalendarPopup(True)
        self.calendario.setMinimumDate(QDate.currentDate())
        self.calendario.dateChanged.connect(self.actualizar_horas_disponibles)
        fecha_layout.addWidget(self.calendario)
        controles_layout.addLayout(fecha_layout)
        
        # Sección de hora
        hora_layout = QHBoxLayout()
        hora_layout.addWidget(QLabel("Hora:"))
        self.combo_hora = QComboBox()
        self.combo_hora.setEditable(True)
        self.actualizar_horas_disponibles()
        hora_layout.addWidget(self.combo_hora)
        
        hora_layout.addWidget(QLabel(":"))
        
        self.combo_minutos = QComboBox()
        self.combo_minutos.setEditable(True)
        for m in range(0, 60, 5):  # Cada 5 minutos
            self.combo_minutos.addItem(f"{m:02d}")
        hora_layout.addWidget(self.combo_minutos)
        controles_layout.addLayout(hora_layout)
        
        # Tren
        tren_layout = QHBoxLayout()
        tren_layout.addWidget(QLabel("Unidad:"))
        self.combo_tren = QComboBox()
        self.combo_tren.addItem("Seleccionar")
        self.cargar_trenes_disponibles()
        tren_layout.addWidget(self.combo_tren)
        controles_layout.addLayout(tren_layout)
        
        # Ruta
        ruta_layout = QHBoxLayout()
        ruta_layout.addWidget(QLabel("Ruta:"))
        self.combo_ruta = QComboBox()
        self.combo_ruta.addItem("Seleccionar")
        self.cargar_rutas()
        self.combo_ruta.currentIndexChanged.connect(self.on_ruta_selected)
        ruta_layout.addWidget(self.combo_ruta)
        controles_layout.addLayout(ruta_layout)
        
        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.regresar_home)
        botones_layout.addWidget(self.btn_cancelar)
        
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.clicked.connect(self.validar_asignacion)
        botones_layout.addWidget(self.btn_consultar)
        
        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.clicked.connect(self.confirmar_asignacion)
        botones_layout.addWidget(self.btn_confirmar)
        
        controles_layout.addLayout(botones_layout)
        
        # Mensaje de estado
        self.label_mensaje = QLabel()
        self.label_mensaje.setWordWrap(True)
        self.label_mensaje.setStyleSheet("padding: 5px; margin-top: 5px; font-size: 12px;")
        controles_layout.addWidget(self.label_mensaje)
        
        main_layout.addWidget(panel_controles, stretch=3)  # 60% del espacio
        
        # Panel derecho con imagen (40% del espacio)
        panel_imagen = QFrame()
        panel_imagen.setFrameShape(QFrame.Shape.StyledPanel)
        imagen_layout = QVBoxLayout(panel_imagen)
        
        self.img_ruta = QLabel()
        self.img_ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_ruta.setStyleSheet("""
            background-color: #f0f0f0; 
            border: 1px solid #ccc;
            padding: 5px;
            qproperty-alignment: 'AlignCenter';
        """)
        self.img_ruta.setMinimumSize(300, 400)
        self.img_ruta.setText("Seleccione una ruta para ver su imagen")
        
        scroll_img = QScrollArea()
        scroll_img.setWidget(self.img_ruta)
        scroll_img.setWidgetResizable(True)
        imagen_layout.addWidget(scroll_img)
        
        main_layout.addWidget(panel_imagen, stretch=2)  # 40% del espacio
        
        self.adjustSize()
        self.setMinimumSize(700, 500)

    def actualizar_horas_disponibles(self):
        """Actualiza las horas disponibles según la fecha seleccionada"""
        self.combo_hora.clear()
        
        hora_actual = QTime.currentTime().hour()
        minuto_actual = QTime.currentTime().minute()
        
        # Si es hoy, mostramos horas desde la actual
        if self.calendario.date() == QDate.currentDate():
            hora_inicio = hora_actual
        else:
            hora_inicio = 0  # Si es otro día, mostramos todas las horas
            
        for h in range(hora_inicio, 24):
            self.combo_hora.addItem(f"{h:02d}")

    def load_route_image(self, id_ruta):
        """Carga la imagen de la ruta desde la base de datos"""
        try:
            self.img_ruta.clear()
            query = "SELECT IMAGEN FROM RUTA WHERE ID_RUTA = :id_ruta"
            image_data = self.db.fetch_all(query, {"id_ruta": id_ruta})

            if not image_data or not image_data[0][0]:
                self.img_ruta.setText("No hay imagen disponible para esta ruta")
                return

            # Obtener el BLOB de la imagen
            image_blob = image_data[0][0]
            image_bytes = image_blob.read()

            # Crear QPixmap desde bytes
            pixmap = QPixmap()
            if not pixmap.loadFromData(image_bytes):
                self.img_ruta.setText("Formato de imagen no soportado")
                return

            # Escalar manteniendo aspecto
            scaled_pixmap = pixmap.scaled(
                self.img_ruta.width() - 20,
                self.img_ruta.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.img_ruta.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error al cargar imagen: {str(e)}")
            self.img_ruta.setText("Error al cargar imagen")

    def on_ruta_selected(self):
        """Maneja la selección de una ruta"""
        if self.combo_ruta.currentIndex() > 0:
            id_ruta = self.combo_ruta.currentData()
            self.load_route_image(id_ruta)

    def cargar_trenes_disponibles(self):
        """Carga los trenes disponibles con información de sus horarios"""
        self.combo_tren.clear()
        self.combo_tren.addItem("Seleccionar")
        
        query = """
            SELECT T.ID_TREN, T.NOMBRE 
            FROM TREN T 
            WHERE T.ESTADO = 'ACTIVO'
            ORDER BY T.ID_TREN
        """
        trenes = self.db.fetch_all(query)
        
        if trenes:
            for id_tren, nombre in trenes:
                # Obtener último horario asignado
                query_ultimo = """
                    SELECT MAX(H.HORA_LLEGADA_PROGRAMADA)
                    FROM ASIGNACION_TREN A
                    JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
                    WHERE A.ID_TREN = :id_tren
                """
                ultimo_horario = self.db.fetch_one(query_ultimo, {"id_tren": id_tren})
                
                texto = f"{id_tren} - {nombre}"
                if ultimo_horario and ultimo_horario[0]:
                    if isinstance(ultimo_horario[0], datetime):
                        texto += f" (Último: {ultimo_horario[0].strftime('%H:%M')})"
                    else:
                        texto += f" (Último: {str(ultimo_horario[0])})"
                
                self.combo_tren.addItem(texto, id_tren)

    def cargar_rutas(self):
        """Carga las rutas disponibles con información básica"""
        self.combo_ruta.clear()
        self.combo_ruta.addItem("Seleccionar")
        
        query = """
            SELECT R.ID_RUTA, 
                   LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN) AS ESTACIONES
            FROM RUTA R
            JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
            JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
            GROUP BY R.ID_RUTA
            ORDER BY R.ID_RUTA
        """
        rutas = self.db.fetch_all(query)
        
        if rutas:
            for id_ruta, estaciones in rutas:
                self.combo_ruta.addItem(f"Ruta {id_ruta} - {estaciones.split('→')[0].strip()}...", id_ruta)

    def validar_asignacion(self):
        """Valida la asignación con todas las reglas de negocio"""
        # Validación básica de campos
        if self.combo_tren.currentIndex() <= 0:
            self.mostrar_mensaje("Seleccione un tren válido", False)
            return False
            
        if self.combo_ruta.currentIndex() <= 0:
            self.mostrar_mensaje("Seleccione una ruta válida", False)
            return False
            
        try:
            hora = int(self.combo_hora.currentText())
            minutos = int(self.combo_minutos.currentText())
            if not (0 <= hora < 24 and 0 <= minutos < 60):
                raise ValueError
        except ValueError:
            self.mostrar_mensaje("La hora seleccionada no es válida", False)
            return False
            
        fecha = self.calendario.date()
        fecha_hora_seleccionada = QDateTime(fecha, QTime(hora, minutos))
        
        if fecha_hora_seleccionada < QDateTime.currentDateTime():
            self.mostrar_mensaje("No se puede asignar un horario en el pasado", False)
            return False
            
        id_tren = self.combo_tren.currentData()
        id_ruta = self.combo_ruta.currentData()
        
        # Obtener duración de la nueva ruta
        query_duracion = "SELECT DURACION_ESTIMADA FROM RUTA WHERE ID_RUTA = :id_ruta"
        duracion = self.db.fetch_one(query_duracion, {"id_ruta": id_ruta})
        if not duracion:
            self.mostrar_mensaje("No se pudo obtener la duración de la ruta", False)
            return False
            
        duracion = duracion[0]
        nueva_salida = fecha_hora_seleccionada.toPyDateTime()
        nueva_llegada = nueva_salida + timedelta(minutes=duracion)
        
        # 1. Verificar que el tren no tenga viajes solapados en la misma fecha
        query_viajes = """
            SELECT H.HORA_SALIDA_PROGRAMADA, H.HORA_LLEGADA_PROGRAMADA,
                   R.DURACION_ESTIMADA, R.ID_RUTA
            FROM ASIGNACION_TREN A
            JOIN HORARIO H ON A.ID_HORARIO = H.ID_HORARIO
            JOIN RUTA R ON A.ID_RUTA = R.ID_RUTA
            WHERE A.ID_TREN = :id_tren
            AND TRUNC(H.HORA_SALIDA_PROGRAMADA) = TO_DATE(:fecha, 'YYYY-MM-DD')
            ORDER BY H.HORA_SALIDA_PROGRAMADA
        """
        
        try:
            viajes = self.db.fetch_all(query_viajes, {
                "id_tren": id_tren,
                "fecha": fecha.toString("yyyy-MM-dd")
            })
        except Exception as e:
            print(f"Error en consulta de viajes: {str(e)}")
            self.mostrar_mensaje("Error al verificar horarios existentes", False)
            return False
            
        if viajes:
            for viaje in viajes:
                salida_existente = viaje[0] if isinstance(viaje[0], datetime) else datetime.strptime(str(viaje[0]), '%Y-%m-%d %H:%M:%S')
                llegada_existente = viaje[1] if isinstance(viaje[1], datetime) else datetime.strptime(str(viaje[1]), '%Y-%m-%d %H:%M:%S')
                
                # Verificar solapamiento
                if (nueva_salida < llegada_existente and nueva_llegada > salida_existente):
                    self.mostrar_mensaje(
                        f"El tren ya tiene un viaje asignado de {salida_existente.strftime('%H:%M')} "
                        f"a {llegada_existente.strftime('%H:%M')}", False)
                    return False
                    
                # Verificar tiempo mínimo entre viajes
                tiempo_minimo = timedelta(minutes=self.TIEMPO_ABORDAJE)
                if abs(nueva_salida - llegada_existente) < tiempo_minimo or abs(salida_existente - nueva_llegada) < tiempo_minimo:
                    self.mostrar_mensaje(
                        f"Debe haber al menos {self.TIEMPO_ABORDAJE} minutos entre viajes "
                        f"(Viaje existente: {salida_existente.strftime('%H:%M')}-{llegada_existente.strftime('%H:%M')})", 
                        False)
                    return False
                    
                # Verificar cambio de ruta (si es diferente a la actual)
                if viaje[3] != id_ruta:
                    tiempo_transferencia = timedelta(minutes=self.TIEMPO_TRANSFERENCIA)
                    if abs(nueva_salida - llegada_existente) < tiempo_transferencia:
                        # Obtener estaciones de ambas rutas
                        estaciones_ruta_actual = self.obtener_estaciones_ruta(id_ruta)
                        estaciones_ruta_existente = self.obtener_estaciones_ruta(viaje[3])
                        
                        # Verificar si comparten estaciones
                        if not set(estaciones_ruta_actual).intersection(set(estaciones_ruta_existente)):
                            self.mostrar_mensaje(
                                f"El tren necesita al menos {self.TIEMPO_TRANSFERENCIA} minutos "
                                f"para cambiar de ruta (no comparten estaciones)", 
                                False)
                            return False
        
        # Si todo está bien
        self.mostrar_mensaje(
            f"Asignación válida. Viaje programado de {nueva_salida.strftime('%H:%M')} "
            f"a {nueva_llegada.strftime('%H:%M')}. Tiempo de abordaje: {self.TIEMPO_ABORDAJE} minutos.", 
            True)
        return True

    def obtener_estaciones_ruta(self, id_ruta):
        """Obtiene las estaciones de una ruta específica"""
        query = """
            SELECT E.ID_ESTACION 
            FROM RUTA_DETALLE RD
            JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
            WHERE RD.ID_RUTA = :id_ruta
            ORDER BY RD.ORDEN
        """
        resultados = self.db.fetch_all(query, {"id_ruta": id_ruta})
        return [r[0] for r in resultados] if resultados else []

    def confirmar_asignacion(self):
        """Confirma y guarda la asignación en la base de datos"""
        if not self.validar_asignacion():
            QMessageBox.critical(self, "Error", "No se pudo realizar la asignación de horario")
            return
            
        try:
            hora = int(self.combo_hora.currentText())
            minutos = int(self.combo_minutos.currentText())
            fecha = self.calendario.date()
            id_tren = self.combo_tren.currentData()
            id_ruta = self.combo_ruta.currentData()
            
            # Obtener duración estimada de la ruta
            query_duracion = "SELECT DURACION_ESTIMADA FROM RUTA WHERE ID_RUTA = :id_ruta"
            duracion = self.db.fetch_one(query_duracion, {"id_ruta": id_ruta})[0]
            
            # Crear fechas/horas en formato correcto para Oracle
            fecha_hora_salida = QDateTime(fecha, QTime(hora, minutos))
            salida_str = fecha_hora_salida.toString("yyyy-MM-dd HH:mm:ss")
            llegada_str = fecha_hora_salida.addSecs(duracion * 60).toString("yyyy-MM-dd HH:mm:ss")
            
            # Insertar horario
            query_horario = """
                INSERT INTO HORARIO (ID_HORARIO, HORA_SALIDA_PROGRAMADA, HORA_LLEGADA_PROGRAMADA)
                VALUES ((SELECT NVL(MAX(ID_HORARIO), 0) + 1 FROM HORARIO), 
                        TO_DATE(:salida, 'YYYY-MM-DD HH24:MI:SS'), 
                        TO_DATE(:llegada, 'YYYY-MM-DD HH24:MI:SS'))
                RETURNING ID_HORARIO INTO :id_horario
            """
            
            id_horario = self.db.execute_query_with_return(query_horario, {
                "salida": salida_str,
                "llegada": llegada_str
            })
            
            if not id_horario:
                raise Exception("Error al insertar horario")
            
            # Insertar asignación
            query_asignacion = """
                INSERT INTO ASIGNACION_TREN (ID_ASIGNACION, ID_TREN, ID_RUTA, ID_HORARIO)
                VALUES ((SELECT NVL(MAX(ID_ASIGNACION), 0) + 1 FROM ASIGNACION_TREN), 
                        :id_tren, :id_ruta, :id_horario)
            """
            if not self.db.execute_query(query_asignacion, {
                "id_tren": id_tren,
                "id_ruta": id_ruta,
                "id_horario": id_horario
            }):
                raise Exception("Error al insertar asignación")
            
            # Commit
            if not self.db.commit():
                raise Exception("Error al hacer commit")
            
            QMessageBox.information(
                self, 
                "Éxito", 
                f"Asignación realizada:\n"
                f"Tren: {self.combo_tren.currentText().split('-')[0].strip()}\n"
                f"Ruta: {self.combo_ruta.currentText().split('-')[0].strip()}\n"
                f"Horario: {salida_str.split(' ')[1]} - {llegada_str.split(' ')[1]}\n"
                f"Tiempo de abordaje: {self.TIEMPO_ABORDAJE} minutos")
            
            # Actualizar y regresar
            self.cargar_trenes_disponibles()
            self.regresar_home()
            
        except Exception as e:
            print(f"Error al confirmar: {str(e)}")
            self.db.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo completar la asignación: {str(e)}")

    def mostrar_mensaje(self, texto, es_exito):
        """Muestra mensajes de estado"""
        self.label_mensaje.setText(texto)
        self.label_mensaje.setStyleSheet(
            "color: green; font-weight: bold;" if es_exito else 
            "color: red; font-weight: bold;")

    def regresar_home(self):
        """Regresa a la pantalla principal"""
        self.main_window.cambiar_interfaz(0)

    def resizeEvent(self, event):
        """Redimensiona la imagen al cambiar el tamaño"""
        if hasattr(self, 'img_ruta') and self.img_ruta.pixmap():
            self.img_ruta.setPixmap(self.img_ruta.pixmap().scaled(
                self.img_ruta.width(), 
                self.img_ruta.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        super().resizeEvent(event)