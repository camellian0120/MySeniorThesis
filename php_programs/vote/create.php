<?php
// create.php
require 'db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $title = $_POST['title'];
    $end_time = $_POST['end_time'];
    $options = $_POST['options']; // 配列として受け取る

    // バリデーション（空欄チェック）
    $valid_options = array_filter($options, function($v) { return trim($v) !== ''; });
    
    if ($title && $end_time && count($valid_options) >= 2) {
        // トランザクション開始
        $pdo->beginTransaction();
        try {
            // スレッド保存
            $stmt = $pdo->prepare("INSERT INTO polls (title, end_time) VALUES (?, ?)");
            $stmt->execute([$title, $end_time]);
            $poll_id = $pdo->lastInsertId();

            // 選択肢保存
            $stmt_opt = $pdo->prepare("INSERT INTO options (poll_id, name) VALUES (?, ?)");
            foreach ($valid_options as $opt_name) {
                $stmt_opt->execute([$poll_id, $opt_name]);
            }

            $pdo->commit();
            header("Location: index.php"); // メインへリダイレクト
            exit;
        } catch (Exception $e) {
            $pdo->rollBack();
            $error = "作成に失敗しました。";
        }
    } else {
        $error = "タイトル、終了時間、および2つ以上の選択肢を入力してください。";
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>スレッド作成</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="header">
        <h1>新規スレッド作成</h1>
    </div>

    <?php if (isset($error)): ?>
        <p style="color: red;"><?= h($error) ?></p>
    <?php endif; ?>

    <form method="post" id="createForm">
        <div class="form-group">
            <label>タイトル</label>
            <input type="text" name="title" class="form-control" required placeholder="例: 好きなプログラミング言語は？">
        </div>

        <div class="form-group">
            <label>終了時間</label>
            <input type="datetime-local" name="end_time" class="form-control" required>
        </div>

        <div class="form-group">
            <label>選択肢 (2つ以上必須)</label>
            <div id="options-container">
                <input type="text" name="options[]" class="form-control" placeholder="選択肢 1" required style="margin-bottom:5px;">
                <input type="text" name="options[]" class="form-control" placeholder="選択肢 2" required style="margin-bottom:5px;">
            </div>
            <div class="add-option" onclick="addOption()">＋ 選択肢を追加する</div>
        </div>

        <div style="margin-top: 20px;">
            <button type="submit" class="btn btn-primary">作成する</button>
            <a href="index.php" class="btn btn-secondary">キャンセル</a>
        </div>
    </form>

    <script>
        function addOption() {
            const container = document.getElementById('options-container');
            const input = document.createElement('input');
            input.type = 'text';
            input.name = 'options[]';
            input.className = 'form-control';
            input.placeholder = '選択肢 ' + (container.children.length + 1);
            input.style.marginBottom = '5px';
            input.required = true;
            container.appendChild(input);
        }
    </script>
</body>
</html>