import os
import time
import logging
import oracledb
from base_de_datos.event_manager import EventManager

# Intentar que los LOB (CLOB/BLOB) se obtengan ya como strings/bytes para no depender de la conexión luego
try:  # Disponible en versiones recientes de oracledb
    oracledb.defaults.fetch_lobs = True
except Exception:
    pass

# Session pool defaults (pueden override con variables de entorno)
DEFAULT_POOL_MIN = int(os.getenv("APP_DB_POOL_MIN", "1"))
DEFAULT_POOL_MAX = int(os.getenv("APP_DB_POOL_MAX", "5"))
DEFAULT_POOL_INC = int(os.getenv("APP_DB_POOL_INCREMENT", "1"))
DEFAULT_POOL_TIMEOUT = int(os.getenv("APP_DB_POOL_TIMEOUT", "300"))  # segundos inactivos antes de reciclar
DEFAULT_POOL_WAIT_TIMEOUT = int(os.getenv("APP_DB_POOL_WAIT_TIMEOUT", "10"))  # segundos esperando slot
DEFAULT_POOL_PING_INTERVAL = int(os.getenv("APP_DB_POOL_PING_INTERVAL", "60"))  # segundos
DEFAULT_POOL_MAX_LIFETIME = int(os.getenv("APP_DB_POOL_MAX_LIFETIME", "7200"))  # segundos

# Conexión/consulta
DEFAULT_CALL_TIMEOUT_MS = int(os.getenv("APP_DB_CALL_TIMEOUT_MS", "10000"))  # 10s
DEFAULT_STMT_CACHE_SIZE = int(os.getenv("APP_DB_STMT_CACHE_SIZE", "100"))
DEFAULT_ARRAYSIZE = int(os.getenv("APP_DB_ARRAYSIZE", "200"))
DEFAULT_PREFETCHROWS = int(os.getenv("APP_DB_PREFETCHROWS", str(DEFAULT_ARRAYSIZE + 1)))
DEFAULT_BINDARRAYSIZE = int(os.getenv("APP_DB_BINDARRAYSIZE", "200"))

# Observabilidad y reintentos
DEFAULT_SLOW_MS = int(os.getenv("APP_DB_SLOW_MS", "200"))
DEFAULT_RETRY_BACKOFF_MS = int(os.getenv("APP_DB_RETRY_BACKOFF_MS", "200"))

class DatabaseConnection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, username=None, password=None, host=None, port=None, sid=None, service_name=None):
        if self._initialized:
            return

        self._logger = logging.getLogger(__name__)
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.sid = sid
        # Nombre del servicio (PDB). Si se proporciona, se usará en lugar del SID
        self.service_name = service_name
        self.connection = None
        # Eliminamos cursor persistente: cada operación creará su propio cursor
        self.cursor = None  # mantenido por compatibilidad pero no usado
        self.session_pool = None
        self.pool_min = DEFAULT_POOL_MIN
        self.pool_max = DEFAULT_POOL_MAX
        self.pool_inc = DEFAULT_POOL_INC
        self.pool_timeout = DEFAULT_POOL_TIMEOUT
        self.pool_wait_timeout = DEFAULT_POOL_WAIT_TIMEOUT
        self.pool_ping_interval = DEFAULT_POOL_PING_INTERVAL
        self.pool_max_lifetime = DEFAULT_POOL_MAX_LIFETIME

        self._call_timeout_ms = DEFAULT_CALL_TIMEOUT_MS
        self._stmt_cache_size = DEFAULT_STMT_CACHE_SIZE
        self._arraysize = DEFAULT_ARRAYSIZE
        self._prefetchrows = DEFAULT_PREFETCHROWS
        self._bindarraysize = DEFAULT_BINDARRAYSIZE
        self._slow_ms = DEFAULT_SLOW_MS
        self._retry_backoff_ms = DEFAULT_RETRY_BACKOFF_MS

        self._dsn = None
        self.event_manager = None
        # Métricas simples
        self._metrics = {"queries": 0, "slow_queries": 0, "retries": 0}
        self._initialized = True

    def _build_dsn(self):
        if self._dsn:
            return self._dsn
        if self.service_name:
            self._dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
        else:
            self._dsn = oracledb.makedsn(self.host, self.port, self.sid)
        return self._dsn

    def connect(self):
        """Establecer la conexión a la base de datos si no está activa"""
        try:
            if self.connection and self._test_connection():
                return True

            dsn = self._build_dsn()

            # Crear session pool para seguridad en threads
            try:
                self.session_pool = oracledb.SessionPool(
                    user=self.username,
                    password=self.password,
                    dsn=dsn,
                    min=self.pool_min,
                    max=self.pool_max,
                    increment=self.pool_inc,
                    threaded=True,
                    getmode=oracledb.POOL_GETMODE_WAIT,
                    timeout=self.pool_timeout,
                    wait_timeout=self.pool_wait_timeout,
                    ping_interval=self.pool_ping_interval,
                    max_lifetime_session=self.pool_max_lifetime,
                )
                self.connection = self.session_pool.acquire()
            except Exception:
                # Fallback sin pool
                self.session_pool = None
                self.connection = oracledb.connect(user=self.username, password=self.password, dsn=dsn)

            # Mantener comportamiento actual: crear EventManager básico aquí
            # (optimización más fina pospuesta mientras coordinamos con event_manager)
            self.event_manager = EventManager(self)
            self._configure_connection(self.connection)
            try:
                self._logger.info("python-oracledb mode: %s", "thin" if oracledb.is_thin_mode() else "thick")
            except Exception:
                pass
            self._logger.info("Conexión exitosa a la base de datos Oracle")
            return True
        except oracledb.DatabaseError as e:
            self._logger.error("Error de conexión: %s", e)
            return False

    def _test_connection(self):
        """Método alternativo para verificar conexión sin usar ping()"""
        try:
            if self.session_pool:
                # Adquirir una conexión rápida del pool
                conn = self.session_pool.acquire()
                try:
                    with conn.cursor() as c:
                        c.execute("SELECT 1 FROM DUAL")
                finally:
                    conn.close()
                return True
            elif self.connection:
                with self.connection.cursor() as c:
                    c.execute("SELECT 1 FROM DUAL")
                return True
            return False
        except Exception:
            return False

    # --- NUEVO: recrear pool y ensure_connection ---
    def _recreate_pool(self):
        try:
            if not (self.username and (self.sid or self.service_name)):
                return False
            dsn = self._build_dsn()
            self.session_pool = oracledb.SessionPool(
                user=self.username,
                password=self.password,
                dsn=dsn,
                min=self.pool_min,
                max=self.pool_max,
                increment=self.pool_inc,
                threaded=True,
                getmode=oracledb.POOL_GETMODE_WAIT,
                timeout=self.pool_timeout,
                wait_timeout=self.pool_wait_timeout,
                ping_interval=self.pool_ping_interval,
                max_lifetime_session=self.pool_max_lifetime,
            )
            # actualizar conexión principal de referencia
            self.connection = self.session_pool.acquire()
            self._configure_connection(self.connection)
            return True
        except Exception as e:
            self._logger.warning("Error recreando pool: %s", e)
            self.session_pool = None
            return self.connect()

    def ensure_connection(self):
        """Garantiza que exista una conexión válida (recrea si está rota)."""
        try:
            if self.session_pool:
                try:
                    test_conn = self.session_pool.acquire()
                    try:
                        with test_conn.cursor() as c:
                            c.execute("SELECT 1 FROM DUAL")
                    finally:
                        test_conn.close()
                except oracledb.Error as e:
                    if any(code in str(e) for code in ("DPY-1001", "DPI-1010", "ORA-03114", "ORA-03113")):
                        print("Pool inválido, recreando...")
                        return self._recreate_pool()
                    else:
                        raise
                return True
            else:
                if not self.connection or not self._test_connection():
                    return self.connect()
                return True
        except Exception as e:
            self._logger.warning("ensure_connection fallo: %s", e)
            return False

    def close(self):
        """Cerrar la conexión y el cursor"""
        if self.cursor:
            try:
                self.cursor.close()
            except oracledb.Error as e:
                self._logger.debug("Error al cerrar el cursor: %s", e)
        if self.connection:
            try:
                # si connection proviene del pool, close lo devolverá al pool
                self.connection.close()
            except oracledb.Error as e:
                self._logger.debug("Error al cerrar la conexión: %s", e)
        if self.session_pool:
            try:
                # Cerrar explícitamente el pool
                self.session_pool.close(force=True)
                self.session_pool = None
            except Exception:
                pass

    def fetch_all(self, query, params=None):
        """Ejecutar una consulta SELECT y devolver todos los resultados"""
        try:
            return self._run_with_retry('_fetch_all_core', query, params)
        except oracledb.Error as e:
            print(f"Error en fetch_all: {e}")
            return None

    def fetch_one(self, query, params=None):
        """Ejecutar una consulta SELECT y devolver un solo resultado"""
        try:
            return self._run_with_retry('_fetch_one_core', query, params)
        except oracledb.Error as e:
            print(f"Error en fetch_one: {e}")
            return None

    def execute_and_fetch(self, query, params=None):
        """
        Ejecuta una consulta (INSERT/UPDATE/DELETE con RETURNING o SELECT) 
        y devuelve los resultados, haciendo commit.
        """
        try:
            return self._run_with_retry('_execute_and_fetch_core', query, params)
        except oracledb.Error as e:
            print(f"Error en execute_and_fetch: {e}")
            return None

    def execute_query(self, query, params=None, return_rows=False):
        """
        Ejecutar una consulta (INSERT, UPDATE, DELETE)
        Si return_rows=True, devuelve el número de filas afectadas
        """
        try:
            return self._run_with_retry('_execute_query_core', query, params, return_rows=return_rows)
        except oracledb.DatabaseError as e:
            print(f"Error en execute_query: {e}")
            return False

    def execute_many(self, query, params_list):
        """Ejecutar múltiples inserciones/actualizaciones en una sola operación"""
        try:
            return self._run_with_retry('_execute_many_core', query, params_list)
        except oracledb.DatabaseError as e:
            print(f"Error en execute_many: {e}")
            return 0

    # --- Métodos core (sin reintento) ---
    def _acquire_conn(self):
        self.ensure_connection()
        if self.session_pool:
            conn = self.session_pool.acquire()
            self._configure_connection(conn)
            return conn
        self._configure_connection(self.connection)
        return self.connection

    def _configure_connection(self, conn):
        if not conn:
            return
        try:
            # Timeout por llamada en ms
            if getattr(conn, 'call_timeout', None) is not None:
                conn.call_timeout = self._call_timeout_ms
            # Tamaño de caché de sentencias
            if getattr(conn, 'stmtcachesize', None) is not None:
                conn.stmtcachesize = self._stmt_cache_size
        except Exception:
            pass

    def _materialize_lobs_row(self, row):
        if not row:
            return row
        new_row = []
        for col in row:
            if hasattr(col, 'read') and callable(getattr(col, 'read')):
                try:
                    new_row.append(col.read())
                except Exception:
                    new_row.append(str(col))
            else:
                new_row.append(col)
        return tuple(new_row)

    def _fetch_all_core(self, query, params=None):
        conn = self._acquire_conn()
        try:
            t0 = time.perf_counter()
            with conn.cursor() as c:
                c.arraysize = self._arraysize
                c.prefetchrows = self._prefetchrows
                c.execute(query, params if params is not None else None)
                rows = c.fetchall()
            dt = (time.perf_counter() - t0) * 1000
            self._metrics["queries"] += 1
            if dt > self._slow_ms:
                self._metrics["slow_queries"] += 1
                self._logger.debug("fetch_all lento (%.0f ms): %s", dt, query)
            return [self._materialize_lobs_row(r) for r in rows] if rows else []
        finally:
            if self.session_pool and conn:
                conn.close()

    def _fetch_one_core(self, query, params=None):
        conn = self._acquire_conn()
        try:
            t0 = time.perf_counter()
            with conn.cursor() as c:
                c.arraysize = self._arraysize
                c.prefetchrows = self._prefetchrows
                c.execute(query, params if params is not None else None)
                row = c.fetchone()
            dt = (time.perf_counter() - t0) * 1000
            self._metrics["queries"] += 1
            if dt > self._slow_ms:
                self._metrics["slow_queries"] += 1
                self._logger.debug("fetch_one lento (%.0f ms): %s", dt, query)
            return self._materialize_lobs_row(row) if row else None
        finally:
            if self.session_pool and conn:
                conn.close()

    def _execute_and_fetch_core(self, query, params=None):
        conn = self._acquire_conn()
        try:
            t0 = time.perf_counter()
            with conn.cursor() as c:
                c.arraysize = self._arraysize
                c.prefetchrows = self._prefetchrows
                c.execute(query, params if params is not None else None)
                rows = c.fetchall()
                conn.commit()
            dt = (time.perf_counter() - t0) * 1000
            self._metrics["queries"] += 1
            if dt > self._slow_ms:
                self._metrics["slow_queries"] += 1
                self._logger.debug("execute_and_fetch lento (%.0f ms): %s", dt, query)
            return [self._materialize_lobs_row(r) for r in rows] if rows else []
        finally:
            if self.session_pool and conn:
                conn.close()

    def _execute_query_core(self, query, params=None, return_rows=False):
        conn = self._acquire_conn()
        try:
            t0 = time.perf_counter()
            with conn.cursor() as c:
                c.execute(query, params if params is not None else None)
                rows_affected = c.rowcount
                conn.commit()
            dt = (time.perf_counter() - t0) * 1000
            self._metrics["queries"] += 1
            if dt > self._slow_ms:
                self._metrics["slow_queries"] += 1
                self._logger.debug("execute_query lento (%.0f ms): %s", dt, query)
            return rows_affected if return_rows else True
        finally:
            if self.session_pool and conn:
                conn.close()

    def _execute_many_core(self, query, params_list):
        conn = self._acquire_conn()
        try:
            t0 = time.perf_counter()
            with conn.cursor() as c:
                if params_list is None:
                    params_list = []
                c.bindarraysize = min(len(params_list) if hasattr(params_list, '__len__') else DEFAULT_BINDARRAYSIZE, self._bindarraysize)
                c.executemany(query, params_list)
                rows_affected = c.rowcount
                conn.commit()
            dt = (time.perf_counter() - t0) * 1000
            self._metrics["queries"] += 1
            if dt > self._slow_ms:
                self._metrics["slow_queries"] += 1
                self._logger.debug("execute_many lento (%.0f ms): %s", dt, query)
            return rows_affected
        finally:
            if self.session_pool and conn:
                conn.close()

    # --- Reintento genérico ---
    def _run_with_retry(self, core_method_name, *args, **kwargs):
        attempts = 0
        last_exc = None
        while attempts < 2:
            try:
                return getattr(self, core_method_name)(*args, **kwargs)
            except oracledb.Error as e:
                last_exc = e
                msg = str(e)
                if any(code in msg for code in ("DPY-1001", "DPI-1010", "ORA-03114", "ORA-03113", "ORA-00028", "ORA-125", "ORA-03135")):
                    self._logger.warning("Conexion invalida detectada (%s), reintentando (%d)...", e, attempts+1)
                    # Forzar reconexión/pool recreate
                    if self.session_pool:
                        self._recreate_pool()
                    else:
                        self.connect()
                    self._metrics["retries"] += 1
                    # backoff breve
                    time.sleep(self._retry_backoff_ms / 1000.0)
                    attempts += 1
                    continue
                else:
                    raise
        # Si llega aquí, falló dos veces
        raise last_exc
            
    def commit(self):
        """Realiza commit de la transacción actual"""
        if self.connection:
            try:
                self.connection.commit()
                return True
            except oracledb.DatabaseError as e:
                self._logger.error("Error al hacer commit: %s", e)
                return False

    def rollback(self):
        """Realiza rollback de la transacción actual"""
        if self.connection:
            try:
                self.connection.rollback()
                return True
            except oracledb.DatabaseError as e:
                self._logger.error("Error al hacer rollback: %s", e)
                return False

    def init_event_manager(self, usuario_id):
        """Inicializa el EventManager con el usuario_id proporcionado"""
        try:
            self.event_manager = EventManager(self, usuario_id)
            return True
        except Exception as e:
            self._logger.error("Error al inicializar EventManager: %s", e)
            return False

    def get_metrics(self):
        """Devuelve métricas simples de uso/diagnóstico."""
        return dict(self._metrics)