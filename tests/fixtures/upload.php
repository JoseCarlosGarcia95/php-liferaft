<?php
header('Content-Type: application/json');
session_start();
$key = 'upload_progress_' . (isset($_POST['PHP_SESSION_UPLOAD_PROGRESS']) ? $_POST['PHP_SESSION_UPLOAD_PROGRESS'] : 'test');
if (isset($_GET['seed'])) {
    $_SESSION[$key] = array('cancel_upload' => true);
    session_write_close();
    echo json_encode(array('seeded' => true));
    return;
}
$files = array();
foreach ($_FILES as $name => $file) {
    $files[$name] = array('size' => $file['size'], 'error' => $file['error']);
}
$result = array(
    'version' => PHP_VERSION,
    'content_length' => isset($_SERVER['CONTENT_LENGTH']) ? (int) $_SERVER['CONTENT_LENGTH'] : 0,
    'files' => $files,
    'progress' => isset($_SESSION[$key]) ? $_SESSION[$key] : null,
    'extensions' => get_loaded_extensions()
);
session_destroy();
echo json_encode($result);
