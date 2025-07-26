from flask import Flask, request
import psycopg2

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hola desde Python Flask"

@app.route("/insertar", methods=["POST"])
def insertar():
    nombre = request.form.get("nombre")
    telefono = request.form.get("telefono")
    conn = psycopg2.connect(
        host="postgres",
        dbname="labdb",
        user="labuser",
        password="labpass"
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO contactos (nombre, telefono) VALUES (%s, %s);", (nombre, telefono))
    conn.commit()
    cur.close()
    conn.close()
    return "Datos insertados correctamente"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

