import yaml
import psycopg2
import os
import sys

# Colores para la terminal
VERDE = '\033[92m'
ROJO = '\033[91m'
RESET = '\033[0m'

print(f"\n{VERDE}🔍 INICIANDO DIAGNÓSTICO DEL SISTEMA ETL...{RESET}\n")

# 1. PRUEBA DE CONFIGURACIÓN
print("1️⃣  Verificando archivo config.yaml...")
if not os.path.exists("config.yaml"):
    print(f"{ROJO}❌ Error: No existe config.yaml{RESET}")
    sys.exit()

try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    print(f"{VERDE}✅ Archivo leído correctamente.{RESET}")
    url = config['database']['target_url']
    print(f"   URL Destino detectada: {url[:25]}... (oculto)")
except Exception as e:
    print(f"{ROJO}❌ Error leyendo YAML: {e}{RESET}")
    sys.exit()

# 2. PRUEBA DE CONEXIÓN
print("\n2️⃣  Probando conexión a Supabase...")
try:
    conn = psycopg2.connect(url)
    cursor = conn.cursor()
    print(f"{VERDE}✅ Conexión Exitosa.{RESET}")
except Exception as e:
    print(f"{ROJO}❌ Falló la conexión: {e}{RESET}")
    print("   -> Revisa tu contraseña en config.yaml")
    sys.exit()

# 3. PRUEBA DE TABLAS
print("\n3️⃣  Verificando tablas de destino (QA)...")
tablas_qa = ["clientes_qa", "ordenes_qa", "detalle_ordenes_qa"]
faltantes = []

for t in tablas_qa:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"   Tabla '{t}': {VERDE}OK{RESET} (Tiene {count} filas)")
    except Exception as e:
        print(f"   Tabla '{t}': {ROJO}ERROR - No existe o no se puede leer.{RESET}")
        print(f"   Detalle: {e}")
        conn.rollback() # Necesario para seguir
        faltantes.append(t)

if faltantes:
    print(f"\n{ROJO}⚠️ ERROR CRÍTICO: Faltan tablas en la base de datos.{RESET}")
    print("   Solución: Ve al SQL Editor de Supabase y corre el script de creación de tablas.")
    sys.exit()

# 4. PRUEBA DE ESCRITURA (INSERT)
print("\n4️⃣  Intentando insertar un registro de prueba en 'clientes_qa'...")
try:
    # ID negativo para no estorbar datos reales
    sql = """
        INSERT INTO clientes_qa (id, nombre_completo, email, telefono, tarjeta_credito, etl_batch_id) 
        VALUES (-999, 'Test Diagnostico', 'test@test.com', '000', '000', 'TEST_RUN')
        ON CONFLICT (id) DO NOTHING;
    """
    cursor.execute(sql)
    conn.commit()
    print(f"{VERDE}✅ ¡ÉXITO! Se pudo escribir en la base de datos.{RESET}")
    
    # Limpiamos el dato de prueba
    cursor.execute("DELETE FROM clientes_qa WHERE id = -999")
    conn.commit()
    print(f"   (Dato de prueba borrado correctamente)")

except Exception as e:
    print(f"{ROJO}❌ FALLÓ LA ESCRITURA: {e}{RESET}")
    print("   -> Posible causa: Falta la PRIMARY KEY en la tabla.")
    print("   -> Solución: Ejecuta 'ALTER TABLE clientes_qa ADD PRIMARY KEY (id);' en Supabase.")

print(f"\n{VERDE}🏁 DIAGNÓSTICO FINALIZADO.{RESET}")
conn.close()