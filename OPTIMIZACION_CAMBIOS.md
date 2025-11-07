# Registro de cambios de optimización

Este documento anota, por archivo, los cambios realizados durante el proceso de optimización. Cada sección incluye la fecha, el objetivo y un resumen técnico de lo aplicado.

## APP/main.py

Fecha: 2025-10-25

Objetivos:
- Evitar bloqueos del loop de UI ante eventos en tiempo real
- Desacoplar inicialización pesada (lazy-load de vistas)
- Reducir repaints/actualizaciones innecesarias
- Mejorar observabilidad (logging y tiempos)

Cambios:
- Lazy-load de interfaces mediante factories y placeholders: solo se crea la vista al mostrarse por primera vez.
- Coalescing de eventos con QTimer (150 ms): múltiples eventos cercanos se condensan en una sola actualización.
- Actualización de solo la vista visible; las no visibles se marcan "dirty" y se refrescan al entrar.
- Conexión centralizada a eventos con entrega encolada (QueuedConnection) para evitar reentrancias/bloqueos.
- Sustitución de prints por logging configurable (APP_LOG_LEVEL), y medición del tiempo de creación de MainWindow.
- Limpieza en closeEvent: desconexión de señales y parada de timers.
- Micro-opt de UI: setFixedWidth(50) para el menú lateral y splitter no colapsable.

Notas:
- No se modificaron otros archivos.
- Se mantiene compatibilidad intentando refrescar vistas via `actualizar_datos()` o `cargar_datos()` si existen.

## APP/base_de_datos/db.py

Fecha: 2025-10-25

Objetivos:
- Mejorar robustez y rendimiento de acceso a Oracle
- Evitar bloqueos prolongados y mejorar reutilización de recursos
- Aumentar observabilidad con logs y métricas

Cambios aplicados:
- Logging y latencias: reemplazo de prints por logging; cronometraje de operaciones y registro de consultas lentas (umbral configurable: `APP_DB_SLOW_MS`).
- Timeouts y caché: configuración de `call_timeout` y `stmtcachesize` por conexión (por entorno: `APP_DB_CALL_TIMEOUT_MS`, `APP_DB_STMT_CACHE_SIZE`).
- Pool robusto (SessionPool): parámetros configurables (`min`, `max`, `increment`, `timeout`, `wait_timeout`, `ping_interval`, `max_lifetime_session`, `getmode=WAIT`) vía variables `APP_DB_POOL_*`.
- Ajustes por cursor: `arraysize`, `prefetchrows` y `bindarraysize` configurables (`APP_DB_ARRAYSIZE`, `APP_DB_PREFETCHROWS`, `APP_DB_BINDARRAYSIZE`).
- Cierre correcto: cierre explícito del pool con `close(force=True)` y limpieza de referencias.
- Reintentos con backoff: reintentos ante errores recuperables (ORA/DPY/DPI) con backoff breve (`APP_DB_RETRY_BACKOFF_MS`) y conteo de reintentos.
- Contrato de parámetros: uso de `None` en lugar de listas vacías cuando no hay parámetros.
- DSN cacheado: construcción de DSN única por instancia.
- Métricas básicas: `get_metrics()` devuelve consultas totales, lentas y reintentos.
- Thin/Thick (punto 8): se retiró `init_oracle_client(...)` para usar thin por defecto; se agrega log del modo actual (`thin`/`thick`) tras conectar.

Notas anteriores:
- Inicialmente se mantenía la creación de `EventManager(self)` en `connect()` (punto 7 pendiente de coordinar con `event_manager.py`).
- Si se detectan problemas tras retirar `init_oracle_client`, evaluar reintroducirlo de forma opcional o condicional por entorno.

Cambio 7 (2025-10-26): imports perezosos y limpieza
- Se eliminó la creación automática de `EventManager` dentro de `connect()`; ahora la inicialización es explícita a través de `init_event_manager(usuario_id, auto_start=True)`.
- Import perezoso: `EventManager` se importa dentro de `init_event_manager` en lugar de a nivel de módulo.
- Ciclo de vida: `close()` detiene y desasocia el `EventManager` si existe (`stop()` y `detach_from_db()`), y lo borra de la referencia de `db`.
- Coordinación con UI: `APP/main.py` ahora llama `db.init_event_manager(id_usuario)` al iniciar sesión; se eliminó la dependencia directa (`from base_de_datos.event_manager import EventManager`) en `main.py` y en `interfaces/monitoreo.py` (import no usado).

## APP/base_de_datos/event_manager.py

Fecha: 2025-10-26

Objetivo (fase 1):
- Reiniciar los campos `HORA_SALIDA_REAL` y `HORA_LLEGADA_REAL` de `ASIGNACION_TREN` cuando se registre la última llegada del día o al detectar cambio de día, manteniendo la lógica de día agnóstico de horarios/asignaciones.

Cambios aplicados (fase 1):
- Se agrega `self._current_date` para detectar cambio de día en `verificar_eventos()`.
- Nuevo flujo post-evento: tras una llegada exitosa y si no quedan eventos pendientes, se lanza un `DbTask` que pone en `NULL` las horas reales de todas las asignaciones y posteriormente recarga los eventos (`_reset_asignaciones_async`).
- En `verificar_eventos()`, si cambia el día, se dispara el mismo reset asíncrono y, al finalizar, se recargan los eventos del nuevo ciclo.
- El reset se ejecuta en worker `_reset_asignaciones_worker` con `commit`/`rollback` defensivos.

Cambios adicionales realizados (post-fase 1):
- Mejora de detección de llegadas: ahora se cargan eventos del día tanto de SALIDA (cuando `HORA_SALIDA_REAL IS NULL`) como de LLEGADA (cuando `HORA_LLEGADA_REAL IS NULL` y ya hay `HORA_SALIDA_REAL`). Se ordenan por hora y se valida formato de tiempo.
- Recarga inmediata tras SALIDA: al completar una salida se recargan eventos para que las llegadas dependientes queden elegibles sin esperar al verificador periódico.
- Prevención de ejecución masiva tras cambios de fecha: se introduce un filtro de hora mínima (`min_time`) por defecto en "ahora" y una ventana opcional de catch-up controlada por `APP_EVENTS_CATCHUP_MINS` (minutos). Así se evitan ejecuciones de cientos de eventos atrasados salvo que se habilite explícitamente.

Cambios aprobados e implementados (fase 2: 1, 2, 3, 4, 6, 8, 9):
- (1) Logging estructurado: reemplazo de prints por `logging`, logger de módulo `APP.event_manager`, mensajes con contexto (tipo de evento, asignación, hora) y niveles adecuados.
- (2) Programación con un único timer reutilizable y guard anti-solapes: un solo QTimer para el próximo evento, reprogramable; se añade un flag de ejecución para evitar reentradas mientras un evento está en curso; se reprograma al finalizar el worker.
- (3) Verificador periódico único y no intrusivo: consolidado en un único `verification_timer` y protegido por guardas para no interferir mientras hay ejecución en curso.
- (4) Deduplicación de programación: si el próximo evento a programar no cambia (misma asignación/tipo/hora), se evita recrear el timer.
- (6) Método `stop()`: detiene y limpia timers y estado para un apagado ordenado desde la UI.
- (8) Señales de actualización coalescidas con motivo: se añade emisión auxiliar con motivo (p. ej. `"salida"`, `"llegada"`, `"reset"`, `"reload"`) manteniendo compatibilidad con `update_triggered`.
- (9) Métricas básicas del gestor: contadores de salidas/llegadas/resets/errores y marcas de tiempo del último evento; método `get_metrics()` para consulta.

Notas:
- Los puntos (5) y (7) quedan pendientes para la siguiente iteración. El (7) implica coordinación con `db.py` sobre la creación/vida del `EventManager`.

Ajustes adicionales (ruido de logs en ráfagas simultáneas):
- Se añadió una guarda en `programar_proximo_evento()` para no programar si hay un evento en curso, evitando intentos redundantes.
- Se bajó el nivel de mensajes previamente marcados como WARNING a DEBUG/INFO en casos benignos (intento de ejecución durante ráfaga; lista vacía al hacer pop; cambios durante verificación). Resultado: no aparecen advertencias mientras todo funciona correctamente.

Cambios implementados ahora (fase 2: 5 y 7):
- (5) Catch-up/backfill avanzado configurable:
	- `APP_EVENTS_CATCHUP_MODE`: none (por defecto) | window | all | schedule-only.
		- none: sólo eventos futuros.
		- window: incluye vencidos dentro de `APP_EVENTS_CATCHUP_MINS`.
		- all: incluye todo el día y procesa vencidos en lotes controlados.
		- schedule-only: no ejecuta vencidos; descarta eventos atrasados y programa a partir del próximo futuro.
	- `APP_EVENTS_BATCH_SIZE` y `APP_EVENTS_BATCH_DELAY_MS`: cuando el modo es `all`, los vencidos se ejecutan en lotes de tamaño configurable con una pausa entre lotes para evitar ráfagas.
- (7) Coordinación con db:
	- Nuevo parámetro `auto_start` en `EventManager(..., auto_start=True)` para permitir inicialización diferida sin arrancar timers ni cargas iniciales.
	- Métodos `start()`/`stop()` para controlar el ciclo de vida desde fuera.
	- Métodos `attach_to_db()`/`detach_from_db()` y registro seguro de `db.event_manager` si está libre.

Mejora adicional (2025-11-06): Simulación de retrasos
- Se añade simulación de retrasos para SALIDA y LLEGADA con configuración por entorno:
	- `APP_DELAY_ENABLED` (1/true por defecto): activa la simulación.
	- `APP_DELAY_MODE`: `threshold` (por defecto) o `prob`.
		- threshold: `randint(0..MAX)` y si el valor > `THRESHOLD` se usa como retraso, si no 0.
		- prob: con `PROB` (0..1) hay retraso `randint(1..MAX)`; si no, 0.
	- `APP_DELAY_MAX_MINUTES` (15 por defecto), `APP_DELAY_THRESHOLD` (5 por defecto), `APP_DELAY_PROB` (0.35 por defecto).
- Los retrasos aplican tanto en `manejar_salida`/`manejar_llegada` como en los workers `_task_manejar_salida`/`_task_manejar_llegada`.
- Se registran en logs los retrasos simulados aplicados.

## APP/interfaces/login.py

Fecha: 2025-10-26

Objetivos aprobados (2, 3, 4, 6, 8):
- (2) Consulta eficiente y segura: uso de `fetch_one` con parámetros nombrados (`:usuario`, `:pwd`) en vez de `fetch_all` con posicionales.
- (3) Logging prudente y sin credenciales: se eliminan prints de usuario/contraseña; se agrega logger del módulo con mensajes informativos sin exponer datos sensibles.
- (4) Anti-doble click: deshabilitar inputs y botón mientras se verifica, evitando múltiples envíos simultáneos.
- (6) Cierre tras 3 intentos: se mantiene la política de cierre, ahora intentando `QApplication.quit()` de forma ordenada; fallback a `sys.exit()` si no hay instancia.
- (8) Limpieza de imports: unificación de imports de Qt, remoción de no usados.

Ajuste UX:
- Foco tras error: al limpiar la contraseña después de “usuario o contraseña incorrectos”, el foco ahora se aplica con `QTimer.singleShot(0, ...)` para ejecutarse luego de re-habilitar los campos (evita que `setFocus()` se pierda durante el estado ocupado).

## APP/interfaces/usuarios.py

Fecha: 2025-10-26

Cambios aprobados y aplicados:
- (3) SQL parametrizado consistente y uso de helpers del módulo DB: se migran consultas a `fetch_all`, `fetch_one` y `execute_query` con parámetros nombrados, evitando cursores manuales y asegurando commit automático.
- (4) Evitar N+1 al contar historial: se sustituye el bucle de consultas por una única consulta con subselect de conteo por usuario.
- (8) Señales conectadas una sola vez: `itemSelectionChanged` se conecta en `initUI`, eliminando conectar/desconectar en cada carga.
- (10) Logger: se añade `logging.getLogger(__name__)` y se reemplazan prints por logs (sin añadir otras responsabilidades de estado ocupado).

Notas:
- Por indicación, se mantuvo la columna de contraseña sin cambios funcionales (no se ocultó ni retiró).

## APP/interfaces/home.py

Fecha: 2025-10-26

Cambios aprobados y aplicados (1, 2, 3, 4, 5, 6, 9, 14[seq HISTORIAL]):
- (1) Logger y eliminación de prints: se añade `logging.getLogger(__name__)` y se reemplazan prints por logs `debug`.
- (2/14) Acceso BD con helpers y secuencia para HISTORIAL: uso de parámetros nombrados y `execute_query`/`fetch_one`; inserción en `HISTORIAL` con `HISTORIAL_SEQ.NEXTVAL` (compromiso: toda inserción futura a HISTORIAL usará la secuencia).
- (3) Usar ID ya disponible: en cancelar se utiliza `ID_ASIGNACION` tomado de la tabla sin consultar de nuevo por horario.
- (4) Manejo robusto de nulos y tipos: casteo seguro y checks antes de usar resultados.
- (5) Integración segura con EventManager: emisión de `update_triggered` solo si existe; fallback a refresco local.
- (6) Coalescer recargas: se introduce `self._refresh_timer` (single-shot) y `actualizar_datos()` programa la recarga.
- (9) Limpiezas menores: eliminación de `hide()` duplicado, conversión del timer de reloj a atributo y remoción de configuraciones duplicadas de scrollbars.

## APP/interfaces/asignacion.py

Fecha: 2025-10-26

Cambios aprobados y aplicados (1, 2, 3[solo secuencia en HISTORIAL], 4, 8, 10, 11):
- (1) Logger: se añade `logging.getLogger(__name__)` en ambas clases y se reemplazan prints por logs (niveles debug/error).
- (2) Acceso a BD consistente: `confirmar_asignacion` y `confirmar_modificacion` migran a helpers (`execute_query`, `fetch_one`, `fetch_all`) con parámetros nombrados; se elimina el manejo manual de cursores/commit.
- (3) Secuencia para HISTORIAL: en `confirmar_modificacion` las inserciones ahora usan `HISTORIAL_SEQ.NEXTVAL`. No se agregaron nuevas inserciones fuera del flujo existente.
- (4) Emisión segura de eventos: `update_triggered` se emite solo si `db.event_manager` existe y expone la señal, evitando errores si no está inicializado.
- (8) Validaciones y nulos: `confirmar_asignacion` llama a `validar_asignacion()` y verifica `currentData()` no nulo antes de insertar.
- (10) DRY helpers: se extraen `_load_route_image_helper` y `_cargar_rutas_helper` para compartir la lógica entre ambas clases (carga de imagen y rutas).
- (11) SQL expresivo y consistente: consultas con binds nombrados y estilo uniforme; sin concatenación de parámetros.

Notas:
- No se añadieron registros extra a `HISTORIAL`; solo se cambió a `HISTORIAL_SEQ.NEXTVAL` donde ya se insertaba.
- La carga de imágenes ahora centraliza el manejo de LOB/bytes y errores, con escalado suave.

Cambios adicionales aprobados y aplicados (6, 9, 12, 14):
- (6) Evitar N+1 al filtrar horarios: se agrega `_get_asignados_set(...)` para precargar `ID_HORARIO` asignados por ruta (y excluir la asignación actual en modificar). Se elimina el `SELECT COUNT(*)` por cada fila.
- (9) Escalado responsivo de imagen: guardamos el `QPixmap` original al cargar y reescalamos en `resizeEvent` de ambas clases mediante `_rescale_route_image(...)`.
- (12) Mensajería uniforme: se usa `mostrar_mensaje(...)` para estados de éxito/aviso/error en cargas de horarios y trenes; se homogenizan textos.
- (14) Métricas debug ligeras: logs `debug` con conteos (total/filtrados de horarios, trenes disponibles) y tiempos aproximados en ms para diagnósticos.

## APP/interfaces/horarios.py

Fecha: 2025-11-03

Cambios aprobados y aplicados (1, 2, 3, 6, 7, 8, 10, 11, 12, 13):
- (1) Acceso a BD con helpers y parámetros nombrados: migración de operaciones a `fetch_one`/`fetch_all`/`execute_query` con binds nombrados; se evita el cursor manual.
- (2) Secuencia para HISTORIAL: todas las inserciones a `HISTORIAL` usan `HISTORIAL_SEQ.NEXTVAL`.
- (3) Emisión segura de eventos: `update_triggered` se emite solo si existe `db.event_manager` y la señal.
- (6) Logger por módulo: se añade `logging.getLogger(__name__)`; se reemplazan prints por `logger.debug` y se agregan logs informativos en cargas y eliminaciones.
- (7) Transacciones robustas: se ejecutan operaciones de eliminación + historial dentro de un único bloque PL/SQL por llamada (atómico) y con commit automático del helper.
- (8) Carga robusta de imagen de ruta: uso de `fetch_one` y helper `_read_blob_to_bytes` para compatibilidad `LOB/bytes/memoryview`, conservando la escala suave.
- (10) Limpieza de código: se elimina bloque grande de UI comentado (botones antiguos) para mejorar mantenibilidad.
- (11) UX scroll: `singleShot` de 50 ms y verificación de visibilidad del panel antes de desplazar el scroll.
- (12) Mensajes de error informativos: en eliminaciones, se muestran IDs involucrados y pista ante errores de integridad referencial (ORA-02291/02292).
- (13) Validaciones suaves/tipos: helper `_get_selected_id(...)` para castear IDs de forma segura y uso en flujos de edición/eliminación.

Notas:
- Se mantuvo la lógica de confirmación (QMessageBox) existente salvo en `eliminar_asignacion`, que ya usaba `QMessageBox.question` estándar.

## APP/interfaces/paneles/panel_horarios.py

Fecha: 2025-11-04

Cambios aprobados y aplicados (1, 2, 3, 6, 7, 13):
- (1) Uso de helpers de BD con parámetros nombrados en `consultar()` y `confirmar()` de ambas clases; se elimina el manejo manual de cursores.
- (2) Secuencia para `HISTORIAL`: inserción en `InterfazEditarHorario.confirmar` usa `HISTORIAL_SEQ.NEXTVAL`.
- (3) Emisión segura de eventos: `update_triggered` se emite solo si el `EventManager` existe y expone la señal.
- (6) Logger por módulo: se añade `logging.getLogger(__name__)` y logs informativos en consultas/inserciones/actualizaciones y errores.
- (7) Commit/rollback gestionado por helpers: se retiran `commit()`/`rollback()` manuales; los helpers hacen commit automático; en errores se muestra un mensaje y se registra en logs.
- (13) Señales tras éxito real: se emiten `asignacion_exitosa` y `update_triggered` únicamente cuando las operaciones en BD concluyen sin excepción.

Cambio adicional (4) - 2025-11-05:
- Validación de duplicados optimizada: se sustituyeron comprobaciones con `COUNT(*)` por `EXISTS` en `consultar()` y `confirmar()` de ambas clases para evitar escaneos innecesarios y mejorar el rendimiento.

## APP/interfaces/paneles/panel_rutas.py

Fecha: 2025-11-05

Cambios aprobados y aplicados (1, 2, 3, 7, 8, 10, 14, 15):
- (1) Helpers y parámetros nombrados: migración de consultas/actualizaciones a `fetch_one`, `fetch_all`, `execute_query` con binds nombrados. Se eliminan cursores manuales y `commit()/rollback()` explícitos.
- (2) Secuencia para HISTORIAL: inserciones en edición usan `HISTORIAL_SEQ.NEXTVAL`.
- (3) Emisión segura de eventos: `update_triggered` y `asignacion_exitosa` solo tras éxito y con guardas por existencia de señal.
- (7) Manejo robusto de imagen: lectura con try/except; si falla, se continúa sin imagen mostrando aviso.
- (8) Logger por módulo: se añade `logging` y se sustituyen prints/errores silenciosos por logs informativos y de error.
- (10) Creación de estación: verificación de duplicado (case-insensitive) antes de insertar; mensajes amigables.
- (14) Limpieza de imports: unificación y remoción de duplicados/no usados.
- (15) Edición tolerante a “solo duración”: durante edición, si el orden de estaciones es idéntico a la ruta actual:
	- Si la duración es igual: no se actualiza y se informa "Una ruta idéntica ya existe".
	- Si la duración es distinta: se actualiza únicamente la duración (y la imagen si corresponde) y se registra en HISTORIAL.

Ajuste en Consultar (edición):
- El botón Consultar refleja la misma lógica: si solo cambia la duración, informa explícitamente el cambio propuesto (p. ej. "se actualizaría la duración de X a Y"). Si hay una ruta idéntica con distinto ID, bloquea con el mensaje de duplicado.

## APP/interfaces/monitoreo.py

Fecha: 2025-11-05

Cambios aprobados y aplicados (1, 2, 6, 8):
- (1) Logger y eliminación de prints: se añade `logging.getLogger(__name__)` y se reemplazan prints por logs (`debug/info/warning/error/exception`) con contexto.
- (2) Coalescer recargas: se incorpora `self._refresh_timer` (single-shot) y `actualizar_datos()` programa la recarga en 150 ms, evitando ráfagas y parpadeos.
- (6) Integración segura del timer de progreso: se detiene el `timer_progreso` antes de iniciar una nueva selección, y también al cerrar/limpiar el panel; guardas para evitar solapes/excepciones.
- (8) Limpieza de imports: se remueven imports no usados y se consolida la cabecera de imports (se elimina `QFont` y `DatabaseConnection`).

Notas:
- Se añadieron capturas de errores en consultas con mensajes a logs y vaciado seguro de tabla/panel cuando falla la carga.

## APP/interfaces/incidencias.py

Fecha: 2025-11-05

Cambios aprobados y aplicados (1, 2, 3, 4, 6):
- (1) Helpers de BD y parámetros nombrados: migración de consultas en `mostrar_afectaciones_no_resuelta`, `mostrar_afectaciones_resuelta`, `load_incidencias` y `resolver_incidencia` a `fetch_one`/`fetch_all`/`execute_query` con binds nombrados; se elimina el manejo manual de cursores y `commit()/rollback()` explícitos.
- (2) Logger por módulo: se añade `logging.getLogger(__name__)` y se sustituyen prints por logs informativos y de error.
- (3) Emisión y conexión segura de eventos: la conexión a `update_triggered` se realiza solo si existe el `event_manager`; la emisión tras resolver una incidencia se hace con guardas y captura de errores.
- (4) Coalescer de recargas: `actualizar_datos()` ahora programa la recarga con un `QTimer` single-shot (150 ms) para evitar ráfagas y parpadeos; fallback directo si el timer falla.
- (6) Limpieza de imports: se elimina `DatabaseConnection` no utilizado y se consolida la cabecera de imports.

Notas:
- Se mantienen los formatos de hora y las cadenas de ruta existentes (LISTAGG con separadores) para estabilidad visual.
- Ante errores al cargar afectaciones o incidencias, se registran en logs y se vacía la tabla afectada de forma segura.

## APP/interfaces/paneles/panel_incidencias.py

Fecha: 2025-11-05

Cambios aprobados y aplicados (1, 2, 3[consolidado], 4, 6, 7):
- (1) Helpers de BD y binds nombrados: `cargar_asignaciones`, `obtener_info` e `insertar_incidencia` usan `fetch_one`/`fetch_all`/`execute_query` con parámetros nombrados; sin cursores manuales ni `commit()/rollback()` explícitos.
- (2) IDs y auditoría: `INCIDENCIA` usa `NVL(MAX(ID_INCIDENCIA), 0) + 1` por solicitud expresa (no usar secuencias fuera de HISTORIAL); `HISTORIAL` usa siempre `HISTORIAL_SEQ.NEXTVAL` y se inserta en ambos casos (fecha actual o manual).
- (3) `obtener_info` consolidado: una sola consulta devuelve duración, orden de estaciones (LISTAGG), horario y tren; corrige el bug del nombre del tren y reduce latencia.
- (4) Coalescer recargas: `actualizar_datos()` programa la recarga con `QTimer` single-shot (150 ms) y registra en logs; fallback directo en caso de error del timer.
- (6) Emisión segura de eventos: `update_triggered` se emite solo si existe el `event_manager` y la señal; errores capturados en logs.
- (7) Logging y manejo de errores: logger por módulo; captura de excepciones en carga de asignaciones y en inserción con mensajes al usuario y vaciado seguro cuando corresponde.

Notas:
- Se mantienen los separadores "→" en las cadenas de rutas para coherencia visual con otras vistas.
- Se eliminó el intento previo de usar `INCIDENCIA_SEQ` y se fijó la política de ID por `MAX+1` para `INCIDENCIA`.
 - Se eliminó el intento previo de usar `INCIDENCIA_SEQ` y se fijó la política de ID por `MAX+1` para `INCIDENCIA`.

## APP/interfaces/infraestructura.py

Fecha: 2025-11-06

Cambios aprobados y aplicados (1, 2, 3, 5, 6, 7, 12):
- (1) Migración a helpers y binds nombrados: `eliminar_tren` y `eliminar_estacion` ahora usan `execute_query` y parámetros nombrados, sin cursores ni commits manuales.
- (2) Transacción atómica para eliminación de tren: bloque PL/SQL reasigna todas las asignaciones y registra cada cambio; si no hay tren disponible, aborta todo.
- (3) HISTORIAL con secuencia: inserciones dentro del bloque usan `HISTORIAL_SEQ.NEXTVAL` con formato uniforme de `INFORMACION`.
- (5) Logger por módulo: se añade `logging.getLogger(__name__)` y se reemplazan prints por logs informativos y de error.
- (6) Emisión segura de eventos: `update_triggered` se emite sólo si el `EventManager` y la señal existen, con captura de errores.
- (7) Coalescer recargas: se introduce `_refresh_timer` (single-shot 150 ms) y `actualizar_datos()` programa la recarga en vez de ejecutarla inmediatamente.
- (12) Limpieza y reducción de flicker: cargas de tablas con `setUpdatesEnabled(False)` y `setSortingEnabled(False)` durante el llenado; imports reorganizados.

Notas:
- Política mantenida: no se introducen nuevas secuencias fuera de HISTORIAL.
- `resizeRowsToContents()` se mantiene comentado para activarlo manualmente si el volumen de filas es bajo.

## APP/interfaces/paneles/panel_trenes.py

Fecha: 2025-11-06

Cambios aprobados y aplicados (1, 2, 4, 5, 12):
- (1) Migración a helpers de BD: se reemplaza el uso directo de cursores/commit por `fetch_one` y `execute_query` en verificación, inserción y actualización.
- (2) Binds nombrados y verificación case-insensitive: consultas con parámetros nombrados (`:nombre`, `:capacidad`, `:estado`, `:id_tren`) y comparación `UPPER(...)` para detectar duplicados.
- (4) Manejo de errores + logging: se añade `logging.getLogger(__name__)`; los errores se registran con `logger.exception`/`logger.error` y se muestran mensajes adecuados al usuario.
- (5) Emisión segura de eventos: `update_triggered` se emite sólo si existe `event_manager` y la señal; se captura cualquier fallo al emitir.
- (12) Type hints y docstrings: anotaciones en métodos clave y docstrings breves para ambas clases.

Notas:
- No se modificó la lógica de confirmación (diálogo) en edición ni se añadieron validadores de UI, conforme al alcance aprobado.

## APP/interfaces/paneles/panel_estaciones.py

Fecha: 2025-11-06

Cambios aprobados y aplicados (1, 2, 4, 6, 10):
- (1) Migración a helpers de BD: inserción y actualización usan `fetch_one` y `execute_query` con commits gestionados por el helper; se elimina el cursor manual.
- (2) Verificación case-insensitive de duplicados: consultas de disponibilidad usan `UPPER(NOMBRE) = UPPER(:nombre)` tanto en alta como en edición (excluyendo el propio ID).
- (4) Logger por módulo: se añade `logging.getLogger(__name__)` y se registran excepciones con `logger.exception`, además de errores operativos.
- (6) Emisión segura de eventos: `update_triggered` sólo se emite si existe `event_manager` y la señal, con captura de posibles fallos.
- (10) Type hints y docstrings: anotaciones de tipos en métodos y docstrings breves en clases `InterfazAgregarEstacion` e `InterfazEditarEstacion`.

Notas:
- Se mantuvo el comportamiento del diálogo de confirmación en edición (`confirmacion.exec() == 2`) al no estar incluido en los cambios aprobados.
- Mensajes de error genéricos se conservaron (no se incluyó manejo diferenciado de errores no duplicado).
Cambio adicional (2025-11-06):
- Se añadió verificación silenciosa case-insensitive previa a INSERT y UPDATE (punto 2 extendido) para evitar que se inserten nombres que difieran sólo en mayúsculas/minúsculas cuando el usuario no pulsa "Consultar".

## APP/interfaces/optimizacion.py

Fecha: 2025-11-06

Cambios aprobados y aplicados (1, 2[solo secuencia], 3, 5, 6, 7, 14, 16):
- (1) Helpers/binds nombrados: unificación de parámetros nombrados en consultas; eliminación de `DatabaseConnection` no usado. Se mantienen cursores manuales en confirmar/rechazar para transacción única.
- (2) HISTORIAL con secuencia: todas las inserciones a `HISTORIAL` usan `HISTORIAL_SEQ.NEXTVAL`; se retiró el cálculo por `MAX+1`.
- (3) Transacción atómica por confirmación/rechazo: las operaciones DML de confirmar/rechazar se ejecutan dentro de una única transacción con `commit()` al final y `rollback()` en errores.
- (5) Emisión segura de eventos y coalescer: guardas al emitir `update_triggered` y `actualizar_datos()` ahora programa una recarga con `QTimer` single-shot (150 ms).
- (6) Logger por módulo: se añade `logging.getLogger(__name__)`, se reemplaza `print()` por logs y se registran excepciones con contexto.
- (7) Carga optimizada: se eliminan N+1 de horarios originales/nuevos incluyendo `TO_CHAR(...)` y cálculos de +15 min directamente en las consultas de afectadas.
- (14) Type hints y docstrings: anotaciones de tipos en métodos clave y docstring de clase.
- (16) Limpieza de imports: reordenamiento y remoción de imports no utilizados.

Notas:
- No se modificó la lógica de diálogos (`exec()` con valores numéricos) al no estar aprobada en esta ronda.
- La selección de tren disponible sigue realizándose por el primer disponible; se añadieron logs de error en caso de fallos.

## APP/interfaces/mejora.py

Fecha: 2025-11-06

Cambios aprobados y aplicados (1, 2, 3, 5, 6, 7, 10, 11, 12):
- (1) Binds nombrados y helpers: migración a `fetch_one`/`fetch_all`/`execute_query` con parámetros nombrados de forma consistente.
- (2) Logger por módulo: se añade `logging.getLogger(__name__)` y se reemplazan `print()` por logs; manejo de excepciones con `logger.exception`.
- (3) Coalescer de recargas + enganche de evento: `actualizar_datos()` programa recarga con `QTimer` single-shot (150 ms) y se conecta a `db.event_manager.update_triggered` si existe.
- (5) Reducción de N+1: cargas de historial (horarios, rutas, asignaciones) resueltas con consultas en lote y mapeos en memoria.
- (6) Rendimiento UI: uso de `setUpdatesEnabled(False)` y `setSortingEnabled(False)` durante el llenado de tablas para evitar parpadeo.
- (7) Reportes agregados: consultas únicas para conteos de asignaciones e incidencias por ruta y tren.
- (10) Type hints y docstrings: anotaciones y docstring en la clase y métodos públicos clave.
- (11) Limpieza de imports: eliminación de `DatabaseConnection` no usado y consolidación de imports.
- (12) Botón Actualizar: ahora llama a `actualizar_datos()` (coalescido) en lugar de recargar directo.

Cambio adicional (8): retraso promedio en SQL
- Se movió el cálculo de “retraso promedio” a SQL en ambos reportes (rutas y trenes),
  evitando bucles Python y múltiples consultas. La lógica replica la anterior: diferencia en minutos entre hora real y programada para salida y llegada, sólo cuenta si > 0 y <= 10; se promedia sobre todos los registros válidos.
- El formato visual se mantiene: “N/A” cuando no hay datos; en caso contrario, minutos con un decimal.

## APP/interfaces/menu_lateral.py

Fecha: 2025-11-06

Cambios aprobados y aplicados (1, 2, 3, 4):
- (1) Acceso a BD consistente y seguro: `load_user_name` usa `fetch_one` con bind nombrado `:id_usuario`, reemplaza `print()` por logger y maneja errores; fallback a “Usuario” si no hay datos o el ID no es numérico.
- (2) Logger por módulo: `logging.getLogger(__name__)` y logs `debug` en toggles y carga de usuario.
- (3) Limpieza de imports: se eliminan duplicados/no usados y se consolida la cabecera.
- (4) Type hints y docstrings: docstring de clase y anotaciones en métodos públicos; firmas tipadas para eventos de Qt.
