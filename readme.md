# 🛡️ Sistema ETL de Migración y Enmascaramiento de Datos

**FES Acatlán - Matemáticas Aplicadas y Computación**
**Materia:** Administración de Bases de Datos

Este proyecto implementa un pipeline **ETL (Extract, Transform, Load)** robusto desarrollado en Python. Su objetivo principal es migrar datos sensibles desde un entorno de Producción a un entorno de QA (Calidad), aplicando reglas de enmascaramiento en tiempo real para proteger la Información Personal Identificable (PII).

El sistema cuenta con una interfaz gráfica interactiva construida con **Streamlit**, gestión de estado local, logs de auditoría en base de datos y soporte para Docker.

---

## 📋 Características Principales

* **Idempotencia y Persistencia:** Capacidad de reanudar cargas interrumpidas gracias al archivo de estado (`state.json`).
* **Modos de Ejecución:**
    * 🔴 **Carga Completa (Full Load):** Limpieza total del destino y recarga desde cero.
    * 🔄 **Carga Incremental (Delta):** Detección y migración solo de registros nuevos.
    * 🧪 **Modo Ensayo (Dry Run):** Verificación de conexiones sin alterar datos.
* **Enmascaramiento de Datos:** Transformación irreversible de datos sensibles (Email, Tarjetas, Nombres).
* **Auditoría Dual:** Logs técnicos en archivo local JSON y logs de cumplimiento en tabla SQL.
* **Monitor en Tiempo Real:** Visualización inmediata de los datos migrados en la interfaz.

---

## 🛠️ a. Pasos de Instalación (Setup)

### 1. Requisitos Previos
* **Python 3.9** o superior.
* **PostgreSQL** (Local o Supabase).
* **Docker Desktop** (Opcional, si se desea contenedorizar se recomienda esta opción como prioridad).

### 2. Instalación de Dependencias
Clona el repositorio y ejecuta:
```bash
pip install -r requirements.txt