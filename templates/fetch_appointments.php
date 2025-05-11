<?php
header("Content-Type: application/json");

// Database connection
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "world";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die(json_encode(["error" => "Connection failed: " . $conn->connect_error]));
}

// Fetch data from the database
$sql = "SELECT Appointment_Id, StudentNumber, AppointmentDate, CollectionDate, CollectionTime, AppointmentStatus FROM appointments";
$result = $conn->query($sql);

// Fetch all results as an associative array
$appointments = [];
if ($result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $appointments[] = $row;
    }
}

// Close connection
$conn->close();

// Return JSON response
echo json_encode($appointments);
?>
