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
-
## APP/base_de_datos/event_manager.py

Fecha: 2025-10-25

Objetivos:
- Reducir freezes por solapes de verificación y mejorar previsibilidad de timers
- Bajar ruido en consola y mejorar trazabilidad
- Preparar ajustes finos de rendimiento sin cambiar SQL aún

Cambios aplicados (1,2,3,4,5,6,7,8,9):
- Logging estructurado: reemplazo de `print` por `logging` con niveles; mensajes claros por evento y errores en workers.
- Verificación periódica sin solapes: `verification_timer` singleShot y guard `_verificando`; intervalo configurable con `APP_EVENTS_VERIFY_MS` (default 60000 ms).
- Reutilización de timer de próximo evento: `current_timer` único con callback `_on_next_event_timeout` y almacenamiento de `_next_event`.
- Coalescing de señales: se mantiene emisión en workers al finalizar una operación; sin emisiones extra en caminos intermedios.
- Método `stop()`: detiene timers y limpia estado para cambio de sesión/cierre.
- Orden garantizado: lista `eventos_pendientes` ordenada por `hora_programada` tras cargar.
- Configuración por entorno: `APP_EVENTS_VERIFY_MS` para tuning rápido del polling.

- SQL por hora (punto 5): se evita `TO_CHAR` en WHERE/ORDER BY; se usa aritmética de fecha anclada a hoy para comparar solo la hora del día y se ordena por `HORA_EVENTO_DT` nativo; `TO_CHAR` se mantiene solo en SELECT para la UI.
- Menos SELECT redundantes (punto 7): `registrar_historial` acepta `hora_salida_real_str` opcional y los llamadores la pasan cuando ya la tienen, evitando lecturas extra.

Notas:
- La lógica de “solo hora del día” se conserva; no se consideran eventos del día siguiente por diseño.

Notas:
- Se mantiene la creación de `EventManager(self)` en `connect()` (punto 7 pendiente de coordinar con `event_manager.py`).
- Si se detectan problemas tras retirar `init_oracle_client`, evaluar reintroducirlo de forma opcional o condicional por entorno.
