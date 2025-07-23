<?php

// Configuración de la base de datos
$host = 'postgres'; // Nombre del servicio de PostgreSQL en docker-compose
$dbname = 'labdb';
$user = 'labuser';
$password = 'labpass';

$conn = null; // Inicializar $conn a null

try {
    // Conexión a la base de datos
    $conn = new PDO("pgsql:host=$host;dbname=$dbname", $user, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $nombre = isset($_GET['nombre']) ? $_GET['nombre'] : 'AnonimoApache';
    $telefono = isset($_GET['telefono']) ? $_GET['telefono'] : 'N/A';

    // Preparar y ejecutar la consulta SQL
    $stmt = $conn->prepare("INSERT INTO contactos (nombre, telefono) VALUES (:nombre, :telefono)");
    $stmt->bindParam(':nombre', $nombre);
    $stmt->bindParam(':telefono', $telefono);
    $stmt->execute();

    echo "Datos insertados correctamente desde Apache/PHP: Nombre='" . htmlspecialchars($nombre) . "', Telefono='" . htmlspecialchars($telefono) . "'";

} catch (PDOException $e) {
    echo "Error al insertar datos: " . $e->getMessage();
} finally {
    // Cerrar la conexión
    if ($conn) {
        $conn = null;
    }
}

?>
