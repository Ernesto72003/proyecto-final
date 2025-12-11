# Usamos una imagen ligera de Python
FROM python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema requeridas para postgres
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copiar archivos del proyecto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Puerto para la Web UI
EXPOSE 8501

# Comando de inicio
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]