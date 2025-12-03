<?php
// vote.php
require 'db.php';

$poll_id = $_GET['id'] ?? null;
if (!$poll_id) { header("Location: index.php"); exit; }

// スレッド情報の取得
$stmt = $pdo->prepare("SELECT * FROM polls WHERE id = ?");
$stmt->execute([$poll_id]);
$poll = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$poll) { die("スレッドが見つかりません"); }

// 選択肢情報の取得
$stmt = $pdo->prepare("SELECT * FROM options WHERE poll_id = ?");
$stmt->execute([$poll_id]);
$options = $stmt->fetchAll(PDO::FETCH_ASSOC);

// 状態判定
$cookie_name = "voted_poll_" . $poll_id;
$has_voted = isset($_COOKIE[$cookie_name]);
$is_expired = new DateTime() > new DateTime($poll['end_time']);
$show_results = $has_voted || $is_expired;

// 投票処理（POST時）
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !$show_results) {
    $option_id = $_POST['option_id'];
    
    // 投票数を加算
    $stmt = $pdo->prepare("UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?");
    $stmt->execute([$option_id, $poll_id]);

    // Cookieをセット（有効期限30日）
    setcookie($cookie_name, '1', time() + (86400 * 30), "/");
    
    // 再読み込みして結果を表示
    header("Location: vote.php?id=" . $poll_id);
    exit;
}

// 総投票数の計算（割合表示用）
$total_votes = 0;
foreach ($options as $opt) { $total_votes += $opt['votes']; }
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title><?= h($poll['title']) ?> - 投票</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="header">
        <h1>投票画面</h1>
        <a href="index.php" class="btn btn-secondary">← 一覧に戻る</a>
    </div>

    <div class="card">
        <h2><?= h($poll['title']) ?></h2>
        <p class="meta">終了期限: <?= h($poll['end_time']) ?></p>
        
        <?php if ($is_expired && !$has_voted): ?>
            <p style="color: red;">※ この投票は終了しました。</p>
        <?php elseif ($has_voted): ?>
            <p style="color: green;">※ 投票済みです。</p>
        <?php endif; ?>

        <hr>

        <?php if ($show_results): ?>
            <h3>現在の投票結果（総数: <?= $total_votes ?>票）</h3>
            <?php foreach ($options as $opt): ?>
                <?php 
                    $percent = $total_votes > 0 ? round(($opt['votes'] / $total_votes) * 100) : 0;
                ?>
                <div style="margin-bottom: 15px;">
                    <div><?= h($opt['name']) ?> (<?= $opt['votes'] ?>票)</div>
                    <div class="result-bar-bg">
                        <div class="result-bar-fill" style="width: <?= $percent ?>%;"></div>
                        <div class="result-text"><?= $percent ?>%</div>
                    </div>
                </div>
            <?php endforeach; ?>

        <?php else: ?>
            <form method="post">
                <?php foreach ($options as $opt): ?>
                    <button type="submit" name="option_id" value="<?= $opt['id'] ?>" class="btn btn-vote">
                        <?= h($opt['name']) ?> に投票する
                    </button>
                <?php endforeach; ?>
            </form>
        <?php endif; ?>
    </div>
</body>
</html>