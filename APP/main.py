from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QSplitter, QMessageBox
from base_de_datos.db import DatabaseConnection  # Importar la clase de conexión a la base de datos
from interfaces.login import LoginInterface
from interfaces.menu_lateral import MenuLateral
from interfaces.home import InterfazHome
from interfaces.horarios import GestionHorariosRutas
from interfaces.monitoreo import MonitoreoInterface
from interfaces.incidencias import GestionIncidencias
from interfaces.infraestructura import GestionInfraestructura
from interfaces.optimizacion import OptimizacionDinamica
from interfaces.asignacion import InterfazAsignacion
from PyQt6.QtWidgets import QStackedWidget
import sys

class MainWindow(QMainWindow):
    def __init__(self, db, id_usuario):
        super().__init__()
        
        self.id_usuario = id_usuario # Aqui se guarda el ID del usuario logueado
        
        self.setWindowTitle('Sistema de Control de Trenes')

        # Configurar conexión a BD
        self.db = db
        
        # Conectar la señal de actualización de eventos
        self.db.event_manager.update_triggered.connect(self.actualizar_interfaz)

        # Crear widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Crear splitter para dividir la interfaz
        splitter = QSplitter()
#comentario test 0

        # 1. Menú lateral
        self.menu = MenuLateral(username="NOMBRE DE USUARIO")
        self.menu.setMinimumWidth(50)
        self.menu.setMaximumWidth(50)  

        # 2. Área de contenido
        self.stacked_widget = QStackedWidget()

        # Crear interfaces y pasar la conexión a la base de datos
        self.interfaces = [
            InterfazHome(self, self.db),
            GestionHorariosRutas(self, self.db),
            MonitoreoInterface(self, self.db),
            GestionIncidencias(self, self.db),
            GestionInfraestructura(self, self.db),
            OptimizacionDinamica(self, self.db),
            InterfazAsignacion(self, self.db)
        ]

        # Conectar la señal de actualización a cada interfaz
        for interfaz in self.interfaces:
            self.db.event_manager.update_triggered.connect(interfaz.actualizar_datos)
            #self.db.event_manager.update_triggered.connect(self.interfaz_home.actualizar_datos)


        for interface in self.interfaces:
            self.stacked_widget.addWidget(interface)

        # Configurar splitter
        splitter.addWidget(self.menu)
        splitter.addWidget(self.stacked_widget)
        splitter.setSizes([50, self.width() - 100])  # Establecer tamaños iniciales

        # Conectar señal del menú
        self.menu.cambio_interfaz.connect(self.cambiar_interfaz)

        main_layout.addWidget(splitter)

        # Mostrar maximizado
        self.showMaximized()

    def cambiar_interfaz(self, index):
        """Cambia a la interfaz seleccionada"""
        self.stacked_widget.setCurrentIndex(index)

    def actualizar_interfaz(self):
        """Actualiza las interfaces cuando ocurre un evento"""
        print("Actualizando interfaz debido a un evento...")
        for interface in self.interfaces:
            if hasattr(interface, 'cargar_datos'):
                interface.cargar_datos()

def main():
    app = QApplication([])

    # Conexión a base de datos
    db = DatabaseConnection("PROYECTO_IS", "123", "localhost", 1521, "orcldb21c")
    if not db.connect():
        QMessageBox.critical(None, "Error", "No se pudo conectar a la base de datos")
        sys.exit()

    # Crear ventana de login
    login = LoginInterface(db)
    login.show()

    # Función que se ejecuta al iniciar sesión correctamente
    def iniciar_sesion_exitoso(id_usuario):
        login.close()
        ventana_principal = MainWindow(db, id_usuario)
        ventana_principal.showMaximized()

    login.login_exitoso.connect(iniciar_sesion_exitoso)

    sys.exit(app.exec())

if __name__ == "__main__":
    #app = QApplication([])
    #window = MainWindow()
    #app.exec()
    #sys.exit(app.exec())
    main()