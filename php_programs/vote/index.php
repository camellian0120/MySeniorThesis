<?php
// index.php
require 'db.php';

// スレッド一覧を取得（終了時間が新しい順）
$stmt = $pdo->query("SELECT * FROM polls ORDER BY created_at DESC");
$polls = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>投票アプリ - メイン</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="header">
        <h1>スレッド一覧</h1>
        <a href="create.php" class="btn btn-primary">＋ スレッド作成</a>
    </div>

    <div class="poll-list">
        <?php if (count($polls) === 0): ?>
            <p>現在スレッドはありません。</p>
        <?php else: ?>
            <?php foreach ($polls as $poll): ?>
                <?php 
                    $is_expired = new DateTime() > new DateTime($poll['end_time']);
                    $status_text = $is_expired ? '<span style="color:red">【終了】</span>' : '<span style="color:green">【受付中】</span>';
                ?>
                <a href="vote.php?id=<?= h($poll['id']) ?>" class="poll-link">
                    <div class="card">
                        <h2><?= $status_text ?> <?= h($poll['title']) ?></h2>
                        <div class="meta">終了日時: <?= h($poll['end_time']) ?></div>
                    </div>
                </a>
            <?php endforeach; ?>
        <?php endif; ?>
    </div>
</body>
</html>