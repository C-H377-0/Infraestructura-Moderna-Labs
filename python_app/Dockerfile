# Imagen base liviana de Python
FROM python:3.10-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala curl (útil para pruebas) y dependencias básicas
RUN apt-get update && \
    apt-get install -y curl build-essential gcc libpq-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copia el archivo de dependencias y lo instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código fuente
COPY . .

# Expone el puerto Flask
EXPOSE 5000

# Comando por defecto al arrancar el contenedor
CMD ["python", "app.py"]
