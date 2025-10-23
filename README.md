# TRACKSYNC — Sistema de Control de Trenes (PyQt6 + Oracle)

Aplicación de escritorio para la gestión operativa de una red de trenes: horarios, rutas, monitoreo en tiempo real, incidencias, infraestructura, optimización y administración de usuarios. Construida con PyQt6 y Oracle Database (vía python-oracledb), lista para ejecutarse en Windows y empaquetarse con PyInstaller.

## Características principales

- Inicio de sesión con rol administrador y usuarios normales
- Panel principal con menú lateral animado y navegación entre módulos
- Módulos incluidos:
  - Home: visión general y acceso rápido
  - Horarios y rutas: gestión de horarios y definición de rutas con estaciones
  - Monitoreo: seguimiento de salidas/llegadas y progreso de trenes
  - Incidencias: registro automático y manual de incidencias (retrasos, averías, emergencias)
  - Infraestructura: consulta y mantenimiento de activos
  - Optimización: cálculos y ajustes dinámicos
  - Mejora continua: historial y métricas
  - Gestión de usuarios: alta/baja/edición (solo admin)
- Gestor de eventos con QThreadPool: programa salidas/llegadas, registra historial e incidencias sin bloquear la UI
- Conexión robusta a Oracle con reconexión/pool de sesiones y manejo de LOBs
- Assets e iconografía integrados para una experiencia moderna

## Requisitos

- Windows 10/11 (probado con PowerShell)
- Python 3.10 o superior (recomendado)
- Oracle Database 21c (puede ser instalación local con OraDB21Home o instancia remota)
- Conectividad a la BD
  - Por defecto la app usa python-oracledb en modo thin (no requiere Oracle Client)
  - Si tienes Oracle Home (p. ej., OraDB21Home), puedes habilitar modo thick (ver abajo)

Paquetes de Python:
- PyQt6
- oracledb

## Instalación

1) Crear y activar un entorno virtual (opcional, recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install PyQt6 oracledb
```

3) Configurar Oracle Database:
- Asegúrate de tener una instancia accesible (local o remota) de Oracle 21c
- Identifica tu service name (PDB) o SID; ejemplos comunes: `orclpdb` o `orclpdb21c`

4) Cargar el esquema y datos de ejemplo (opcional pero recomendado para probar la app):
- Abre `PROYECTO_IS.sql` y ajusta las líneas de conexión a tus credenciales/servicio si es necesario
- Ejecuta el script en tu instancia (SQL*Plus/SQLcl/SQL Developer)

El script crea el usuario `PROYECTO_IS/123`, tablas, secuencias/triggers y datos de ejemplo (trenes, estaciones, rutas, horarios, usuarios, etc.). Si usas un PDB distinto, ajusta el service/TNS de conexión en el script antes de ejecutarlo.

## Configuración de la aplicación

Por defecto, la app intenta conectar a:

```python
# APP/main.py
DatabaseConnection(
    username="PROYECTO_IS",
    password="123",
    host="localhost",
    port=1521,
    sid=None,
    service_name="orclpdb21c"  # ajusta según tu PDB
)
```

Ajusta esos valores en `APP/main.py` si tu entorno es distinto (puedes usar SID en lugar de service_name).

Notas:
- Por defecto, el proyecto utiliza python-oracledb en modo thin, por lo que no requiere Oracle Client.
- Si prefieres usar tu instalación local Oracle 21c (OraDB21Home) y aprovechar tnsnames.ora, wallets o TCPS, puedes activar el modo thick.

### Modo thick (opcional) con Oracle 21c y OraDB21Home

1) Define variables de entorno para tu Oracle Home (ajusta la ruta a tu instalación):

```powershell
$env:ORACLE_HOME = "C:\\app\\<usuario>\\product\\21c\\dbhome_1"
$env:PATH = "$env:ORACLE_HOME\\bin;$env:PATH"
# (opcional si usas tnsnames.ora)
$env:TNS_ADMIN = "$env:ORACLE_HOME\\network\\admin"
```

2) En caso de querer forzar thick desde el código, sustituye la inicialización de cliente en `APP/base_de_datos/db.py` por algo similar a:

```python
import os, oracledb
try:
  lib_dir = os.environ.get("ORACLE_CLIENT_LIB_DIR") or os.path.join(os.environ["ORACLE_HOME"], "bin")
  oracledb.init_oracle_client(lib_dir=lib_dir)  # thick mode
except Exception:
  # fallback a thin si no se encuentra el cliente
  pass
```

3) Con thick mode puedes seguir usando host/port/service_name; si además usas un alias de tnsnames.ora, adapta la creación del DSN en tu código para usar el alias directamente.

## Cómo ejecutar

Desde la raíz del repo:

```powershell
python .\APP\main.py
```

Credenciales de ejemplo (cargadas por `PROYECTO_IS.sql`):
- Admin: usuario `9999`, contraseña `ADMIN_CONTROL_TRENES_0000`
- Usuarios de prueba: ver inserts en `PROYECTO_IS.sql`

## Estructura del proyecto

```
APPv0.2/
├─ APP/
│  ├─ main.py                 # Punto de entrada de la GUI
│  ├─ utils.py                # Utilidades para rutas de recursos
│  ├─ base_de_datos/
│  │  ├─ db.py               # Conexión Oracle (pool, reconexión, helpers)
│  │  ├─ db_worker.py        # Worker QRunnable + señales para tareas BD
│  │  └─ event_manager.py    # Gestor de eventos de trenes (QTimer/QThreadPool)
│  ├─ interfaces/            # Módulos de UI (PyQt6)
│  │  ├─ login.py            # Inicio de sesión (admin/usuario)
│  │  ├─ menu_lateral.py     # Navegación y branding
│  │  ├─ home.py, horarios.py, monitoreo.py, incidencias.py, ...
│  │  └─ paneles/            # Subvistas (estaciones, rutas, trenes, etc.)
│  └─ ControlTrenes.spec     # Especificación PyInstaller (empaquetado)
├─ demo/                     # Mini demos de threading/pool (opcional)
├─ Sources/                  # Conexión OracleXE y scripts auxiliares
├─ PROYECTO_IS.sql           # Script principal de esquema y datos de ejemplo
└─ imagenes/, icons/, ...    # Recursos gráficos
```

## Empaquetado (opcional) con PyInstaller

Hay una especificación `APP/ControlTrenes.spec`. Para generar un ejecutable:

```powershell
python -m pip install pyinstaller
pyinstaller .\APP\ControlTrenes.spec
```

El resultado quedará bajo `APP\build\ControlTrenes` o `dist` según la spec. Verifica que los íconos (`APP/icons/`) se incluyan; la app usa `_MEIPASS` para resolver rutas en modo empaquetado.

## Solución de problemas

- No conecta a Oracle
  - Verifica host/puerto/service_name en `APP/main.py` (en 21c suele ser `orclpdb`)
  - Prueba una conexión independiente (SQL*Plus/SQLcl)
  - Si usas thick, confirma que `oci.dll` se resuelve (PATH incluye `...\bin` de OraDB21Home) y que `TNS_ADMIN` apunta a tu `tnsnames.ora`
  - Si hay errores `DPY-1001`, `DPI-1010`, `ORA-03114`, `ORA-03113`, la capa de reconexión intentará recuperarse; revisa logs de consola
- La UI no muestra íconos
  - Confirma que `APP/icons/` existe y que el `TRACKSYNC.ico/png` esté presente
  - En ejecutable, verifica que los recursos se hayan añadido en la spec
- Login falla siempre
  - Asegura que ejecutaste `PROYECTO_IS.sql`
  - Revisa que la tabla `USUARIO` contenga registros y que la conexión se haga contra el esquema correcto
- Eventos no se disparan
  - El `EventManager` usa hora del sistema y consulta horarios programados; verifica que existan horarios futuros y asignaciones con `HORA_SALIDA_REAL` nula

## Desarrollo

- Estilo: PyQt6 para UI; python-oracledb para BD; QThreadPool para trabajos en segundo plano
- Sugerencia: agregar `requirements.txt` con `PyQt6` y `oracledb` para instalaciones reproducibles
- Tests/Demos: ver carpeta `demo/` para ejemplos de threading sin tocar la app principal

## Licencia

Este proyecto se distribuye con fines educativos. Agrega aquí la licencia que prefieras (por ejemplo, MIT) si planeas publicarlo.
