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
if __name__ == "__main__":
    guardar_imagen_ruta(1, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-1-Metro-mapa.png')
    guardar_imagen_ruta(2, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-2-Metro-mapa.png')
    guardar_imagen_ruta(3, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-3-Metro-mapa.png')
    guardar_imagen_ruta(4, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-4-Metro-mapa.png')
    guardar_imagen_ruta(5, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-5-Metro-mapa.png')
    guardar_imagen_ruta(6, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-6-Metro-mapa.png')
    guardar_imagen_ruta(7, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-7-Metro-mapa.png')
    guardar_imagen_ruta(8, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-8-Metro-mapa.png')
    guardar_imagen_ruta(9, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-9-Metro-mapa.png')
    guardar_imagen_ruta(10, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-A-Metro-mapa.png')
    guardar_imagen_ruta(11, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-B-Metro-mapa.png')
    guardar_imagen_ruta(12, r'D:/6 semestre/is/PFinal/APPv0.2/imagenes/Linea-12-Metro-mapa.png')
    print("Imágenes guardadas correctamente en la base de datos.")
    # Cerrar la conexión
    conn.close()
