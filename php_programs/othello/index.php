<?php
session_start();

/* ------------------------
    初期化処理
------------------------ */
if (!isset($_SESSION['board'])) {
    // 8x8 の盤面
    $board = array_fill(0, 8, array_fill(0, 8, ' '));

    // 初期配置
    $board[3][3] = 'W';
    $board[3][4] = 'B';
    $board[4][3] = 'B';
    $board[4][4] = 'W';

    $_SESSION['board'] = $board;
    $_SESSION['turn'] = 'B'; // B = 黒, W = 白
}

/* ------------------------
    関数定義
------------------------ */

// 盤面内かどうか
function inBoard($x, $y) {
    return $x >= 0 && $x < 8 && $y >= 0 && $y < 8;
}

// 裏返せるか調べる（裏返せる石のリストを返す）
function getFlips($board, $turn, $x, $y) {
    if ($board[$y][$x] !== ' ') return [];

    $enemy = ($turn === 'B') ? 'W' : 'B';
    $dirs = [
        [1,0],[-1,0],[0,1],[0,-1],
        [1,1],[1,-1],[-1,1],[-1,-1]
    ];

    $flips_total = [];

    foreach ($dirs as $d) {
        $dx = $d[0];
        $dy = $d[1];
        $cx = $x + $dx;
        $cy = $y + $dy;
        $flips = [];

        while (inBoard($cx, $cy) && $board[$cy][$cx] === $enemy) {
            $flips[] = [$cx, $cy];
            $cx += $dx;
            $cy += $dy;
        }

        if (inBoard($cx, $cy) && $board[$cy][$cx] === $turn && count($flips) > 0) {
            $flips_total = array_merge($flips_total, $flips);
        }
    }

    return $flips_total;
}

// 現在のターンで置ける場所のリスト
function getValidMoves($board, $turn) {
    $moves = [];
    for ($y=0; $y<8; $y++) {
        for ($x=0; $x<8; $x++) {
            if (count(getFlips($board, $turn, $x, $y)) > 0) {
                $moves[] = [$x, $y];
            }
        }
    }
    return $moves;
}

// 石の個数を数える
function countStones($board) {
    $black = 0; $white = 0;
    foreach ($board as $row) {
        foreach ($row as $c) {
            if ($c === 'B') $black++;
            if ($c === 'W') $white++;
        }
    }
    return [$black, $white];
}

/* ------------------------
    クリック処理
------------------------ */
if (isset($_GET['x']) && isset($_GET['y'])) {
    $x = intval($_GET['x']);
    $y = intval($_GET['y']);
    $board = $_SESSION['board'];
    $turn = $_SESSION['turn'];

    $flips = getFlips($board, $turn, $x, $y);
    if (count($flips) > 0) {
        // 石を置く
        $board[$y][$x] = $turn;
        foreach ($flips as $f) {
            $board[$f[1]][$f[0]] = $turn;
        }
        // ターン切り替え
        $turn = ($turn === 'B') ? 'W' : 'B';
    }

    // 次のターンで置ける場所がない場合、スキップ
    if (count(getValidMoves($board, $turn)) === 0) {
        $turn = ($turn === 'B') ? 'W' : 'B';

        // 両方置けなければ終了
        if (count(getValidMoves($board, $turn)) === 0) {
            $_SESSION['gameover'] = true;
        }
    }

    $_SESSION['board'] = $board;
    $_SESSION['turn'] = $turn;
}

/* ------------------------
    結果判定
------------------------ */
list($black, $white) = countStones($_SESSION['board']);
$total = $black + $white;

$gameover = false;
$reason = "";

if ($total == 64 || $black == 0 || $white == 0) {
    $gameover = true;
}

if (isset($_SESSION['gameover'])) {
    $gameover = true;
}

?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>PHP オセロ</title>
<style>
    table {
        border-collapse: collapse;
        margin: 20px auto;
    }
    td {
        width: 50px;
        height: 50px;
        border: 1px solid #333;
        text-align: center;
        vertical-align: middle;
        font-size: 30px;
        background-color: #0A7D00;
        cursor: pointer;
    }
    td.disabled {
        background-color: #0A7D00;
        cursor: default;
    }
</style>
</head>
<body>

<?php if (!$gameover): ?>
<h2 style="text-align:center;">
    <?php echo ($_SESSION['turn'] === 'B') ? "● 黒のターン" : "○ 白のターン"; ?>
</h2>
<?php else: ?>
<h2 style="text-align:center;">ゲーム終了</h2>
<h3 style="text-align:center;">
    黒：<?php echo $black; ?> / 白：<?php echo $white; ?><br>
    <?php
    if ($black > $white) echo "勝者：黒（●）";
    else if ($white > $black) echo "勝者：白（○）";
    else echo "引き分け";
    ?>
</h3>
<p style="text-align:center;">
    <a href="index.php?reset=1">もう一度遊ぶ</a>
</p>
<?php endif; ?>

<?php
if (isset($_GET['reset'])) {
    session_destroy();
    header("Location: index.php");
    exit;
}
?>

<table>
<?php
$turn = $_SESSION['turn'];
$board = $_SESSION['board'];
$validMoves = getValidMoves($board, $turn);

$validMap = [];
foreach ($validMoves as $vm) {
    $validMap[$vm[1]][$vm[0]] = true;
}

for ($y=0; $y<8; $y++) {
    echo "<tr>";
    for ($x=0; $x<8; $x++) {
        $stone = $board[$y][$x];
        $char = " ";
        if ($stone === 'B') $char = "●";
        if ($stone === 'W') $char = "○";

        if (!$gameover && isset($validMap[$y][$x])) {
            echo "<td><a href=\"?x=$x&y=$y\" style='display:block;width:100%;height:100%;text-decoration:none;color:black;'>$char</a></td>";
        } else {
            echo "<td class='disabled'>$char</td>";
        }
    }
    echo "</tr>";
}
?>
</table>

</body>
</html>
