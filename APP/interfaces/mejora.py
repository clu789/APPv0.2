from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QPushButton, QMessageBox, QScrollArea, QFrame,
                             QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt
from base_de_datos.db import DatabaseConnection

class MejoraContinua(QWidget):
    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window
        self.db = db

        self.setWindowTitle("Análisis y Mejora Continua")
        self.setGeometry(100, 100, 1200, 600)
        self.initUI()
        self.cargar_datos()
        
    def initUI(self):
        # Layout principal con scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Widget contenedor principal
        self.main_container = QWidget()
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Configurar el scroll area
        self.scroll_area.setWidget(self.main_container)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.scroll_area)
        self.layout().setContentsMargins(0, 0, 0, 0)
    
        # Título con estilo mejorado
        header = QLabel("Historial del Sistema")
        header.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
                border-bottom: 2px solid #3498db;
            }
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
    
        # --- Primera fila: Tres tablas en horizontal ---
        tablas_superiores_container = QWidget()
        tablas_superiores_layout = QHBoxLayout(tablas_superiores_container)
        tablas_superiores_layout.setContentsMargins(0, 0, 0, 0)
        tablas_superiores_layout.setSpacing(15)
    
        # Función para configurar tablas
        def configurar_tabla(tabla, headers):
            tabla.setColumnCount(len(headers))
            tabla.setHorizontalHeaderLabels(headers)
            tabla.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                QHeaderView::section {
                    background-color: #3498db;
                    color: white;
                    padding: 8px;
                    font-weight: bold;
                    border: none;
                }
                QTableWidget::item {
                    padding: 6px;
                    border-bottom: 1px solid #eee;
                }
            """)
            tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tabla.verticalHeader().setVisible(False)
            tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    
        # Función para crear sección de tabla con título (solo para las 3 primeras tablas)
        def crear_seccion_tabla_horizontal(titulo, tabla, stretch=1):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)
            
            label = QLabel(titulo)
            label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding-bottom: 5px;
                }
            """)
            
            layout.addWidget(label)
            layout.addWidget(tabla)
            tablas_superiores_layout.addWidget(container, stretch)
    
        # Tabla 1: Historial de Horarios
        self.tabla_horarios = QTableWidget()
        configurar_tabla(self.tabla_horarios, ["ID Horario", "Información", "Fecha Registro"])
        crear_seccion_tabla_horizontal("Historial de Horarios:", self.tabla_horarios, 1)
    
        # Tabla 2: Reporte de Rutas
        self.tabla_reporte_rutas = QTableWidget()
        configurar_tabla(self.tabla_reporte_rutas, ["ID Ruta", "Asignaciones", "Retraso Promedio", "Incidencias"])
        crear_seccion_tabla_horizontal("Reporte de Rutas:", self.tabla_reporte_rutas, 1)
    
        # Tabla 3: Reporte de Trenes
        self.tabla_reporte_trenes = QTableWidget()
        configurar_tabla(self.tabla_reporte_trenes, ["ID Tren", "Asignaciones", "Retraso Promedio", "Incidencias"])
        crear_seccion_tabla_horizontal("Reporte de Trenes:", self.tabla_reporte_trenes, 1)
    
        main_layout.addWidget(tablas_superiores_container)
    
        # --- Segunda fila: Historial de Rutas ---
        rutas_label = QLabel("Historial de Rutas:")
        rutas_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 5px;
            }
        """)
        main_layout.addWidget(rutas_label)
        
        self.tabla_rutas = QTableWidget()
        configurar_tabla(self.tabla_rutas, ["ID Ruta", "Información", "Fecha Registro"])
        main_layout.addWidget(self.tabla_rutas)
    
        # --- Tercera fila: Historial de Asignaciones ---
        asignaciones_label = QLabel("Historial de Asignaciones:")
        asignaciones_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 5px;
            }
        """)
        main_layout.addWidget(asignaciones_label)
        
        self.tabla_asignaciones = QTableWidget()
        configurar_tabla(self.tabla_asignaciones, ["ID Asignación", "Información", "Fecha Registro"])
        main_layout.addWidget(self.tabla_asignaciones)
    
        # Botón para actualizar con estilo
        btn_actualizar = QPushButton("Actualizar Datos")
        btn_actualizar.setStyleSheet("""
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
            }
        """)
        btn_actualizar.clicked.connect(self.cargar_datos)
        
        # Contenedor para centrar el botón
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_actualizar)
        btn_layout.addStretch()
        
        main_layout.addWidget(btn_container)

    def cargar_datos(self):
        self.cargar_historial_horarios()
        self.cargar_historial_rutas()
        self.cargar_historial_asignaciones()
        self.generar_reporte_rutas()
        self.generar_reporte_trenes()

    def actualizar_datos(self):
        self.cargar_datos()
        
    def cargar_historial_horarios(self):
        try:
            # 1. Obtener datos
            historial = self.db.fetch_all("""
                SELECT ID_HORARIO, INFORMACION, FECHA_REGISTRO
                FROM HISTORIAL
                WHERE ID_HORARIO IS NOT NULL
            """)

            if not historial:
                self.tabla_horarios.setRowCount(0)
                return

            # 2. Precalcular filas necesarias
            horarios_mostrados = set()
            total_filas = len(historial)  # Filas de historial
            for id_horario, _, _ in historial:
                if id_horario not in horarios_mostrados:
                    horarios_mostrados.add(id_horario)
                    total_filas += 1  # +1 fila por horario actual

            # 3. Configurar tabla
            self.tabla_horarios.setSortingEnabled(False)  # Desactivar ordenamiento temporal
            self.tabla_horarios.setRowCount(total_filas)

            # 4. Llenar datos
            fila = 0
            horarios_mostrados = set()

            for id_horario, info_hist, fecha in historial:
                # Procesar CLOB
                if hasattr(info_hist, 'read'):
                    info_hist = info_hist.read()

                # Datos de historial
                self.tabla_horarios.setItem(fila, 0, QTableWidgetItem(str(id_horario)))
                self.tabla_horarios.setItem(fila, 1, QTableWidgetItem(info_hist))
                self.tabla_horarios.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
                fila += 1

                # Datos de horario actual (solo una vez por ID)
                if id_horario not in horarios_mostrados:
                    horarios_mostrados.add(id_horario)
                    resultado = self.db.fetch_one("""
                        SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI') || ' - ' || 
                               TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI')
                        FROM HORARIO
                        WHERE ID_HORARIO = :1
                    """, [id_horario])

                    if resultado:
                        self.tabla_horarios.setItem(fila, 0, QTableWidgetItem(str(id_horario)))
                        self.tabla_horarios.setItem(fila, 1, QTableWidgetItem("HORARIO ACTUAL: " + resultado[0]))
                        self.tabla_horarios.setItem(fila, 2, QTableWidgetItem(""))
                        fila += 1

            # 5. Ajustes finales
            self.tabla_horarios.setSortingEnabled(True)
            self.tabla_horarios.sortItems(0, Qt.SortOrder.AscendingOrder)
            self.tabla_horarios.resizeColumnsToContents()

        except Exception as e:
            print(f"Error en cargar_historial_horarios: {str(e)}")
            self.tabla_horarios.setRowCount(0)  # Limpiar tabla en caso de error

    def cargar_historial_rutas(self):
        try:
            # 1. Obtener datos del historial
            historial = self.db.fetch_all("""
                SELECT ID_RUTA, INFORMACION, FECHA_REGISTRO
                FROM HISTORIAL
                WHERE ID_RUTA IS NOT NULL
            """)

            if not historial:
                self.tabla_rutas.setRowCount(0)
                return

            # 2. Precalcular el número total de filas necesarias
            rutas_mostradas = set()
            total_filas = len(historial)  # Filas básicas del historial

            # Contar rutas únicas para las filas adicionales
            for id_ruta, _, _ in historial:
                if id_ruta not in rutas_mostradas:
                    rutas_mostradas.add(id_ruta)
                    total_filas += 1  # +1 fila por cada ruta actual

            # 3. Configurar tabla
            self.tabla_rutas.setSortingEnabled(False)  # Desactivar ordenamiento temporal
            self.tabla_rutas.setRowCount(total_filas)

            # 4. Llenar datos
            fila = 0
            rutas_mostradas = set()  # Reiniciamos para el llenado

            for id_ruta, info_hist, fecha in historial:
                # Convertir CLOB si es necesario
                if hasattr(info_hist, 'read'):
                    info_hist = info_hist.read()
                elif not isinstance(info_hist, str):
                    info_hist = str(info_hist)

                # Datos de historial
                self.tabla_rutas.setItem(fila, 0, QTableWidgetItem(str(id_ruta)))
                self.tabla_rutas.setItem(fila, 1, QTableWidgetItem(info_hist))
                self.tabla_rutas.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
                fila += 1

                # Datos de ruta actual (solo una vez por ID)
                if id_ruta not in rutas_mostradas:
                    rutas_mostradas.add(id_ruta)
                    resultado = self.db.fetch_one("""
                        SELECT R.DURACION_ESTIMADA,
                               LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                        FROM RUTA R
                        JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
                        JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                        WHERE R.ID_RUTA = :1
                        GROUP BY R.DURACION_ESTIMADA
                    """, [id_ruta])

                    if resultado:
                        duracion, estaciones = resultado
                        info_actual = f"RUTA ACTUAL: Duración: {duracion}; Orden: {estaciones}"

                        self.tabla_rutas.setItem(fila, 0, QTableWidgetItem(str(id_ruta)))
                        self.tabla_rutas.setItem(fila, 1, QTableWidgetItem(info_actual))
                        self.tabla_rutas.setItem(fila, 2, QTableWidgetItem(""))
                        fila += 1

            # 5. Ajustes finales
            self.tabla_rutas.setSortingEnabled(True)
            self.tabla_rutas.sortItems(0, Qt.SortOrder.AscendingOrder)
            self.tabla_rutas.resizeColumnsToContents()
            self.tabla_rutas.resizeRowsToContents()

        except Exception as e:
            print(f"Error en cargar_historial_rutas: {str(e)}")
            self.tabla_rutas.setRowCount(0)  # Limpiar tabla en caso de error
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los datos de rutas: {str(e)}")

    def cargar_historial_asignaciones(self):
        try:
            # 1. Obtener datos del historial
            historial = self.db.fetch_all("""
                SELECT ID_ASIGNACION, INFORMACION, FECHA_REGISTRO
                FROM HISTORIAL
                WHERE ID_ASIGNACION IS NOT NULL 
                  AND ID_INCIDENCIA IS NULL 
                  AND HORA_REAL IS NULL
                ORDER BY FECHA_REGISTRO DESC
            """)
            
            if not historial:
                self.tabla_asignaciones.setRowCount(0)
                return
    
            # 2. Precalcular el número total de filas
            asignaciones_mostradas = set()
            total_filas = len(historial)  # Filas básicas del historial
            
            # Contar asignaciones únicas para filas adicionales
            for id_asignacion, _, _ in historial:
                if id_asignacion not in asignaciones_mostradas:
                    asignaciones_mostradas.add(id_asignacion)
                    total_filas += 1  # +1 fila por cada asignación actual
    
            # 3. Configurar tabla
            self.tabla_asignaciones.setSortingEnabled(False)
            self.tabla_asignaciones.setRowCount(total_filas)
    
            # 4. Llenar datos
            fila = 0
            asignaciones_mostradas = set()  # Reiniciamos para el llenado
            
            for id_asignacion, info_hist, fecha in historial:
                # Convertir CLOB si es necesario
                if hasattr(info_hist, 'read'):
                    info_hist = info_hist.read()
                elif not isinstance(info_hist, str):
                    info_hist = str(info_hist)
    
                # Datos de historial
                self.tabla_asignaciones.setItem(fila, 0, QTableWidgetItem(str(id_asignacion)))
                self.tabla_asignaciones.setItem(fila, 1, QTableWidgetItem(info_hist))
                self.tabla_asignaciones.setItem(fila, 2, QTableWidgetItem(fecha.strftime('%d-%m-%Y %H:%M')))
                fila += 1
    
                # Datos de asignación actual (solo una vez por ID)
                if id_asignacion not in asignaciones_mostradas:
                    asignaciones_mostradas.add(id_asignacion)
                    
                    # Obtener datos básicos de la asignación
                    datos_asignacion = self.db.fetch_one("""
                        SELECT ID_RUTA, ID_HORARIO, ID_TREN
                        FROM ASIGNACION_TREN
                        WHERE ID_ASIGNACION = :1
                    """, [id_asignacion])
                    
                    if datos_asignacion:
                        id_ruta, id_horario, id_tren = datos_asignacion
                        
                        # Obtener detalles del horario
                        horario = self.db.fetch_one("""
                            SELECT TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI'),
                                   TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI')
                            FROM HORARIO WHERE ID_HORARIO = :1
                        """, [id_horario])
                        hora_inicio, hora_fin = horario if horario else ("?", "?")
                        
                        # Obtener detalles de la ruta
                        ruta = self.db.fetch_one("""
                            SELECT R.DURACION_ESTIMADA,
                                   LISTAGG(E.NOMBRE, ' → ') WITHIN GROUP (ORDER BY RD.ORDEN)
                            FROM RUTA R
                            JOIN RUTA_DETALLE RD ON R.ID_RUTA = RD.ID_RUTA
                            JOIN ESTACION E ON RD.ID_ESTACION = E.ID_ESTACION
                            WHERE R.ID_RUTA = :1
                            GROUP BY R.DURACION_ESTIMADA
                        """, [id_ruta])
                        duracion, estaciones = ruta if ruta else ("?", "?")
                        
                        # Obtener nombre del tren
                        tren = self.db.fetch_one("SELECT NOMBRE FROM TREN WHERE ID_TREN = :1", [id_tren])
                        nombre_tren = tren[0] if tren else "?"
                        
                        # Construir información actual
                        info_actual = (
                            f"ASIGNACIÓN ACTUAL: Duración: {duracion}; "
                            f"Estaciones: {estaciones}; "
                            f"Horario: {hora_inicio}-{hora_fin}; "
                            f"Tren: {nombre_tren}"
                        )
                        
                        # Insertar datos actuales
                        self.tabla_asignaciones.setItem(fila, 0, QTableWidgetItem(str(id_asignacion)))
                        self.tabla_asignaciones.setItem(fila, 1, QTableWidgetItem(info_actual))
                        self.tabla_asignaciones.setItem(fila, 2, QTableWidgetItem(""))
                        fila += 1
    
            # 5. Ajustes finales
            self.tabla_asignaciones.setSortingEnabled(True)
            self.tabla_asignaciones.sortItems(0, Qt.SortOrder.AscendingOrder)
            self.tabla_asignaciones.resizeColumnsToContents()
            self.tabla_asignaciones.resizeRowsToContents()
            
        except Exception as e:
            print(f"Error en cargar_historial_asignaciones: {str(e)}")
            self.tabla_asignaciones.setRowCount(0)
            QMessageBox.warning(self, "Error", 
                f"No se pudieron cargar los datos de asignaciones:\n{str(e)}")

    def generar_reporte_rutas(self):
        try:
            # 1. Obtener todas las rutas actuales
            rutas = self.db.fetch_all("SELECT ID_RUTA FROM RUTA")
            if not rutas:
                self.tabla_reporte_rutas.setRowCount(0)
                return

            # Preparar la tabla
            self.tabla_reporte_rutas.setRowCount(len(rutas))
            self.tabla_reporte_rutas.setSortingEnabled(False)

            for i, (id_ruta,) in enumerate(rutas):
                # 2. Contar asignaciones para esta ruta
                asignaciones = self.db.fetch_one("""
                    SELECT COUNT(*) 
                    FROM ASIGNACION_TREN 
                    WHERE ID_RUTA = :1
                """, [id_ruta])
                num_asignaciones = asignaciones[0] if asignaciones else 0

                # 3. Calcular retraso promedio
                retraso_promedio = self.calcular_retraso_promedio_ruta(id_ruta)

                # 4. Contar incidencias para esta ruta
                incidencias = self.db.fetch_one("""
                    SELECT COUNT(*) 
                    FROM INCIDENCIA I
                    JOIN ASIGNACION_TREN A ON I.ID_ASIGNACION = A.ID_ASIGNACION
                    WHERE A.ID_RUTA = :1
                """, [id_ruta])
                num_incidencias = incidencias[0] if incidencias else 0

                # Insertar datos en la tabla
                self.tabla_reporte_rutas.setItem(i, 0, QTableWidgetItem(str(id_ruta)))
                self.tabla_reporte_rutas.setItem(i, 1, QTableWidgetItem(str(num_asignaciones)))
                self.tabla_reporte_rutas.setItem(i, 2, QTableWidgetItem(f"{retraso_promedio:.1f} min" if retraso_promedio is not None else "N/A"))
                self.tabla_reporte_rutas.setItem(i, 3, QTableWidgetItem(str(num_incidencias)))

            # Ajustes finales
            self.tabla_reporte_rutas.setSortingEnabled(True)
            self.tabla_reporte_rutas.resizeColumnsToContents()

        except Exception as e:
            print(f"Error al generar reporte de rutas: {str(e)}")
            self.tabla_reporte_rutas.setRowCount(0)
            QMessageBox.warning(self, "Error", f"No se pudo generar el reporte: {str(e)}")

    def calcular_retraso_promedio_ruta(self, id_ruta):
        try:
            # 1. Obtener todas las asignaciones para esta ruta
            asignaciones = self.db.fetch_all("""
                SELECT A.ID_ASIGNACION, A.ID_HORARIO
                FROM ASIGNACION_TREN A
                WHERE A.ID_RUTA = :1
            """, [id_ruta])

            if not asignaciones:
                return None

            total_retrasos = 0
            total_registros = 0

            for id_asignacion, id_horario in asignaciones:
                # 2. Obtener horario programado
                horario = self.db.fetch_one("""
                    SELECT 
                        TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'),
                        TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
                    FROM HORARIO
                    WHERE ID_HORARIO = :1
                """, [id_horario])

                if not horario:
                    continue

                hora_salida_prog, hora_llegada_prog = horario

                # 3. Obtener registros históricos con horas reales
                registros = self.db.fetch_all("""
                    SELECT HORA_REAL
                    FROM HISTORIAL
                    WHERE ID_ASIGNACION = :1 
                      AND HORA_REAL IS NOT NULL
                """, [id_asignacion])

                for (hora_real_str,) in registros:
                    # Extraer horas de salida y llegada reales
                    try:
                        # Formato: "HH:mm:ss-HH:mm:ss"
                        hora_salida_real_str, hora_llegada_real_str = hora_real_str.split('-')

                        # Convertir a objetos datetime.time para comparación
                        from datetime import datetime
                        hora_salida_real = datetime.strptime(hora_salida_real_str, '%H:%M:%S').time()
                        hora_llegada_real = datetime.strptime(hora_llegada_real_str, '%H:%M:%S').time()
                        hora_salida_prog_obj = datetime.strptime(hora_salida_prog, '%H:%M:%S').time()
                        hora_llegada_prog_obj = datetime.strptime(hora_llegada_prog, '%H:%M:%S').time()

                        # Calcular diferencia en minutos (considerando días diferentes)
                        def calcular_diferencia_minutos(hora_real, hora_prog):
                            real = datetime.combine(datetime.today(), hora_real)
                            prog = datetime.combine(datetime.today(), hora_prog)
                            if real < prog:  # Si llegó temprano, considerar como 0
                                return 0
                            return (real - prog).total_seconds() / 60

                        retraso_salida = calcular_diferencia_minutos(hora_salida_real, hora_salida_prog_obj)
                        retraso_llegada = calcular_diferencia_minutos(hora_llegada_real, hora_llegada_prog_obj)

                        # Solo considerar retrasos entre 1 y 10 minutos
                        if 0 < retraso_salida <= 10:
                            total_retrasos += retraso_salida
                            total_registros += 1

                        if 0 < retraso_llegada <= 10:
                            total_retrasos += retraso_llegada
                            total_registros += 1

                    except Exception as e:
                        print(f"Error procesando registro {hora_real_str}: {str(e)}")
                        continue

            return total_retrasos / total_registros if total_registros > 0 else 0

        except Exception as e:
            print(f"Error al calcular retraso para ruta {id_ruta}: {str(e)}")
            return None
        
    def generar_reporte_trenes(self):
        try:
            # 1. Obtener todos los trenes actuales
            trenes = self.db.fetch_all("SELECT ID_TREN, NOMBRE FROM TREN")
            if not trenes:
                self.tabla_reporte_trenes.setRowCount(0)
                return

            # Preparar la tabla
            self.tabla_reporte_trenes.setRowCount(len(trenes))
            self.tabla_reporte_trenes.setSortingEnabled(False)

            for i, (id_tren, nombre_tren) in enumerate(trenes):
                # 2. Contar asignaciones para este tren
                asignaciones = self.db.fetch_one("""
                    SELECT COUNT(*) 
                    FROM ASIGNACION_TREN 
                    WHERE ID_TREN = :1
                """, [id_tren])
                num_asignaciones = asignaciones[0] if asignaciones else 0

                # 3. Calcular retraso promedio
                retraso_promedio = self.calcular_retraso_promedio_tren(id_tren)

                # 4. Contar incidencias para este tren
                incidencias = self.db.fetch_one("""
                    SELECT COUNT(*) 
                    FROM INCIDENCIA I
                    JOIN ASIGNACION_TREN A ON I.ID_ASIGNACION = A.ID_ASIGNACION
                    WHERE A.ID_TREN = :1
                """, [id_tren])
                num_incidencias = incidencias[0] if incidencias else 0

                # Insertar datos en la tabla
                self.tabla_reporte_trenes.setItem(i, 0, QTableWidgetItem(f"{id_tren} ({nombre_tren})"))
                self.tabla_reporte_trenes.setItem(i, 1, QTableWidgetItem(str(num_asignaciones)))
                self.tabla_reporte_trenes.setItem(i, 2, QTableWidgetItem(f"{retraso_promedio:.1f} min" if retraso_promedio is not None else "N/A"))
                self.tabla_reporte_trenes.setItem(i, 3, QTableWidgetItem(str(num_incidencias)))

            # Ajustes finales
            self.tabla_reporte_trenes.setSortingEnabled(True)
            self.tabla_reporte_trenes.resizeColumnsToContents()

        except Exception as e:
            print(f"Error al generar reporte de trenes: {str(e)}")
            self.tabla_reporte_trenes.setRowCount(0)
            QMessageBox.warning(self, "Error", f"No se pudo generar el reporte de trenes: {str(e)}")

    def calcular_retraso_promedio_tren(self, id_tren):
        try:
            # 1. Obtener todas las asignaciones para este tren
            asignaciones = self.db.fetch_all("""
                SELECT A.ID_ASIGNACION, A.ID_HORARIO
                FROM ASIGNACION_TREN A
                WHERE A.ID_TREN = :1
            """, [id_tren])

            if not asignaciones:
                return None

            total_retrasos = 0
            total_registros = 0

            for id_asignacion, id_horario in asignaciones:
                # 2. Obtener horario programado
                horario = self.db.fetch_one("""
                    SELECT 
                        TO_CHAR(HORA_SALIDA_PROGRAMADA, 'HH24:MI:SS'),
                        TO_CHAR(HORA_LLEGADA_PROGRAMADA, 'HH24:MI:SS')
                    FROM HORARIO
                    WHERE ID_HORARIO = :1
                """, [id_horario])

                if not horario:
                    continue
                
                hora_salida_prog, hora_llegada_prog = horario

                # 3. Obtener registros históricos con horas reales
                registros = self.db.fetch_all("""
                    SELECT HORA_REAL
                    FROM HISTORIAL
                    WHERE ID_ASIGNACION = :1 
                      AND HORA_REAL IS NOT NULL
                """, [id_asignacion])

                for (hora_real_str,) in registros:
                    # Extraer horas de salida y llegada reales
                    try:
                        # Formato: "HH:mm:ss-HH:mm:ss"
                        hora_salida_real_str, hora_llegada_real_str = hora_real_str.split('-')

                        # Convertir a objetos datetime.time para comparación
                        from datetime import datetime
                        hora_salida_real = datetime.strptime(hora_salida_real_str, '%H:%M:%S').time()
                        hora_llegada_real = datetime.strptime(hora_llegada_real_str, '%H:%M:%S').time()
                        hora_salida_prog_obj = datetime.strptime(hora_salida_prog, '%H:%M:%S').time()
                        hora_llegada_prog_obj = datetime.strptime(hora_llegada_prog, '%H:%M:%S').time()

                        # Calcular diferencia en minutos (considerando días diferentes)
                        def calcular_diferencia_minutos(hora_real, hora_prog):
                            real = datetime.combine(datetime.today(), hora_real)
                            prog = datetime.combine(datetime.today(), hora_prog)
                            if real < prog:  # Si llegó temprano, considerar como 0
                                return 0
                            return (real - prog).total_seconds() / 60

                        retraso_salida = calcular_diferencia_minutos(hora_salida_real, hora_salida_prog_obj)
                        retraso_llegada = calcular_diferencia_minutos(hora_llegada_real, hora_llegada_prog_obj)

                        # Solo considerar retrasos entre 1 y 10 minutos
                        if 0 < retraso_salida <= 10:
                            total_retrasos += retraso_salida
                            total_registros += 1

                        if 0 < retraso_llegada <= 10:
                            total_retrasos += retraso_llegada
                            total_registros += 1

                    except Exception as e:
                        print(f"Error procesando registro {hora_real_str}: {str(e)}")
                        continue
                    
            return total_retrasos / total_registros if total_registros > 0 else 0

        except Exception as e:
            print(f"Error al calcular retraso para tren {id_tren}: {str(e)}")
            return None
        