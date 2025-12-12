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


### 1. Requisitos Previos y Preparación
Antes de ejecutar el programa (sea con Docker o Python), asegúrese de tener configurada la base de datos y los archivos:

1.  **Base de Datos:** Asegúrese de que las tablas destino existan en su PostgreSQL (Local o Supabase). Ejecute este SQL si aún no lo ha hecho:
    ```sql
    CREATE TABLE clientes_qa (id INT PRIMARY KEY, nombre_completo VARCHAR(150), email VARCHAR(150), telefono VARCHAR(100), tarjeta_credito VARCHAR(100), etl_batch_id VARCHAR(100));
    CREATE TABLE ordenes_qa (id INT PRIMARY KEY, cliente_id INT, fecha_orden DATE, total DECIMAL(10,2), etl_batch_id VARCHAR(100));
    CREATE TABLE detalle_ordenes_qa (id INT PRIMARY KEY, orden_id INT, producto VARCHAR(100), cantidad INT, etl_batch_id VARCHAR(100));
    CREATE TABLE auditoria_logs (execution_id VARCHAR(100) PRIMARY KEY, fecha_inicio TIMESTAMP, fecha_fin TIMESTAMP, tablas_procesadas TEXT, total_registros INT, detalle_json TEXT);
    ```

2.  **Archivos del Repositorio:** Clone el repositorio en una carpeta de su ordenador:
    ```bash
    git clone [URL_DEL_REPOSITORIO] proyecto_abd
    ```
    *Archivos clave:* `app.py`, `config.yaml`, `Dockerfile`, `generar_datos.py`, `main.py`, `requirements.txt`.

3.  **Configuración:** Renombre `config.example.yaml` a `config.yaml` y coloque sus credenciales reales de base de datos.

Para que el sistema funcione, debe crear su propio archivo de configuración basándose en la plantilla:
Localice el archivo config.example.yaml en la carpeta.

Copie y pegue el archivo en la misma ubicación (Ctrl+C, Ctrl+V).

Renombre la copia a config.yaml.

Abra config.yaml y reemplace los valores de ejemplo con sus credenciales reales de PostgreSQL, que estan en la documentación del proyecto.

```YAML

Database:
   source_url: "postgresql://postgres.amvqlrljrlvojbgpxfjk:CONTRASEÑAAQUI@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
   target_url: "postgresql://postgres.amvqlrljrlvojbgpxfjk:CONTRASEÑAAQUI@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
tablas:
---
```
### 2. Opciones de Ejecución

Puede elegir cualquiera de las dos opciones siguientes para iniciar el sistema:

#### 🐳 Opción A: Ejecución con Docker (Recomendada)
Esta es la forma recomendada para mover el ETL a QA o Producción, ya que esto nos garantiza que tengamos un entorno inmutable y asegura que el entorno de ejecución sea idéntico en cualquier servidor.

**Pasos:**

1.  **Instalación de Docker:** Si no lo tiene, instale Docker Desktop desde [aquí](https://www.docker.com/products/docker-desktop).
2.  **Abrir Terminal:** Busque la carpeta clonada (ej. `D:\proyecto_abd`), borre la ruta en la barra superior, escriba `cmd` y pulse Enter.
3.  **Construir Imagen:** Ejecute el siguiente comando:
    ```bash
    docker build -t proyecto_abd .
    ```
    *(Nota: No olvide el punto al final).*
4.  **Ejecutar Contenedor:**
    ```bash
    docker run -d -p 8501:8501 --name etl-final proyecto_abd
    ```
5.  **Verificar estado (Opcional):**
    ```bash
    docker ps
    ```
6.  **Acceso:** Abra su navegador en [http://localhost:8501](http://localhost:8501).

> **Nota importante:** En caso de surgir el error `failed to read dockerfile`, asegúrese de estar ubicado exactamente dentro de la carpeta del proyecto donde se encuentra el archivo `Dockerfile`.

---

#### 🐍 Opción B: Ejecución Local con Python (Alternativa)
Si no desea usar Docker, puede ejecutar el sistema directamente en su ordenador siguiendo estos pasos sencillos:

1.  **Instalar Python:** Asegúrese de tener Python 3.9 o superior instalado.
2.  **Abrir Terminal:** Abra una terminal (CMD o PowerShell) dentro de la carpeta del proyecto (`D:\proyecto_abd`).
3.  **Instalar Dependencias:** Ejecute el siguiente comando para instalar las librerías necesarias:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Ejecutar Aplicación:** Inicie el dashboard con el comando:
    ```bash
    streamlit run app.py
    ```
5.  **Acceso:** El sistema abrirá automáticamente una pestaña en su navegador (generalmente `http://localhost:8501`).

---

### 3. Validación Funcional
A partir de aquí, se pueden verificar todos los requisitos desde la interfaz gráfica:

1.  **Login (Requisito 8: RBAC):** Iniciar sesión como `dev` con la contraseña `ABD123`.
2.  **Generación de Datos (Requisito 4):** Usar el botón de generar datos para poblar la tabla fuente.
3.  **Full Load:** Ejecutar la carga completa (verifica Rendimiento/Batch Insert).
4.  **Delta Load:** Ejecutar la carga incremental (verifica Requisito 3).
5.  **Inspector:** Verificar en la pestaña 2 que los datos en DESTINO están enmascarados (Requisito 2).
6.  **Auditoría:** Verificar en la pestaña 3 que los logs se guardan correctamente (Requisito 5 y 6).

---

## 🛡️ b. Manejo de Seguridad

La arquitectura de seguridad del proyecto se basa en tres pilares para cumplir con los requerimientos académicos y las mejores prácticas de la admistración de bases de datos.

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
* **Remota:** Tabla inmutable `auditoria_logs` en PostgreSQL para análisis.
