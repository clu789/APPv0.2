import oracledb
from base_de_datos.event_manager import EventManager

class DatabaseConnection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, username=None, password=None, host=None, port=None, sid=None):
        if self._initialized:
            return

        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.sid = sid
        self.connection = None
        self.cursor = None
        self.event_manager = None  # Inicializar el gestor de eventos
        self._initialized = True

    def connect(self):
        """Establecer la conexión a la base de datos si no está activa"""
        if self.connection and self.connection.ping() is None:
            return True  # Ya hay conexión activa
            
        try:
            dsn = oracledb.makedsn(self.host, self.port, self.sid)
            self.connection = oracledb.connect(
                user=self.username,
                password=self.password,
                dsn=dsn
            )
            self.cursor = self.connection.cursor()
            
            # Iniciar el gestor de eventos
            self.event_manager = EventManager(self)
            
            print("Conexión exitosa a la base de datos Oracle")
            return True
        except oracledb.DatabaseError as e:
            print(f"Error de conexión: {e}")
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
                self.connection.close()
            except oracledb.Error as e:
                print(f"Error al cerrar la conexión: {e}")

    def fetch_all(self, query, params=None):
        """Ejecutar una consulta SELECT y devolver todos los resultados"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or [])
                return cursor.fetchall()
        except oracledb.Error as e:
            print(f"Error en fetch_all: {e}")
            return None

    def fetch_one(self, query, params=None):
        """Ejecutar una consulta SELECT y devolver un solo resultado"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or [])
                return cursor.fetchone()
        except oracledb.Error as e:
            print(f"Error en fetch_one: {e}")
            return None

    def execute_query(self, query, params=None, return_rows=False):
        """
        Ejecutar una consulta (INSERT, UPDATE, DELETE)
        Si return_rows=True, devuelve el número de filas afectadas
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or [])
                rows_affected = cursor.rowcount
                self.connection.commit()
                return rows_affected if return_rows else True
        except oracledb.DatabaseError as e:
            print(f"Error en execute_query: {e}")
            self.connection.rollback()
            return False

    def execute_many(self, query, params_list):
        """Ejecutar múltiples inserciones/actualizaciones en una sola operación"""
        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, params_list)
                rows_affected = cursor.rowcount
                self.connection.commit()
                return rows_affected
        except oracledb.DatabaseError as e:
            print(f"Error en execute_many: {e}")
            self.connection.rollback()
            return 0
            
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