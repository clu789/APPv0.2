import os
import sys

def obtener_ruta_recurso(ruta_relativa):
    """Devuelve la ruta absoluta del recurso, compatible con ejecución directa y PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)
