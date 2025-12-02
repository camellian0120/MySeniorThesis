<?php
declare(strict_types=1);
session_start();

// ----------------------------------------------------------------------
// 定数
// ----------------------------------------------------------------------
const SIZE  = 15; // 15x15 の盤面
const NOONE = 0;
const BLACK = 1; // 黒（先手）
const WHITE = 2; // 白（後手）

// ----------------------------------------------------------------------
// HTML エスケープ
// ----------------------------------------------------------------------
function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

// ----------------------------------------------------------------------
// ゲーム初期化
// ----------------------------------------------------------------------
function init_game(bool $force = false): void {
    $needInit = $force;

    if (!isset($_SESSION["board"]) || !is_array($_SESSION["board"])) {
        $needInit = true;
    }
    if (!isset($_SESSION["turn"])) {
        $needInit = true;
    }

    if ($needInit) {
        $_SESSION["board"] = array_fill(0, SIZE, array_fill(0, SIZE, NOONE));
        $_SESSION["turn"] = BLACK;
        $_SESSION["winner"] = null;
        $_SESSION["move_count"] = 0;

        // CSRF 対策トークン
        $_SESSION["csrf_token"] = bin2hex(random_bytes(32));

        // セッション固定化対策
        session_regenerate_id(true);
    }
}

// ----------------------------------------------------------------------
// 勝利判定（5 連続で勝ち）
// ----------------------------------------------------------------------
function check_win(array $board, int $color): bool {
    // 方向: 右 / 下 / 右下 / 左下
    $dirs = [
        [1, 0],  // →
        [0, 1],  // ↓
        [1, 1],  // ↘
        [-1, 1], // ↙
    ];

    for ($y = 0; $y < SIZE; $y++) {
        for ($x = 0; $x < SIZE; $x++) {
            if ($board[$y][$x] !== $color) continue;

            foreach ($dirs as [$dx, $dy]) {
                $count = 1;
                for ($k = 1; $k < 5; $k++) {
                    $nx = $x + $dx * $k;
                    $ny = $y + $dy * $k;
                    if ($nx < 0 || $ny < 0 || $nx >= SIZE || $ny >= SIZE) break;
                    if ($board[$ny][$nx] !== $color) break;
                    $count++;
                }
                if ($count >= 5) return true;
            }
        }
    }
    return false;
}

// ----------------------------------------------------------------------
// セルクリック（石を置く）
// ----------------------------------------------------------------------
function place_stone(int $x, int $y): void {
    if (!isset($_SESSION["board"], $_SESSION["turn"])) return;

    $board = &$_SESSION["board"];
    $turn  = &$_SESSION["turn"];

    // 既にゲーム終了
    if (!empty($_SESSION["winner"])) return;

    // 既に置かれている
    if ($board[$y][$x] !== NOONE) return;

    // 置く
    $board[$y][$x] = $turn;
    $_SESSION["move_count"]++;

    // 勝利判定
    if (check_win($board, $turn)) {
        $_SESSION["winner"] = $turn;
        return;
    }

    // ターン切替
    $turn = ($turn === BLACK) ? WHITE : BLACK;
}

// ----------------------------------------------------------------------
// POST 処理（安全：CSRF チェック）
// ----------------------------------------------------------------------
init_game();

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    if (
        isset($_POST["token"])
        && hash_equals($_SESSION["csrf_token"] ?? "", $_POST["token"])
    ) {
        if (isset($_POST["x"], $_POST["y"])) {
            $x = filter_var($_POST["x"], FILTER_VALIDATE_INT, ["options" => ["min_range" => 0, "max_range" => SIZE-1]]);
            $y = filter_var($_POST["y"], FILTER_VALIDATE_INT, ["options" => ["min_range" => 0, "max_range" => SIZE-1]]);
            if ($x !== false && $y !== false) {
                place_stone($x, $y);
            }
        }
        if (isset($_POST["restart"])) {
            init_game(true);
        }
    }
}

// ----------------------------------------------------------------------
// HTML 出力開始
// ----------------------------------------------------------------------
$board  = $_SESSION["board"];
$turn   = $_SESSION["turn"];
$winner = $_SESSION["winner"];
$token  = $_SESSION["csrf_token"];
?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>五目並べ</title>
<style>
table { border-collapse: collapse; margin: 20px auto; }
td {
    width: 32px; height: 32px;
    border: 1px solid #888;
    text-align: center; vertical-align: middle;
    font-size: 24px; cursor: pointer;
}
.info { text-align: center; margin-top: 10px; font-size: 20px; }
.restart { margin-top: 20px; text-align: center; }
</style>
</head>
<body>

<div class="info">
<?php if ($winner === BLACK): ?>
    黒の勝ち！
<?php elseif ($winner === WHITE): ?>
    白の勝ち！
<?php else: ?>
    現在のターン：<?= h($turn === BLACK ? "黒" : "白") ?>
<?php endif; ?>
</div>

<!-- 盤面 -->
<form method="post">
<table>
<?php for ($y = 0; $y < SIZE; $y++): ?>
<tr>
<?php for ($x = 0; $x < SIZE; $x++): ?>
    <td>
        <?php if ($winner === null && $board[$y][$x] === NOONE): ?>
            <button type="submit" name="pos" value="1" 
                style="width:100%;height:100%;border:none;background:none;cursor:pointer"
                onclick="this.form.x.value='<?= $x ?>'; this.form.y.value='<?= $y ?>';">
            </button>
        <?php elseif ($board[$y][$x] === BLACK): ?>
            ●
        <?php elseif ($board[$y][$x] === WHITE): ?>
            ○
        <?php endif; ?>
    </td>
<?php endfor; ?>
</tr>
<?php endfor; ?>
</table>

<input type="hidden" name="token" value="<?= h($token) ?>">
<input type="hidden" name="x" value="">
<input type="hidden" name="y" value="">
</form>

<!-- 再スタート -->
<div class="restart">
<form method="post">
    <input type="hidden" name="token" value="<?= h($token) ?>">
    <button type="submit" name="restart" value="1">もう一度遊ぶ</button>
</form>
</div>

</body>
</html>
