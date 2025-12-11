import yaml
import psycopg2
import requests
from faker import Faker
import random
import sys

# Configuración
NUM_REGISTROS = 100
fake = Faker('es_MX')
API_URL = f"https://randomuser.me/api/?results={NUM_REGISTROS}&nat=mx"

def cargar_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

def generar_datos_inteligentes():
    # Buffer para capturar logs y mandarlos a la web
    log_buffer = []
    def log(texto):
        print(texto)
        log_buffer.append(str(texto))

    config = cargar_config()
    
    log(f"🔌 Conectando a la Fuente para buscar último ID...")
    try:
        conn = psycopg2.connect(config['database']['source_url'])
        cursor = conn.cursor()
        
        # 1. BUSCAR EL ID MÁXIMO ACTUAL
        cursor.execute("SELECT COALESCE(MAX(id), 99) FROM clientes")
        ultimo_id = cursor.fetchone()[0]
        log(f"   📊 Último ID encontrado: {ultimo_id}")
        log(f"   🚀 Generando registros del {ultimo_id + 1} al {ultimo_id + NUM_REGISTROS}...")

        # 2. DESCARGAR DATOS DE API
        log(f"🌍 Conectando a API RandomUser...")
        response = requests.get(API_URL)
        datos_api = response.json()['results']

        # 3. INSERTAR
        for i, persona in enumerate(datos_api):
            nuevo_id = ultimo_id + 1 + i
            nombre = f"{persona['name']['first']} {persona['name']['last']}"
            email = persona['email']
            telefono = persona['phone']
            tarjeta = fake.credit_card_number()
            
            sql = "INSERT INTO clientes (id, nombre_completo, email, telefono, tarjeta_credito) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nuevo_id, nombre, email, telefono, tarjeta))

        # 4. ORDENES Y DETALLES
        for i in range(NUM_REGISTROS):
            nid = ultimo_id + 1 + i
            fecha = fake.date_this_year()
            total = round(random.uniform(100, 5000), 2)
            cursor.execute("INSERT INTO ordenes (id, cliente_id, fecha_orden, total) VALUES (%s, %s, %s, %s)", (nid, nid, fecha, total))
            
            prod = fake.word()
            cant = random.randint(1, 5)
            cursor.execute("INSERT INTO detalle_ordenes (id, orden_id, producto, cantidad) VALUES (%s, %s, %s, %s)", (nid, nid, prod, cant))

        conn.commit()
        cursor.close()
        conn.close()
        log(f"✅ ¡Éxito! Se inyectaron {NUM_REGISTROS} registros NUEVOS.")
        return "\n".join(log_buffer)
        
    except Exception as e:
        err = f"❌ Error generando datos: {e}"
        log(err)
        return err

if __name__ == "__main__":
    generar_datos_inteligentes()