#!/bin/sh

# Crear directorios si no existen
mkdir -p /var/loki/index /var/loki/cache /var/loki/chunks

# Cambiar el propietario de los directorios a 'grafana' (UID 472, GID 472)
# ¡Importante! Este chown sigue siendo necesario para que Loki pueda escribir,
# ya que Loki internamente podría cambiar a ese usuario, o el volumen podría
# tener permisos por defecto que no permitan a root escribir directamente si no es el propietario.
# Pero el proceso final de Loki se ejecutará como root.
chown -R 472:472 /var/loki

# Ejecutar el comando original de Loki directamente como el usuario actual (root)
exec /usr/bin/loki -config.file=/etc/loki/loki-config.yml "$@"
