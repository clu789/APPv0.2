import oracledb

class DatabaseConnection:
    def __init__(self, username="PROYECTO_IS", password="123", host="localhost", port=1521, sid="XE"):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.sid = sid
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establecer la conexión a la base de datos"""
        try:
            dsn = oracledb.makedsn(self.host, self.port, self.sid)
            self.connection = oracledb.connect(user=self.username, password=self.password, dsn=dsn)
            self.cursor = self.connection.cursor()
            print("Conexión exitosa a la base de datos Oracle")
        except oracledb.DatabaseError as e:
            print(f"Error de conexión: {e}")

    def close(self):
        """Cerrar la conexión y el cursor"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def fetch_all(self, query, params=None):
        """Ejecutar una consulta SELECT y devolver todos los resultados"""
        if self.cursor:
            self.cursor.execute(query, params or [])
            return self.cursor.fetchall()
        else:
            print("Error: No hay conexión a la base de datos.")
            return None

    def execute_query(self, query, params=None):
        """Ejecutar una consulta (INSERT, UPDATE, DELETE)"""
        if self.cursor:
            try:
                self.cursor.execute(query, params)
                self.connection.commit()
            except oracledb.DatabaseError as e:
                print(f"Error al ejecutar la consulta: {e}")
                self.connection.rollback()
        else:
            print("Error: No hay conexión a la base de datos.")

# --- Ejemplo de uso (puedes descomentar para probar) ---
if __name__ == "__main__":
    db_conn = DatabaseConnection()  # Utiliza los valores predeterminados
    db_conn.connect()

    if db_conn.connection:
        # Ejemplo de consulta
        query = "SELECT SYSDATE FROM DUAL"
        result = db_conn.fetch_all(query)
        if result:
            print(f"Fecha del servidor: {result[0][0]}")

        db_conn.close()