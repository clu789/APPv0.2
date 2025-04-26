#from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
#from PyQt6.QtCore import Qt
#
#class MenuLateral(QWidget):
#    def __init__(self, main_window):
#        super().__init__(main_window)
#        self.main_window = main_window  # Referencia a MainWindow
#        self.setFixedWidth(200)  # Ancho del menú
#        self.setGeometry(-200, 0, 200, main_window.height())  # Inicialmente oculto
#
#        self.layout = QVBoxLayout()
#        self.setLayout(self.layout)
#        self.setStyleSheet("background-color: #2E2E2E; color: white;")  # Estilo
#
#        # Botones de navegación
#        self.btn_horarios = QPushButton("Horarios y Rutas")
#        self.btn_infraestructura = QPushButton("Infraestructura")
#        self.btn_monitoreo = QPushButton("Monitoreo")
#        self.btn_incidencias = QPushButton("Incidencias")
#        self.btn_optimizacion = QPushButton("Optimización")
#        self.btn_analisis = QPushButton("Análisis")
#
#        # Agregar botones al layout
#        for btn in [self.btn_horarios, self.btn_infraestructura, self.btn_monitoreo, 
#                    self.btn_incidencias, self.btn_optimizacion, self.btn_analisis]:
#            btn.setStyleSheet("background-color: #4A4A4A; color: white; border: none; padding: 10px;")
#            btn.clicked.connect(self.cambiar_interfaz)
#            self.layout.addWidget(btn)
#
#    def cambiar_interfaz(self):
#        boton = self.sender()  # Identificar qué botón fue presionado
#        if boton == self.btn_horarios:
#            self.main_window.stack.setCurrentWidget(self.main_window.gestion_horarios)
#        elif boton == self.btn_infraestructura:
#            self.main_window.stack.setCurrentWidget(self.main_window.gestion_infraestructura)
#        elif boton == self.btn_monitoreo:
#            self.main_window.stack.setCurrentWidget(self.main_window.monitoreo_interface)
#        elif boton == self.btn_incidencias:
#            self.main_window.stack.setCurrentWidget(self.main_window.gestion_incidencias)
#        elif boton == self.btn_optimizacion:
#            self.main_window.stack.setCurrentWidget(self.main_window.optimization_interface)
#        elif boton == self.btn_analisis:
#            self.main_window.stack.setCurrentWidget(self.main_window.analysis_interface)
#
#        self.main_window.menu_lateral.setVisible(False)  # Ocultar el menú al cambiar de interfaz
#