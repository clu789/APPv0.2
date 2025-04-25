# py -m pip install pyqt6
# py -m pip install oracledb
# Importar interfaces
from interfaces.monitoreo import MonitoreoInterface
from interfaces.horarios import GestionHorariosRutas
from interfaces.incidencias import GestionIncidencias
from interfaces.infraestructura import GestionInfraestructura
from interfaces.optimizacion import OptimizacionDinamica
from interfaces.home import InterfazHome
#from interfaces.mejora import AnalisisMejoraContinua

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Sistema de Control de Trenes')

        # Crear widget central y la disposición
        central_widget = QWidget(self)
        central_layout = QHBoxLayout(central_widget)

        # Crear el widget para el menú lateral
        self.menu_lateral = QWidget(self)
        self.menu_lateral.setStyleSheet("background-color: #333; color: white;")
        self.menu_lateral.setFixedWidth(200)
        self.menu_lateral.setGeometry(-200, 0, 200, self.height())  # Inicialmente oculto
        
        # Contenedor principal de interfaces
        self.stacked_widget = QStackedWidget(self)
 
        # Crear botones para cambiar entre interfaces en el menú lateral
        self.boton_interfaz_0 = QPushButton("Home", self)
        self.boton_interfaz_0.clicked.connect(lambda: self.change_interface(0))  

        self.boton_interfaz_1 = QPushButton("Gestión de Horarios", self)
        self.boton_interfaz_1.clicked.connect(lambda: self.change_interface(1))

        self.boton_interfaz_2 = QPushButton("Monitoreo", self)
        self.boton_interfaz_2.clicked.connect(lambda: self.change_interface(2))

        self.boton_interfaz_3 = QPushButton("Incidencias", self)
        self.boton_interfaz_3.clicked.connect(lambda: self.change_interface(3))
        
        self.boton_interfaz_4 = QPushButton("Infraestructura", self)
        self.boton_interfaz_4.clicked.connect(lambda: self.change_interface(4))
        
        self.boton_interfaz_5 = QPushButton("Optimizacion", self)
        self.boton_interfaz_5.clicked.connect(lambda: self.change_interface(5))
        
        #self.boton_interfaz_6 = QPushButton("Mejora Continua", self)
        #self.boton_interfaz_6.clicked.connect(lambda: self.change_interface(5))

        # Crear botón para cerrar el menú lateral
        self.boton_cerrar_menu = QPushButton("Cerrar Menú", self)
        self.boton_cerrar_menu.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.boton_cerrar_menu.clicked.connect(self.toggle_menu)

        # Agregar los botones al menú lateral
        menu_layout = QVBoxLayout()
        menu_layout.addWidget(self.boton_interfaz_0)
        menu_layout.addWidget(self.boton_interfaz_1)
        menu_layout.addWidget(self.boton_interfaz_2)
        menu_layout.addWidget(self.boton_interfaz_3)
        menu_layout.addWidget(self.boton_interfaz_4)
        menu_layout.addWidget(self.boton_interfaz_5)
        #menu_layout.addWidget(self.boton_interfaz_6)
        menu_layout.addWidget(self.boton_cerrar_menu)  # Agregar botón para cerrar el menú
        self.menu_lateral.setLayout(menu_layout)

        # Crear interfaces
        self.interface_0 = InterfazHome(self) 
        self.interface_1 = GestionHorariosRutas(self)  # Crear la interfaz de gestión de horarios
        self.interface_2 = MonitoreoInterface(self)
        self.interface_3 = GestionIncidencias(self)
        self.interface_4 = GestionInfraestructura(self)
        self.interface_5 = OptimizacionDinamica(self)
        #self.interface_6 = AnalisisMejoraContinua(self)

        # Agregar interfaces al QStackedWidget
        self.stacked_widget.addWidget(self.interface_0)
        self.stacked_widget.addWidget(self.interface_1)
        self.stacked_widget.addWidget(self.interface_2)
        self.stacked_widget.addWidget(self.interface_3)
        self.stacked_widget.addWidget(self.interface_4)
        self.stacked_widget.addWidget(self.interface_5) 
        #self.stacked_widget.addWidget(self.interface_6)    

        # Establecer el QStackedWidget como el contenido central
        central_layout.addWidget(self.stacked_widget)

        self.setCentralWidget(central_widget)

        # Maximizar la ventana al iniciar
        self.showMaximized()

    def toggle_menu(self):
        # Alternar visibilidad del menú lateral
        if self.menu_lateral.x() == -200:
            self.menu_lateral.setGeometry(0, 0, 200, self.height())  # Hacer visible
        else:
            self.menu_lateral.setGeometry(-200, 0, 200, self.height())  # Ocultar

    def change_interface(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.toggle_menu()  # Cerrar el menú lateral al cambiar de interfaz

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.showMaximized()  # Asegurarse de que la ventana esté maximizada
    app.exec()
