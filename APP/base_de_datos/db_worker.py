from PyQt6.QtCore import QObject, pyqtSignal, QRunnable
import traceback


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(object)
    result = pyqtSignal(object)


class DbTask(QRunnable):
    """QRunnable que ejecuta una función relacionada con la DB en un hilo.

    `func` debe aceptar (conn, *args, **kwargs)
    """
    def __init__(self, db_connection, func, *args, **kwargs):
        super().__init__()
        self.db = db_connection
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        conn = None
        try:
            if getattr(self.db, 'session_pool', None):
                conn = self.db.session_pool.acquire()
            else:
                conn = self.db.connection

            result = self.func(conn, *self.args, **self.kwargs)
            self.signals.result.emit(result)
            self.signals.finished.emit()
        except Exception as e:
            tb = traceback.format_exc()
            self.signals.error.emit((e, tb))
            self.signals.finished.emit()
        finally:
            try:
                if getattr(self.db, 'session_pool', None) and conn:
                    conn.close()
            except Exception:
                pass
