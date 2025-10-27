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
