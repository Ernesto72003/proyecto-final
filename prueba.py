import psycopg2

LINK_COMPLETO = "postgresql://postgres:kfvDiz4TD9mHLSRg@db.amvqlrljrlvojbgpxfjk.supabase.co:5432/postgres"


print("Intentando conectar con el link completo...")

try:
    # Nos conectamos pasando el link directo
    conn = psycopg2.connect(LINK_COMPLETO)
    print("\n✅ ¡CONEXIÓN EXITOSA!")
    print("Ya puedes poner este mismo link en tu archivo config.yaml")
    conn.close()
except Exception as e:
    print("\n❌ FALLÓ LA CONEXIÓN.")
    print("El error detallado es:")
    print(e)