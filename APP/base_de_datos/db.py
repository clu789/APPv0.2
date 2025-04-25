import oracledb

class DatabaseConnection:
    def __init__(self, username, password, host, port, sid):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.sid = sid
        self.connection = None
        self.cursor = None

#self, username="PROYECTO_IS", password="123", host="localhost", port=1521, sid="XE"

    def connect(self):
        """Establecer la conexión a la base de datos"""
        try:
            dsn = oracledb.makedsn(self.host, self.port, self.sid)
            self.connection = oracledb.connect(user=self.username, password=self.password, dsn=dsn)
            self.cursor = self.connection.cursor()
            print("Conexión exitosa a la base de datos Oracle")
        except oracledb.DatabaseError as e:
            print(f"Error de conexión: {e}")
            # Considerar lanzar la excepción nuevamente o retornar un valor que indique el error
            # raise e
            # return False

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
        if self.cursor:
            try:
                self.cursor.execute(query, params or [])
                return self.cursor.fetchall()
            except oracledb.Error as e:
                print(f"Error al ejecutar la consulta fetch_all: {e}")
                return None
        else:
            print("Error: No hay cursor disponible (posiblemente conexión fallida).")
            return None

    def execute_query(self, query, params=None):
        """Ejecutar una consulta (INSERT, UPDATE, DELETE)"""
        if self.cursor and self.connection:
            try:
                self.cursor.execute(query, params)
                self.connection.commit()
            except oracledb.DatabaseError as e:
                print(f"Error al ejecutar la consulta execute_query: {e}")
                self.connection.rollback()
                return False  # Indica que la ejecución falló
            return True   # Indica que la ejecución fue exitosa
        else:
            print("Error: No hay conexión o cursor disponible.")
            return False