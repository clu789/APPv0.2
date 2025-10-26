from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QSplitter, QMessageBox
from PyQt6.QtGui import QIcon
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
import os
import logging
import time
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from base_de_datos.event_manager import EventManager
from interfaces.mejora import MejoraContinua
from interfaces.usuarios import InterfazGestionUsuarios

def _resource_path(*path_parts: str) -> str:
    """Obtiene la ruta absoluta a un recurso, compatible con ejecución normal y empaquetada (PyInstaller)."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, *path_parts)

def _set_windows_app_id(app_id: str) -> None:
    """Establece un AppUserModelID explícito para que Windows muestre el ícono correcto en la barra de tareas.
    Debe llamarse antes de crear ventanas.
    """
    if sys.platform == "win32":
        try:
            import ctypes  # import aquí para evitar import innecesario en otros SO
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            # Si falla, continuamos sin bloquear la app
            pass

class MainWindow(QMainWindow):
    cerrar_sesion_signal = pyqtSignal()
    def __init__(self, db, id_usuario):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        t0 = time.perf_counter()

        #self.id_usuario = id_usuario # Aqui se guarda el ID del usuario logueado
        
        self.setWindowTitle('Sistema de Control de Trenes')
        # Establecer ícono de la ventana (esquina superior izquierda)
        icon_path = _resource_path('icons', 'TRACKSYNC.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Configurar conexión a BD
        self.db = db

        # Estado para manejo de actualizaciones diferidas/coalescidas
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(150)  # ms
        self._update_timer.timeout.connect(self._procesar_actualizacion)
        self._dirty_indices = set()  # vistas que requieren refresh al mostrarse

        # Conectar la señal de actualización de eventos (entrega encolada para no bloquear)
        try:
            self.db.event_manager.update_triggered.connect(
                self._programar_actualizacion,
                Qt.ConnectionType.QueuedConnection,
            )
        except Exception:
            # fallback si la firma de connect no admite el tipo (según versión)
            self.db.event_manager.update_triggered.connect(self._programar_actualizacion)

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
        self.menu = MenuLateral(self.db, id_usuario)
        self.menu.setFixedWidth(50)

        # 2. Área de contenido
        self.stacked_widget = QStackedWidget()

        # Lazy-load: factories por índice para crear cada interfaz bajo demanda
        self._interface_factories = {
            0: lambda self=self, db=self.db, uid=id_usuario: InterfazHome(self, db, uid),
            1: lambda self=self, db=self.db, uid=id_usuario: GestionHorariosRutas(self, db, uid),
            2: lambda self=self, db=self.db: MonitoreoInterface(self, db),
            3: lambda self=self, db=self.db, uid=id_usuario: GestionIncidencias(self, db, uid),
            4: lambda self=self, db=self.db, uid=id_usuario: GestionInfraestructura(self, db, uid),
            5: lambda self=self, db=self.db, uid=id_usuario: OptimizacionDinamica(self, db, uid),
            6: lambda self=self, db=self.db: MejoraContinua(self, db),
            # 7: InterfazAsignacion si se activa en el futuro
        }
        self._interfaces = {}  # índice -> instancia creada
        self._placeholders = {}

        # Insertar placeholders para mantener los índices coherentes
        total_views = len(self._interface_factories)
        for idx in range(total_views):
            ph = QWidget()
            self._placeholders[idx] = ph
            self.stacked_widget.addWidget(ph)

        # Configurar splitter
        splitter.addWidget(self.menu)
        splitter.addWidget(self.stacked_widget)
        splitter.setSizes([50, self.width() - 100])  # Establecer tamaños iniciales
        splitter.setChildrenCollapsible(False)

        # Conectar señal del menú
        self.menu.cambio_interfaz.connect(self.cambiar_interfaz)
        self.menu.cerrar_sesion.connect(self.cerrar_sesion_signal.emit)

        main_layout.addWidget(splitter)

        # Crear y mostrar la primera vista bajo demanda
        self._ensure_interface(0)
        self.stacked_widget.setCurrentIndex(0)

        # Mostrar maximizado
        self.showMaximized()

        t1 = time.perf_counter()
        self._logger.info("MainWindow creada en %.1f ms", (t1 - t0) * 1000)

    def _ensure_interface(self, index: int) -> None:
        """Crea e inserta la interfaz en el índice si aún no existe."""
        if index in self._interfaces:
            return
        factory = self._interface_factories.get(index)
        if not factory:
            return
        widget = factory()
        # Reemplazar placeholder en el mismo índice
        placeholder = self._placeholders.pop(index, None)
        if placeholder is not None:
            self.stacked_widget.removeWidget(placeholder)
            # insertWidget coloca en posición, pero si el índice es > count, lo añade al final
            self.stacked_widget.insertWidget(index, widget)
        else:
            # fallback: añadir al final si no hay placeholder
            self.stacked_widget.addWidget(widget)
        self._interfaces[index] = widget

    def cambiar_interfaz(self, index):
        """Cambia a la interfaz seleccionada"""
        self._ensure_interface(index)
        self.stacked_widget.setCurrentIndex(index)
        # Si estaba marcada como dirty, refrescar al entrar
        if index in self._dirty_indices:
            widget = self._interfaces.get(index)
            if widget is not None:
                self._refresh_widget(widget)
            self._dirty_indices.discard(index)

    def _programar_actualizacion(self) -> None:
        """Coalesce de eventos: programa una actualización de la vista visible y marca el resto como sucia."""
        # Marcar todas las vistas (por índice) como "dirty" excepto la visible
        current = self.stacked_widget.currentIndex()
        self._dirty_indices.update(i for i in self._interface_factories.keys() if i != current)
        if not self._update_timer.isActive():
            self._update_timer.start()

    def _procesar_actualizacion(self) -> None:
        """Ejecuta la actualización de la vista visible de forma segura y ligera."""
        idx = self.stacked_widget.currentIndex()
        widget = self._interfaces.get(idx)
        if widget is None:
            # Si aún no está creada, créala y márcala como limpia
            self._ensure_interface(idx)
            widget = self._interfaces.get(idx)
        if widget is not None:
            self._refresh_widget(widget)
        # la vista visible se considera actualizada
        self._dirty_indices.discard(idx)

    def _refresh_widget(self, widget: QWidget) -> None:
        """Intenta refrescar una vista llamando actualizar_datos() o cargar_datos()."""
        try:
            if hasattr(widget, 'actualizar_datos') and callable(getattr(widget, 'actualizar_datos')):
                widget.actualizar_datos()
            elif hasattr(widget, 'cargar_datos') and callable(getattr(widget, 'cargar_datos')):
                widget.cargar_datos()
        except Exception as e:
            self._logger.warning("Error al refrescar vista %s: %s", type(widget).__name__, e)

    def closeEvent(self, event):
        """Limpieza de conexiones y timers al cerrar la ventana."""
        try:
            self.db.event_manager.update_triggered.disconnect(self._programar_actualizacion)
        except Exception:
            pass
        try:
            if self._update_timer.isActive():
                self._update_timer.stop()
        except Exception:
            pass
        super().closeEvent(event)

def main():
    # Asegura que Windows use el ícono de la app en la barra de tareas
    _set_windows_app_id("APPv0.2.ControlTrenes")

    # Configurar logging básico y nivel por variable de entorno APP_LOG_LEVEL
    log_level_name = os.getenv("APP_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = QApplication([])

    # Estilo global para QMessageBox: fondo consistente y texto blanco
    # Esto aplica a TODOS los QMessageBox de la aplicación sin modificar cada llamada individual.
    app.setStyleSheet(
        """
        QMessageBox { background-color: #0b1522; }
        QMessageBox QLabel, QMessageBox QPushButton { color: white; background-color: #0b1522;}
        """
    )

    # Ícono global de la aplicación
    app_icon_path = _resource_path('icons', 'TRACKSYNC.ico')
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))

    # Conexión a base de datos
    #db = DatabaseConnection("PROYECTO_IS", "123", "localhost", 1521, "XE")
    # Para conectar al PDB, pasar service_name en lugar de SID
    db = DatabaseConnection("PROYECTO_IS", "123", "localhost", 1521, sid=None, service_name="orclpdb21c")
    if not db.connect():
        QMessageBox.critical(None, "Error", "No se pudo conectar a la base de datos")
        sys.exit()

    # Crear ventana de login
    login = LoginInterface(db)
    login.show()

    # Señal cuando es el usuario administrador
    def iniciar_como_admin():
        login.close()
        login.ventana_admin = InterfazGestionUsuarios(db)
        login.ventana_admin.showMaximized()
        def volver_a_login():
            login.ventana_admin.close()
            login.show()
        login.ventana_admin.cerrar_sesion.connect(volver_a_login)

    login.login_es_admin.connect(iniciar_como_admin)

    # Función que se ejecuta al iniciar sesión correctamente
    def iniciar_sesion_exitoso(id_usuario):
        login.close()
        # Pasar el id_usuario al EventManager
        try:
            db.event_manager = EventManager(db, id_usuario)
        except Exception as e:
                QMessageBox.critical(None, "Error", f"No se pudo iniciar el gestor de eventos: {str(e)}")
                return
         #db.event_manager = EventManager(db, id_usuario)
        ventana_principal = MainWindow(db, id_usuario)
        ventana_principal.showMaximized()

        def volver_a_login():
            ventana_principal.close()
            login.show()

        ventana_principal.cerrar_sesion_signal.connect(volver_a_login)

    login.login_exitoso.connect(iniciar_sesion_exitoso)

    sys.exit(app.exec())

if __name__ == "__main__":
    #app = QApplication([])
    #window = MainWindow()
    #app.exec()
    #sys.exit(app.exec())
    main()