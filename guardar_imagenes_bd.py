import os
import oracledb

# Establecer la conexión con la base de datos
#conn = oracledb.connect(user='PROYECTO_IS', password='123', dsn='XE')
conn = oracledb.connect(
    user="PROYECTO_IS",
    password="123",
    dsn="localhost/XE"  # Usa el alias definido en tnsnames.ora
)

# Función para guardar la imagen
def guardar_imagen_ruta(ruta_id, archivo_imagen):
    cursor = conn.cursor()

    # Abrir el archivo de la imagen en modo binario
    with open(archivo_imagen, 'rb') as file:
        imagen_blob = file.read()

    # Consulta para insertar la imagen en la tabla RUTA
    query = """
        UPDATE RUTA 
        SET IMAGEN = :imagen 
        WHERE ID_RUTA = :id_ruta
    """
    
    # Ejecutar la consulta con los parámetros
    cursor.execute(query, {'imagen': imagen_blob, 'id_ruta': ruta_id})
    
    # Confirmar la transacción
    conn.commit()

    # Cerrar el cursor
    cursor.close()

# Ejemplo de uso
guardar_imagen_ruta(1, r'D:\6 semestre\is\PFinal\APPv0.2\imagenes\ruta1.jpg')
guardar_imagen_ruta(2, r'D:\6 semestre\is\PFinal\APPv0.2\imagenes\ruta2.jpg')
guardar_imagen_ruta(3, r'D:\6 semestre\is\PFinal\APPv0.2\imagenes\ruta2_0.png')
guardar_imagen_ruta(4, r'D:\6 semestre\is\PFinal\APPv0.2\imagenes\ruta1.png')
print("Imágenes guardadas correctamente en la base de datos.")
# Cerrar la conexión
conn.close()
