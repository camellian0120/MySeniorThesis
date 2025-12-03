<?php
// db.php
try {
    // データベースファイルを作成/接続
    $pdo = new PDO('sqlite:voting_app.db');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // スレッド（polls）テーブル作成
    $pdo->exec("CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        end_time DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )");

    // 選択肢（options）テーブル作成
    $pdo->exec("CREATE TABLE IF NOT EXISTS options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER,
        name TEXT NOT NULL,
        votes INTEGER DEFAULT 0,
        FOREIGN KEY (poll_id) REFERENCES polls(id)
    )");

} catch (PDOException $e) {
    die("データベース接続エラー: " . $e->getMessage());
}

// XSS対策用関数
function h($str) {
    return htmlspecialchars($str, ENT_QUOTES, 'UTF-8');
}
?>