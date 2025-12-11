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



```md
## 🛡️ b. Manejo de Seguridad

La arquitectura de seguridad del proyecto se basa en tres pilares para cumplir con los requerimientos académicos y las mejores prácticas de ingeniería de datos:

### 1. Almacenamiento de Credenciales (Segregación)
* **Separación de Código y Configuración:** Las credenciales de base de datos **NO** están expuestas dentro del código fuente (`main.py` o `app.py`).
* **Archivo de Configuración Excluido:** Se utiliza un archivo `config.yaml` externo para la conexión. Este archivo está incluido en el `.gitignore`, asegurando que **nunca se suba al repositorio público**.
* **Plantilla Segura:** En el repositorio se incluye un archivo `config.example.yaml` con credenciales ficticias para guiar la instalación sin comprometer la seguridad.

### 2. Control de Acceso Basado en Roles (RBAC)
El sistema implementa una capa de autenticación simulada en el Frontend (`app.py`) para restringir operaciones críticas según el perfil del usuario:

| Rol | Permisos | Contraseña (Demo) |
| :--- | :--- | :--- |
| **Invitado** | Solo lectura (Ver gráficas y logs de auditoría). | *N/A* |
| **Operador** | Ejecución de Carga Incremental (Delta) y Modo Ensayo. | `ABD123` |
| **Dev (Admin)** | Control Total, incluyendo Carga Completa (Truncate) y reinicio de estado. | `ABD123` |

### 3. Trazabilidad y Auditoría
Cada operación genera un `execution_id` único (UUID) que garantiza el no repudio de las acciones. Este ID queda registrado en una **doble bitácora**:
* **Local:** Archivo `logs_historial.json` para consulta inmediata.
* **Remota:** Tabla inmutable `auditoria_logs` en PostgreSQL para análisis forense.