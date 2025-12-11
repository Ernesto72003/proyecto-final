import yaml
import psycopg2
from psycopg2 import extras # ### PUNTO 9: Necesario para Batch Inserts (Rendimiento) ###
import hashlib
import json   # ### NUEVO: Necesario para guardar el archivo de estado (memoria) ###
import os     # ### NUEVO: Necesario para verificar si el archivo existe ###
import uuid      # ### PUNTO 5: Generar ID único de ejecución ###
import datetime # ### PUNTO 5: Capturar hora inicio/fin ###
import time      # ### PUNTO 6: Necesario para esperar entre reintentos ###
import sys       # ### PUNTO 10: Necesario para leer argumentos de línea de comandos ###
from faker import Faker

# --- FIX PARA QUE APP.PY LO ENCUENTRE SIEMPRE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_CONFIG = os.path.join(BASE_DIR, "config.yaml")
ARCHIVO_ESTADO = os.path.join(BASE_DIR, "state.json")
ARCHIVO_LOGS = os.path.join(BASE_DIR, "logs_historial.json") # ### PUNTO 5: Nombre del archivo local de logs ###

# Inicializar Faker para datos falsos (México)
fake = Faker('es_MX')

# ### PUNTO 6: CONFIGURACIÓN DE REINTENTOS ###
MAX_REINTENTOS = 3
TIEMPO_ESPERA = 1 # Segundos (Constante, NO exponencial)

# ### PUNTO 9: CONFIGURACIÓN DE RENDIMIENTO ###
BATCH_SIZE = 1000 # Insertaremos de 1000 en 1000 registros para mayor velocidad
# ---------------------------------------------

# Variable global para capturar logs hacia la web
LOG_BUFFER = []
def print_log(texto):
    print(texto)
    LOG_BUFFER.append(str(texto))

# --- CARGAR CONFIGURACIÓN ---
def cargar_config():
    try:
        with open(ARCHIVO_CONFIG, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print_log("❌ Error: No se encontró el archivo config.yaml")
        return None

# --- FUNCIONES DE ESTADO (MEMORIA) ---
# ### NUEVO: Funciones para leer y guardar hasta dónde nos quedamos ###
def cargar_estado():
    if os.path.exists(ARCHIVO_ESTADO):
        with open(ARCHIVO_ESTADO, "r") as f:
            return json.load(f)
    return {}

def guardar_estado(estado):
    with open(ARCHIVO_ESTADO, "w") as f:
        json.dump(estado, f, indent=4)

# ### PUNTO 6: FUNCIONES AUXILIARES PARA REINTENTOS ###
def conectar_con_reintentos(url):
    """Intenta conectar N veces antes de fallar"""
    for i in range(MAX_REINTENTOS):
        try:
            return psycopg2.connect(url)
        except Exception as e:
            print_log(f"   ⚠️  Falla de conexión (Intento {i+1}/{MAX_REINTENTOS}): {e}")
            if i < MAX_REINTENTOS - 1:
                time.sleep(TIEMPO_ESPERA)
            else:
                raise e # Si fallan todos, lanzamos el error real

def ejecutar_sql_con_reintentos(cursor, sql, params=None):
    """Intenta ejecutar SQL N veces ante errores operativos (Para comandos simples)"""
    for i in range(MAX_REINTENTOS):
        try:
            cursor.execute(sql, params)
            return # Éxito
        except Exception as e:
            try: cursor.connection.rollback()
            except: pass
            
            print_log(f"   ⚠️  Error SQL (Intento {i+1}/{MAX_REINTENTOS}): {e}")
            if i < MAX_REINTENTOS - 1:
                time.sleep(TIEMPO_ESPERA)
            else:
                raise e # Fallo definitivo

# ### PUNTO 9: NUEVA FUNCIÓN PARA INSERTAR POR LOTES (BATCH) ###
def ejecutar_batch_con_reintentos(cursor, sql, lista_datos):
    """Ejecuta inserciones masivas de forma segura y eficiente (Batch)"""
    if not lista_datos: return # Si la lista está vacía, no hace nada

    for i in range(MAX_REINTENTOS):
        try:
            # CORRECCIÓN AQUÍ: Usamos execute_values (compatible con VALUES %s)
            # Antes usabas execute_batch que es para otro formato y causaba el error de string formatting
            extras.execute_values(cursor, sql, lista_datos, page_size=BATCH_SIZE)
            return # Éxito
        except Exception as e:
            try: cursor.connection.rollback()
            except: pass
            
            print_log(f"   ⚠️  Error Batch (Intento {i+1}/{MAX_REINTENTOS}): {e}")
            if i < MAX_REINTENTOS - 1:
                time.sleep(TIEMPO_ESPERA)
            else:
                raise e
# --------------------------------------------------------------

# --- FUNCIONES DE ENMASCARAMIENTO ---

def mascara_hash_email(valor_original):
    """Convierte el email en un Hash SHA256 (Determinístico)"""
    if not valor_original: return None
    salt = "SECRETO_CLASE_ABD" # Semilla para variar el hash
    hash_object = hashlib.sha256((valor_original + salt).encode())
    return f"{hash_object.hexdigest()[:12]}@dominio.com"

def mascara_redaccion(valor_original):
    """Oculta todo menos los últimos 4 caracteres"""
    if not valor_original: return None
    # Si es muy corto, no mostramos nada para seguridad
    if len(valor_original) < 5: return "" 
    return "---" + valor_original[-4:]

def mascara_sintetica_nombre(valor_original):
    """Genera un nombre falso aleatorio"""
    return fake.name()

def mascara_preservar_formato(valor_original):
    """Mantiene formato de teléfono pero cambia números"""
    if not valor_original: return None
    # Generamos números al azar
    nums = fake.numerify(text="##########") 
    # Forzamos el formato +52 (XXX) ...
    return f"+52 ({nums[:3]}) {nums[3:6]}-{nums[6:]}"

# Diccionario que conecta el YAML con las funciones de Python
MAPPING_FUNCIONES = {
    "hash_email": mascara_hash_email,
    "redact_last4": mascara_redaccion,
    "faker_name": mascara_sintetica_nombre,
    "preserve_format": mascara_preservar_formato
}

# --- PROCESO ETL PRINCIPAL ---

# Modificado para recibir argumentos de la Web
def ejecutar_migracion(rol_web=None, opcion_web=None):
    global LOG_BUFFER
    LOG_BUFFER = [] # Limpiar logs
    
    # ### PUNTO 10: MODOS AUTOMÁTICO (SCHEDULER) Y MANUAL ###
    # Si recibimos argumentos desde la web, los usamos. Si no, revisamos sys.argv
    if rol_web and opcion_web:
        usuario_rol = rol_web
        opcion = str(opcion_web)
        print_log(f"\n🤖 MODO WEB: {usuario_rol} - Opción {opcion}")
    elif len(sys.argv) > 2:
        usuario_rol = sys.argv[1].lower()
        opcion = sys.argv[2]
        print_log(f"\n🤖 MODO AUTOMÁTICO (Scheduler) DETECTADO")
        print_log(f"   Rol: {usuario_rol}")
        print_log(f"   Opción: {opcion}")
    else:
        # ### PUNTO 8: SISTEMA DE LOGIN Y ROLES (RBAC) - MANUAL ###
        # Este bloque solo se usa si corres python main.py directo
        usuario_rol = "dev" # Default para pruebas manuales si no hay args
        opcion = "3" 
    # -----------------------------------------------

    # ### PUNTO 5: INICIO DE AUDITORÍA ###
    execution_id = str(uuid.uuid4())   # Generamos un ID único para este reporte
    fecha_inicio = datetime.datetime.now()
    log_detalles = [] # Lista para guardar el reporte de cada tabla
    total_registros_global = 0
    # -----------------------------------

    config = cargar_config()
    estado = cargar_estado() # ### NUEVO: Cargamos la memoria al iniciar ###
    
    print_log(f"🚀 Iniciando Ejecución ID: {execution_id}") # ### PUNTO 5 ###
    print_log(f"👤 Usuario: {usuario_rol.upper()}") # ### PUNTO 8: Mostramos quién está logueado ###

    # Interpretación de opciones
    es_incremental = (opcion == "2")
    es_dry_run = (opcion == "3") # ### PUNTO 10: Bandera para modo ensayo ###

    # ### PUNTO 8: VALIDACIÓN DE PERMISOS (RBAC) ###
    # El operador NO puede hacer carga completa (borrar datos)
    # Nota: El modo ensayo (3) es seguro, así que el operador sí puede usarlo.
    if usuario_rol == "operador" and opcion == "1":
        print_log("\n⛔ ACCESO DENEGADO (Violación de Seguridad)")
        print_log("El rol 'OPERADOR' no tiene permisos para ejecutar Carga COMPLETA (Truncado).")
        print_log("Contacte al administrador de base de datos Ernesto.") # <--- ¡AQUÍ ESTÁ TU CAMBIO! 😎
        
        # Registramos el intento fallido en el log de auditoría local (Requisito de seguridad)
        fecha_fin = datetime.datetime.now()
        log_final = {
            "execution_id": execution_id,
            "inicio": str(fecha_inicio),
            "fin": str(fecha_fin),
            "usuario": usuario_rol,
            "error_seguridad": "Intento no autorizado de Carga Completa",
            "resultado": "BLOQUEADO"
        }
        # Guardamos log local del intento fallido
        historial = []
        if os.path.exists(ARCHIVO_LOGS):
            try:
                with open(ARCHIVO_LOGS, "r") as f: historial = json.load(f)
            except: pass
        historial.append(log_final)
        with open(ARCHIVO_LOGS, "w") as f: json.dump(historial, f, indent=4)
        
        return "\n".join(LOG_BUFFER) # TERMINAMOS EL PROGRAMA AQUÍ POR SEGURIDAD
    # ---------------------------------------

    # 1. CONEXIÓN A LA BASE DE DATOS (CON REINTENTOS)
    print_log("🔌 Conectando a Supabase (con soporte a fallos)...")
    try:
        # ### PUNTO 6: Usamos la función segura ###
        conn_source = conectar_con_reintentos(config['database']['source_url'])
        cursor_source = conn_source.cursor()
        
        conn_target = conectar_con_reintentos(config['database']['target_url'])
        cursor_target = conn_target.cursor()
        
    except Exception as e:
        print_log(f"❌ Error crítico: No se pudo conectar tras {MAX_REINTENTOS} intentos.")
        return "\n".join(LOG_BUFFER)

    # ### PUNTO 10: LÓGICA DRY-RUN (ENSAYO) ###
    if es_dry_run:
        print_log("\n🧪 MODO ENSAYO ACTIVADO: No se modificarán datos.")
        print_log("   Validando conexiones y conteos...")
        
        for tabla_info in config['tablas']:
            nombre = tabla_info['nombre']
            try:
                # Solo contamos en origen
                cursor_source.execute(f"SELECT COUNT(*) FROM {nombre}")
                conteo = cursor_source.fetchone()[0]
                print_log(f"   ✅ Tabla '{nombre}': Conexión OK. Registros disponibles: {conteo}")
            except Exception as e:
                print_log(f"   ❌ Error validando tabla '{nombre}': {e}")
        
        print_log("\n🏁 Ensayo finalizado. Ningún dato fue alterado.")
        return "\n".join(LOG_BUFFER) # Terminamos aquí si es ensayo, no borramos ni insertamos nada.
    # ----------------------------------------

    # ### PUNTO 7: CORRECCIÓN DE LIMPIEZA (Borrar Hijos -> Padres) ###
    # Esto evita el error de Foreign Key Constraint al borrar
    if not es_incremental:
        print_log("\n🧹 MODO COMPLETO: Ejecutando limpieza en orden inverso...")
        tablas_borrar = ["detalle_ordenes_qa", "ordenes_qa", "clientes_qa"]
        
        for t in tablas_borrar:
            print_log(f"   🗑  Limpiando tabla: {t}...")
            try:
                ejecutar_sql_con_reintentos(cursor_target, f"DELETE FROM {t};")
                conn_target.commit()
                # Reseteamos la memoria de esa tabla
                nombre_base = t.replace("_qa", "")
                estado[nombre_base] = 0 
            except Exception as e:
                print_log(f"   ⚠️ No se pudo limpiar {t}: {e}")
    # ---------------------------------------------------------------

    # 2. PROCESAR CADA TABLA DEFINIDA EN EL YAML
    for tabla_info in config['tablas']:
        nombre_tabla = tabla_info['nombre']
        reglas = tabla_info['columnas_enmascarar']
        col_inc = tabla_info.get('columna_incremental', 'id') # ### NUEVO: Leemos qué columna usar para incremental (default: id) ###
        
        # ### PUNTO 5: Crear diccionario de estadísticas para esta tabla ###
        stats_tabla = {
            "tabla": nombre_tabla,
            "registros_leidos": 0,
            "registros_insertados": 0,
            "reglas_aplicadas": list(reglas.keys()),
            "errores": [] # ### PUNTO 6: Agregamos lista de errores ###
        }
        # ----------------------------------------------------------------

        print_log(f"\n🔄 Procesando tabla: {nombre_tabla.upper()}")

        # Extraer datos (Extract)
        try:
            # Leemos el filtro del YAML. Si está vacío, no pone nada.
            filtro_base = tabla_info.get('filtro_sql', '') 
            
            # ### NUEVO: Modificar el SQL para carga incremental ###
            sql_final = f"SELECT * FROM {nombre_tabla} {filtro_base}"
            
            if es_incremental:
                ultimo_valor = estado.get(nombre_tabla, 0)
                print_log(f"   ℹ  Modo INCREMENTAL: Buscando nuevos registros > {ultimo_valor}")
                
                # Inyectamos la condición WHERE id > ultimo_valor
                if "WHERE" in sql_final.upper():
                    # Si ya tiene WHERE, agregamos AND
                    sql_final = sql_final.replace("WHERE", f"WHERE {col_inc} > {ultimo_valor} AND")
                elif "LIMIT" in sql_final.upper():
                     # Si tiene LIMIT pero no WHERE, insertamos el WHERE antes del LIMIT
                     partes = sql_final.upper().split("LIMIT")
                     sql_final = f"SELECT * FROM {nombre_tabla} WHERE {col_inc} > {ultimo_valor} LIMIT {partes[1]}"
                else:
                    # Si no tiene nada, agregamos WHERE
                    sql_final += f" WHERE {col_inc} > {ultimo_valor}"
            # ------------------------------------------------------
            
            # ### PUNTO 6: Lectura segura con reintentos ###
            ejecutar_sql_con_reintentos(cursor_source, sql_final)
            
            columnas = [desc[0] for desc in cursor_source.description]
            filas = cursor_source.fetchall()

            # ### PUNTO 5: Registrar conteo de lectura ###
            stats_tabla["registros_leidos"] = len(filas)
            total_registros_global += len(filas)
            # ------------------------------------------

        except Exception as e:
            print_log(f"⚠️ Error leyendo tabla {nombre_tabla}: {e}")
            stats_tabla["error"] = str(e) # ### PUNTO 5: Guardar error si ocurre ###
            log_detalles.append(stats_tabla)
            continue

        print_log(f"   -> Se encontraron {len(filas)} registros.")

        # Transformar datos (Transform)
        filas_enmascaradas = []
        max_id_lote = estado.get(nombre_tabla, 0) # ### NUEVO: Variable para rastrear el ID más alto de este lote ###

        for fila in filas:
            fila_dict = dict(zip(columnas, fila)) # Convertir tupla a diccionario para manipular fácil
            
            # ### NUEVO: Actualizar el "watermark" (marca de agua) ###
            if col_inc in fila_dict and isinstance(fila_dict[col_inc], int):
                if fila_dict[col_inc] > max_id_lote:
                    max_id_lote = fila_dict[col_inc]
            # -----------------------------------------------------

            fila_nueva = fila_dict.copy()
            
            # Aplicar reglas de enmascaramiento
            for columna, regla in reglas.items():
                if regla in MAPPING_FUNCIONES and columna in fila_nueva:
                    valor_original = fila_nueva[columna]
                    fila_nueva[columna] = MAPPING_FUNCIONES[regla](valor_original)
            
            filas_enmascaradas.append(fila_nueva)

        # Cargar datos (Load) - SIMULACIÓN E INSERCIÓN
        conteo_inserts = 0 # ### PUNTO 5: Contador temporal ###

        # ### PUNTO 9: INSERCIÓN POR LOTES (BATCH) ###
        # Sustituimos el bucle 'for' uno a uno por una inserción masiva
        try:
            if nombre_tabla == "clientes":
                print_log(f"   -> Preparando lote de {len(filas_enmascaradas)} registros para clientes_qa... (Batch)")
                
                # 1. Lista de tuplas para batch
                datos_batch = [
                    (f['id'], f['nombre_completo'], f['email'], f['telefono'], f['tarjeta_credito'], execution_id)
                    for f in filas_enmascaradas
                ]
                
                # 2. SQL genérico
                sql = """
                    INSERT INTO clientes_qa (id, nombre_completo, email, telefono, tarjeta_credito, etl_batch_id)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET 
                        nombre_completo = EXCLUDED.nombre_completo,
                        email = EXCLUDED.email,
                        telefono = EXCLUDED.telefono,
                        tarjeta_credito = EXCLUDED.tarjeta_credito,
                        etl_batch_id = EXCLUDED.etl_batch_id;
                """
                
                if datos_batch:
                    # Usamos execute_values para máxima velocidad en Postgres
                    ejecutar_batch_con_reintentos(cursor_target, sql, datos_batch)
                    conteo_inserts = len(datos_batch)
                
                conn_target.commit()

            elif nombre_tabla == "ordenes":
                print_log(f"   -> Preparando lote de {len(filas_enmascaradas)} registros para ordenes_qa... (Batch)")
                
                datos_batch = [
                    (f['id'], f['cliente_id'], f['fecha_orden'], f['total'], execution_id)
                    for f in filas_enmascaradas
                ]

                sql = """
                    INSERT INTO ordenes_qa (id, cliente_id, fecha_orden, total, etl_batch_id)
                    VALUES %s
                    ON CONFLICT (id) DO NOTHING;
                """
                
                if datos_batch:
                    ejecutar_batch_con_reintentos(cursor_target, sql, datos_batch)
                    conteo_inserts = len(datos_batch)

                conn_target.commit()

            elif nombre_tabla == "detalle_ordenes":
                 print_log(f"   -> Preparando lote de {len(filas_enmascaradas)} registros para detalle_ordenes_qa... (Batch)")
                 
                 datos_batch = [
                    (f['id'], f['orden_id'], f['producto'], f['cantidad'], execution_id)
                    for f in filas_enmascaradas
                 ]

                 sql = """
                    INSERT INTO detalle_ordenes_qa (id, orden_id, producto, cantidad, etl_batch_id)
                    VALUES %s
                    ON CONFLICT (id) DO NOTHING;
                 """
                 
                 if datos_batch:
                    ejecutar_batch_con_reintentos(cursor_target, sql, datos_batch)
                    conteo_inserts = len(datos_batch)

                 conn_target.commit()

        except Exception as e:
            print_log(f"   ❌ Error insertando lote (Batch): {e}")
            stats_tabla["errores"].append(str(e))
        # ---------------------------------------------

        # ### PUNTO 5: Guardar conteo final de esta tabla en el log ###
        stats_tabla["registros_insertados"] = conteo_inserts
        log_detalles.append(stats_tabla)
        # ------------------------------------------------------------

        # ### NUEVO: Guardar el estado si hubo éxito ###
        if filas:
            estado[nombre_tabla] = max_id_lote
            guardar_estado(estado)
            print_log(f"   💾 Estado actualizado: {nombre_tabla} -> {max_id_lote}")

    # ### PUNTO 5: CIERRE DE AUDITORÍA Y GUARDADO EN BD ###
    fecha_fin = datetime.datetime.now()
    
    # 1. Preparamos el objeto JSON final
    log_final = {
        "execution_id": execution_id,
        "usuario": usuario_rol, # ### PUNTO 8: Registramos quién corrió el proceso ###
        "inicio": str(fecha_inicio),
        "fin": str(fecha_fin),
        "total_registros_movidos": total_registros_global,
        "detalles_por_tabla": log_detalles
    }

    # 2. Guardar en Archivo Local JSON (Requisito)
    historial = []
    if os.path.exists(ARCHIVO_LOGS):
        try:
            with open(ARCHIVO_LOGS, "r") as f: historial = json.load(f)
        except: pass # Si falla al leer, empezamos uno nuevo
    
    historial.append(log_final)
    with open(ARCHIVO_LOGS, "w") as f:
        json.dump(historial, f, indent=4)
    print_log(f"\n📄 Log guardado localmente en: {ARCHIVO_LOGS}")

    # 3. Guardar en Base de Datos Supabase (Requisito Histórica en QA)
    try:
        nombres_tablas_str = ", ".join([d['tabla'] for d in log_detalles])
        sql_audit = """
            INSERT INTO auditoria_logs (execution_id, fecha_inicio, fecha_fin, tablas_procesadas, total_registros, detalle_json)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        # ### PUNTO 6: Guardado seguro con reintentos ###
        ejecutar_sql_con_reintentos(cursor_target, sql_audit, (
            execution_id, 
            fecha_inicio, 
            fecha_fin, 
            nombres_tablas_str, 
            total_registros_global, 
            json.dumps(log_detalles) 
        ))
        conn_target.commit()
        print_log("✅ Log guardado en Supabase (tabla auditoria_logs)")
    except Exception as e:
        print_log(f"⚠️ Error guardando en auditoria_logs: {e}")
    # -------------------------------------------------------------------

    # Cerrar conexiones
    try:
        cursor_source.close()
        conn_source.close()
        cursor_target.close()
        conn_target.close()
    except: pass
    print_log("\n🏁 Proceso finalizado exitosamente.")
    
    # DEVOLVEMOS EL TEXTO DEL LOG A LA WEB
    return "\n".join(LOG_BUFFER)

if __name__ == "__main__":
    ejecutar_migracion()