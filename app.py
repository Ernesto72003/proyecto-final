import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import os
import yaml
import psycopg2

# IMPORTACIÓN DIRECTA (SOLUCIÓN DEFINITIVA)
import main as script_etl
import generar_datos as script_generador

# CONFIGURACIÓN
st.set_page_config(page_title="Proyecto Final ETL - FES Acatlán", page_icon="🐾", layout="wide")

# ESTILOS
st.markdown("""
    <style>
    h1, h2, h3 { color: #002B7A !important; }
    div[data-testid="stMetric"], div[data-testid="metric-container"] {
        background-color: #002B7A !important;
        border: 2px solid #D59F0F !important;
        color: white !important;
    }
    [data-testid="stMetricValue"] { color: #D59F0F !important; font-weight: bold !important; }
    .stButton>button { color: #002B7A; border-color: #002B7A; font-weight: bold; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# FUNCIONES
def cargar_logs():
    if os.path.exists("logs_historial.json"):
        try:
            with open("logs_historial.json", "r") as f: return json.load(f)
        except: return []
    return []

def consultar_db(query, target="source"):
    try:
        with open("config.yaml", "r") as f: config = yaml.safe_load(f)
        url = config['database']['source_url'] if target == "source" else config['database']['target_url']
        conn = psycopg2.connect(url)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except: return None

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Escudo-UNAM-escalable.svg/1200px-Escudo-UNAM-escalable.svg.png", width=120)
    st.title("FES ACATLÁN")
    st.markdown("**Matemáticas Aplicadas y Computación**")
    st.markdown("---")
    
    rol = st.selectbox("Perfil:", ["Invitado", "operador", "dev"])
    password_input = ""
    if rol != "Invitado":
        password_input = st.text_input("🔑 Contraseña:", type="password")
        if password_input == "ABD123": st.success("Acceso Concedido")
        elif password_input: st.error("Incorrecta")
    else:
        st.info("Modo Invitado (Lectura)")

# CABECERA
st.title("Proyecto Final ETL")
logs = cargar_logs()
total_movidos = sum([l.get('total_registros_movidos', 0) for l in logs])
k1, k2, k3 = st.columns(3)
k1.metric("Ejecuciones", len(logs))
k2.metric("Registros Migrados", f"{total_movidos:,}")
k3.metric("Ambiente", "PRODUCCIÓN" if password_input == "ABD123" else "LECTURA")

st.divider()

# TABS
tabs = st.tabs(["🚀 Ejecución", "🕵️ Inspector", "📊 Auditoría"])

# TAB 1: EJECUCIÓN + MONITOR EN VIVO
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    
    # FULL LOAD
    with c1:
        st.markdown("### 1. Carga Completa")
        bloqueado = not (rol == "dev" and password_input == "ABD123")
        if st.button("🔴 EJECUTAR FULL LOAD", disabled=bloqueado, use_container_width=True):
            with st.status("Procesando...", expanded=True):
                st.write("🌍 Generando Datos...")
                log_gen = script_generador.generar_datos_inteligentes()
                st.text(log_gen)
                st.write("🔄 Migrando ETL...")
                log_etl = script_etl.ejecutar_migracion(rol, 1)
                st.code(log_etl)
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()

    # DELTA LOAD
    with c2:
        st.markdown("### 2. Carga Incremental")
        bloqueado = not (rol in ["dev", "operador"] and password_input == "ABD123")
        if st.button("🔄 EJECUTAR DELTA", disabled=bloqueado, use_container_width=True):
            with st.status("Procesando...", expanded=True):
                st.write("🌍 Generando Datos...")
                log_gen = script_generador.generar_datos_inteligentes()
                st.text(log_gen)
                st.write("🔍 Sincronizando...")
                log_etl = script_etl.ejecutar_migracion(rol, 2)
                st.code(log_etl)
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()

    # ENSAYO
    with c3:
        st.markdown("### 3. Modo Ensayo")
        if st.button("🧪 EJECUTAR PRUEBA", use_container_width=True):
            log = script_etl.ejecutar_migracion("dev", 3)
            st.code(log)
            st.balloons()

    # MONITOR EN VIVO DE ÚLTIMOS REGISTROS
    st.divider()
    st.subheader("📥 Monitor en Tiempo Real (QA)")
    st.caption("Últimos 8 registros ingresados en el sistema destino.")
    df_recientes = consultar_db("SELECT id, nombre_completo, email, etl_batch_id FROM clientes_qa ORDER BY id DESC LIMIT 8", "target")
    if df_recientes is not None and not df_recientes.empty:
        st.dataframe(df_recientes, use_container_width=True, hide_index=True)
    else:
        st.info("Sin datos recientes.")

# TAB 2: INSPECTOR
with tabs[1]:
    sid = st.number_input("Buscar ID:", 100)
    c1, c2 = st.columns(2)
    with c1:
        st.caption("FUENTE")
        st.dataframe(consultar_db(f"SELECT * FROM clientes WHERE id={sid}", "source"), hide_index=True)
    with c2:
        st.caption("DESTINO")
        st.dataframe(consultar_db(f"SELECT * FROM clientes_qa WHERE id={sid}", "target"), hide_index=True)

# TAB 3: AUDITORÍA
with tabs[2]:
    st.subheader("Historial")
    if logs:
        df = pd.DataFrame(logs)
        df['inicio'] = pd.to_datetime(df['inicio'])
        st.plotly_chart(px.bar(df, x='inicio', y='total_registros_movidos', color_discrete_sequence=['#D59F0F']))
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)