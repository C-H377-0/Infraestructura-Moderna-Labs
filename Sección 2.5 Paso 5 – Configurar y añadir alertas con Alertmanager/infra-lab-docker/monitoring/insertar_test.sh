#!/bin/bash

# URL del endpoint
URL="http://localhost:5000/insertar"

for i in $(seq 1 100); do
  random_choice=$(( $RANDOM % 2 ))
  #if (( i % 2 == 0 )); then
  if (( random_choice == 0 )); then
    nombre="error"
  else
    nombre="ABCD"
  fi

  telefono="999"

  echo "[$i] Enviando: nombre=$nombre, telefono=$telefono"
  curl -s -X POST "$URL" -d "nombre=$nombre&telefono=$telefono"
  echo ""
  sleep 0.1
done

