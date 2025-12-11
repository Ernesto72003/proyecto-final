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
Esta es la fomra recomendada para mover el ETL a QA o Producción, ya que esto nos garantiza que tengamos un entorno inmutable.
Asegura que el entorno de ejecución sea identico en cualquier servidor.

### Instlación de docker
Antes de cualquier cosa instalaremos docker desde internet en la siguiente liga https://www.google.com/search?client=opera&q=docker&sourceid=opera&ie=UTF-8&oe=UTF-8&sei=p1A7aZLoEaGnqtsP54vf2As
para usar el docker que necesitaremos mas adaelante.

Empecemos con lo primeero que tenemos que crear una carpeta donde tenemos que clonar algunos archivos especificos de nuestro repositorio de github, los cuales son:
### 1. app.py
### 2. config.yaml
### 3. dockerfile
### 4. generar_datos.py
### 5. main.py
### 6. prueba.py.
### 7. requirements.txt 

Esto se puede clonar con un comando estandar en la cmd para pasar los archivos del repositorio a la carpeta creada anteriormente:

git clone [URL_DEL_REPOSITORIO] [NOMBRE_DE_LA CARPETA]

Buscamos en nuestro explorador de archivos la carpeta en la cual clonamos los archivos de nuestro repositorio de github y la seleccionamos, dentro de ella en la aparte de arriba debe decir algo
como esto "D:\proyecto_abd" (donde se encuentra nuestra carpeta en el ordenador) borramos eso y ponemos cmd + enter; enseguida nos desplegara la terminal y dira algo como esto
"D:\proyecto_abd>".

Después construimos la imagen del docker con el siguiente comando:

### D:\proyecto_abd>docker build -t proyecto_abd

Ahora ejecutamos la imagen que acabamos de crear.

### D:\proyecto_abd>docker run -d -p 8501:8501 --name etl-final proyecto_abd

Ahora verificamos el estado del contenedor

### D:\proyecto_abd>docker ps

Accedemos a la interfaz gráfica (Streamlit).
Abre tu navegador web y ve a la sigueinte dirección: https://localhost:8501.
A partir de aquí, el profesor puede verificar todos los requisitos desde la interfaz:

1. Login (Requisito 8: RBAC): Iniciar sesión como dev con la contraseña ABD123.

2. Generación de Datos (Requisito 4): Usar el botón de generar datos para poblar la tabla fuente.

3. Full Load: Ejecutar la carga completa (verifica Rendimiento/Batch Insert).

4. Delta Load: Ejecutar la carga incremental (verifica Requisito 3).

5. Inspector: Verificar que los datos en DESTINO están enmascarados (Requisito 2).

6. Auditoría: Verificar que los logs se guardan correctamente (Requisito 5 y 6).








# 🛡️ b. Manejo de Seguridad

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
