<?php
// move.php
session_start();
header('Content-Type: application/json; charset=utf-8');

// helper to respond
function json_err($msg, $code = 400) {
    http_response_code($code);
    echo json_encode(['error' => $msg]);
    exit;
}

// validate session
if (!isset($_SESSION['maze']) || !isset($_SESSION['player']) || !isset($_SESSION['goal'])) {
    json_err('セッション情報がありません。ゲームを再開してください。', 440);
}

// parse input
$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data) || !isset($data['dir'])) {
    json_err('無効なリクエスト。', 400);
}

$dir = $data['dir'];
$allowed = ['up','down','left','right'];
if (!in_array($dir, $allowed, true)) {
    json_err('無効な方向指定。', 400);
}

// current state
$maze = $_SESSION['maze'];
$player = $_SESSION['player'];
$rows = count($maze);
$cols = strlen($maze[0]);

$dr = 0; $dc = 0;
switch ($dir) {
    case 'up': $dr = -1; break;
    case 'down': $dr = 1; break;
    case 'left': $dc = -1; break;
    case 'right': $dc = 1; break;
}

// target
$nr = $player['r'] + $dr;
$nc = $player['c'] + $dc;

// bounds check
if ($nr < 0 || $nr >= $rows || $nc < 0 || $nc >= $cols) {
    // invalid move: ignore
    echo json_encode([
        'player' => $player,
        'steps' => $_SESSION['steps'],
        'cleared' => false,
        'message' => '境界外の移動',
    ]);
    exit;
}

// check wall
$ch = $maze[$nr][$nc] ?? '#';
if ($ch === '#') {
    // wall: ignore move
    echo json_encode([
        'player' => $player,
        'steps' => $_SESSION['steps'],
        'cleared' => false,
        'message' => '壁です',
    ]);
    exit;
}

// move allowed
$_SESSION['player'] = ['r' => $nr, 'c' => $nc];
$_SESSION['steps'] = ($_SESSION['steps'] ?? 0) + 1;

// goal check (maze cell might contain 'G')
$cleared = false;
$goal = $_SESSION['goal'];
if ($nr === $goal['r'] && $nc === $goal['c']) {
    $cleared = true;
}

$now = time();
$elapsed = $now - ($_SESSION['start_time'] ?? $now);

echo json_encode([
    'player' => $_SESSION['player'],
    'steps' => $_SESSION['steps'],
    'cleared' => $cleared,
    'elapsed' => $elapsed,
]);
exit;
