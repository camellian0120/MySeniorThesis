<?php
// php_d100_roller.php - 修正版（CSRF / セッション設定 / XSS対策 / レート制限 等を追加）
declare(strict_types=1);

// セキュリティヘッダ（早めに送る）
header("Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self';");
header("X-Content-Type-Options: nosniff");
header("X-Frame-Options: SAMEORIGIN");

// セッション Cookie の安全なパラメータ設定（session_start の前に設定）
$secureFlag = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || ($_SERVER['SERVER_PORT'] ?? '') == '443';
session_set_cookie_params([
    'lifetime' => 0,               // ブラウザ終了で消える
    'secure' => $secureFlag,       // HTTPS 時は true に
    'httponly' => true,            // JS からはアクセス不可
    'samesite' => 'Lax'            // クロスサイト送信を制限
]);
session_start();

// セッション固定化対策（初回のみID再生成）
if (empty($_SESSION['initiated'])) {
    session_regenerate_id(true);
    $_SESSION['initiated'] = true;
}

// 初期化
if (!isset($_SESSION['d100_history'])) {
    $_SESSION['d100_history'] = [];
}
if (!isset($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// 簡易レートリミッタ（例: 10回 / 60秒）
$rateLimitWindow = 60; // 秒
$rateLimitMax = 10;
if (!isset($_SESSION['rolls_window'])) {
    $_SESSION['rolls_window'] = ['start' => time(), 'count' => 0];
}
if (time() - $_SESSION['rolls_window']['start'] > $rateLimitWindow) {
    $_SESSION['rolls_window'] = ['start' => time(), 'count' => 0];
}

// POST処理
$errors = [];
$results = [];
$total = 0;
$count = 1;
$label = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // CSRF 検証
    $posted_csrf = $_POST['csrf_token'] ?? '';
    if (!is_string($posted_csrf) || !hash_equals($_SESSION['csrf_token'], $posted_csrf)) {
        http_response_code(400);
        $errors[] = '無効なリクエストです（CSRF検証に失敗しました）。';
    }

    // レート制限チェック
    if (empty($errors)) {
        $_SESSION['rolls_window']['count']++;
        if ($_SESSION['rolls_window']['count'] > $rateLimitMax) {
            $errors[] = '短時間に多数のリクエストがありました。しばらく待ってから再度実行してください。';
        }
    }

    // count を安全に取得・制限（1〜100）
    if (empty($errors)) {
        $raw_count = filter_input(INPUT_POST, 'count', FILTER_VALIDATE_INT, [
            'options' => ['default' => 1, 'min_range' => 1, 'max_range' => 100]
        ]);
        $count = (int)$raw_count;
        if ($count < 1) $count = 1;
        if ($count > 100) $count = 100;
    }

    // label の制限（最大200文字、制御文字除去）
    if (empty($errors)) {
        $label_raw = isset($_POST['label']) ? (string)$_POST['label'] : '';
        // 制御文字を除去
        $label_clean = preg_replace('/[\x00-\x1F\x7F]/u', '', $label_raw);
        // 最大200文字（マルチバイト対応）
        $label = mb_substr($label_clean, 0, 200, 'UTF-8');
    }

    // 実行（ランダム生成）
    if (empty($errors)) {
        for ($i = 0; $i < $count; $i++) {
            $roll = random_int(1, 100); // 暗号学的乱数
            $results[] = $roll;
            $total += $roll;
        }

        // 履歴へ追加（新しい順）
        $entry = [
            'time' => date('Y-m-d H:i:s'),
            'count' => $count,
            'label' => $label,
            'results' => $results,
            'total' => $total,
        ];
        array_unshift($_SESSION['d100_history'], $entry);

        // 履歴の上限を100に保つ（メモリ肥大防止）
        if (count($_SESSION['d100_history']) > 100) {
            $_SESSION['d100_history'] = array_slice($_SESSION['d100_history'], 0, 100);
        }
    }
}

$history = $_SESSION['d100_history'] ?? [];

// エスケープ用関数（一貫して使用）
function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}
?>
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>100-sided Dice Roller (安全版)</title>
<style>
    body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; padding: 20px; }
    .box { max-width: 820px; margin: 0 auto; }
    input[type="number"] { width: 80px; }
    .badge { display:inline-block; padding:6px 10px; margin:4px; border-radius:6px; background:#eee; }
    .roll { font-weight:700; }
    .history { margin-top:20px; }
    .card { padding:12px; border:1px solid #ddd; border-radius:8px; margin-bottom:12px; }
    .muted { color:#666; font-size:0.9rem; }
    .error { color:#b00; }
</style>
</head>
<body>
<div class="box">
    <h1>100-sided Dice Roller（安全版）</h1>

    <?php if (!empty($errors)): ?>
        <div class="card error">
            <?php foreach ($errors as $err): ?>
                <p class="error"><?php echo h($err); ?></p>
            <?php endforeach; ?>
        </div>
    <?php endif; ?>

    <form method="post" action="">
        <label>Number of rolls (1–100):
            <input type="number" name="count" value="<?php echo h((string)$count); ?>" min="1" max="100" required>
        </label>
        &nbsp;
        <label>Label (optional):
            <input type="text" name="label" value="<?php echo h($label); ?>" maxlength="200" placeholder="最大200文字">
        </label>
        &nbsp;
        <input type="hidden" name="csrf_token" value="<?php echo h($_SESSION['csrf_token']); ?>">
        <button type="submit">Roll</button>
    </form>

    <?php if (!empty($results)): ?>
    <div class="card">
        <div class="muted">Timestamp: <?php echo h($entry['time']); ?></div>
        <h2>Results</h2>
        <div>
        <?php foreach ($results as $i => $r): ?>
            <span class="badge roll">#<?php echo h((string)($i + 1)); ?>: <?php echo h((string)$r); ?></span>
        <?php endforeach; ?>
        </div>
        <p>Total: <strong><?php echo h((string)$total); ?></strong> / Average: <strong><?php echo h((string)(count($results) ? round($total / count($results), 2) : 0)); ?></strong></p>
        <?php if ($entry['label'] !== ''): ?><p>Label: <?php echo h($entry['label']); ?></p><?php endif; ?>
    </div>
    <?php endif; ?>

    <div class="history">
    <h2>History (last <?php echo h((string)count($history)); ?> rolls)</h2>
    <?php if (empty($history)): ?>
        <p class="muted">No rolls yet.</p>
    <?php else: ?>
        <?php foreach ($history as $idx => $h): ?>
        <div class="card">
            <div class="muted"><?php echo h($h['time']); ?> — Rolls: <?php echo h((string)$h['count']); ?><?php if ($h['label'] !== ''): ?> — Label: <?php echo h($h['label']); ?><?php endif; ?></div>
            <div style="margin-top:8px;">
            <?php foreach ($h['results'] as $i => $r): ?>
                <span class="badge"><?php echo h((string)$r); ?></span>
            <?php endforeach; ?>
            </div>
            <p style="margin-top:8px;">Total: <?php echo h((string)$h['total']); ?> / Average: <?php echo h((string)(count($h['results']) ? round($h['total'] / count($h['results']), 2) : 0)); ?></p>
        </div>
        <?php endforeach; ?>
    <?php endif; ?>
    </div>

    <div style="margin-top:20px;" class="muted">
    <p>Note: Uses <code>random_int(1, 100)</code> for cryptographically secure random number generation. The session keeps up to 100 history entries. CSRFトークン、セッションCookie属性、入力長制限、簡易レート制限を実装しています。</p>
    </div>
</div>
</body>
</html>
