import oracledb
from base_de_datos.event_manager import EventManager
oracledb.init_oracle_client(lib_dir=None)  # fuerza modo thin (útil para evitar errores en Windows)

# Intentar que los LOB (CLOB/BLOB) se obtengan ya como strings/bytes para no depender de la conexión luego
try:  # Disponible en versiones recientes de oracledb
    oracledb.defaults.fetch_lobs = True
except Exception:
    pass

# Session pool defaults
DEFAULT_POOL_MAX = 5

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
        self.pool_max = DEFAULT_POOL_MAX
        self.event_manager = None
        self._initialized = True

    def connect(self):
        """Establecer la conexión a la base de datos si no está activa"""
        try:
            if self.connection and self._test_connection():
                return True

            # Si se proporcionó un service_name (p. ej. orclpdb21c) lo usamos para
            # crear el DSN y conectar al PDB. En caso contrario, se intenta con SID.
            if self.service_name:
                dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
            else:
                dsn = oracledb.makedsn(self.host, self.port, self.sid)

            # Crear session pool para seguridad en threads
            try:
                self.session_pool = oracledb.SessionPool(user=self.username, password=self.password, dsn=dsn,
                                                         min=1, max=self.pool_max, increment=1, threaded=True)
                self.connection = self.session_pool.acquire()
            except Exception:
                # Fallback sin pool
                self.session_pool = None
                self.connection = oracledb.connect(user=self.username, password=self.password, dsn=dsn)

            self.event_manager = EventManager(self)

            print("Conexión exitosa a la base de datos Oracle")
            return True
        except oracledb.DatabaseError as e:
            print(f"Error de conexión: {e}")
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
            if self.service_name:
                dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
            else:
                dsn = oracledb.makedsn(self.host, self.port, self.sid)
            self.session_pool = oracledb.SessionPool(user=self.username, password=self.password, dsn=dsn,
                                                     min=1, max=self.pool_max, increment=1, threaded=True)
            # actualizar conexión principal de referencia
            self.connection = self.session_pool.acquire()
            return True
        except Exception as e:
            print(f"Error recreando pool: {e}")
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
            print(f"ensure_connection fallo: {e}")
            return False

    def close(self):
        """Cerrar la conexión y el cursor"""
        if self.cursor:
            try:
                self.cursor.close()
            except oracledb.Error as e:
                print(f"Error al cerrar el cursor: {e}")
        if self.connection:
            try:
                # si connection proviene del pool, close lo devolverá al pool
                self.connection.close()
            except oracledb.Error as e:
                print(f"Error al cerrar la conexión: {e}")
        if self.session_pool:
            try:
                # Liberar referencia al pool
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
            return self.session_pool.acquire()
        return self.connection

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
            with conn.cursor() as c:
                c.execute(query, params or [])
                rows = c.fetchall()
                return [self._materialize_lobs_row(r) for r in rows] if rows else []
        finally:
            if self.session_pool and conn:
                conn.close()

    def _fetch_one_core(self, query, params=None):
        conn = self._acquire_conn()
        try:
            with conn.cursor() as c:
                c.execute(query, params or [])
                row = c.fetchone()
                return self._materialize_lobs_row(row) if row else None
        finally:
            if self.session_pool and conn:
                conn.close()

    def _execute_and_fetch_core(self, query, params=None):
        conn = self._acquire_conn()
        try:
            with conn.cursor() as c:
                c.execute(query, params or [])
                rows = c.fetchall()
                conn.commit()
                return [self._materialize_lobs_row(r) for r in rows] if rows else []
        finally:
            if self.session_pool and conn:
                conn.close()

    def _execute_query_core(self, query, params=None, return_rows=False):
        conn = self._acquire_conn()
        try:
            with conn.cursor() as c:
                c.execute(query, params or [])
                rows_affected = c.rowcount
                conn.commit()
                return rows_affected if return_rows else True
        finally:
            if self.session_pool and conn:
                conn.close()

    def _execute_many_core(self, query, params_list):
        conn = self._acquire_conn()
        try:
            with conn.cursor() as c:
                c.executemany(query, params_list)
                rows_affected = c.rowcount
                conn.commit()
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
                if any(code in str(e) for code in ("DPY-1001", "DPI-1010", "ORA-03114", "ORA-03113")):
                    print(f"Conexion invalida detectada ({e}), reintentando ({attempts+1})...")
                    # Forzar reconexión/pool recreate
                    if self.session_pool:
                        self._recreate_pool()
                    else:
                        self.connect()
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
                print(f"Error al hacer commit: {e}")
                return False

    def rollback(self):
        """Realiza rollback de la transacción actual"""
        if self.connection:
            try:
                self.connection.rollback()
                return True
            except oracledb.DatabaseError as e:
                print(f"Error al hacer rollback: {e}")
                return False

    def init_event_manager(self, usuario_id):
        """Inicializa el EventManager con el usuario_id proporcionado"""
        try:
            self.event_manager = EventManager(self, usuario_id)
            return True
        except Exception as e:
            print(f"Error al inicializar EventManager: {e}")
            return False