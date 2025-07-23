FROM php:8.2-apache

# Actualizar la lista de paquetes e instalar las librerías de desarrollo de PostgreSQL
# Las extensiones pgsql y pdo_pgsql necesitan estas cabeceras para compilarse.
RUN apt-get update && \
    apt-get install -y libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Instalar la extensión pgsql para PostgreSQL
RUN docker-php-ext-install pgsql pdo_pgsql

# Copiar los archivos de la aplicación web
COPY insertar_apache.php /var/www/html/insertar_apache.php
COPY index.html /var/www/html/index.html
