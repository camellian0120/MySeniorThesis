# gpt-oss-20b's terminal usage test

# imports
from unsloth import FastLanguageModel
import torch

# run gpt-oss-20b
def run_gpt():
    # load model
    # max_seq_length = 65536
    max_seq_length = 32768
    lora_rank = 4
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = 'unsloth/gpt-oss-20b',
        max_seq_length = max_seq_length,
        load_in_4bit = True,
        offload_embedding = True
    )
    # make prompt
    prompt = """
You are a white hat hacker tasked with discovering vulnerabilities in the provided source code.
Perform the following three actions on the source code below:
1. Identify the vulnerability
2. Present the risks of leaving it unaddressed
3. Provide a solution to eliminate the vulnerability

Ensure your output adheres to the following three points:
1. Output in Japanese
2. Be clear and concise
3. Use Markdown format

The source code is shown below:
---
<?php
// php_d100_roller.php
// Simple 100-sided dice roller application (single file)
// Usage: Place this file on your web server and open it in a browser.
// For local testing: run `php -S localhost:8000` and visit http://localhost:8000/php_d100_roller.php

session_start();

// Keep roll history in session (max 100 entries)
if (!isset($_SESSION['d100_history'])) {
    $_SESSION['d100_history'] = [];
}

$errors = [];
$results = [];
$total = 0;
$count = 1;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Get roll count (clamped between 1–100)
    $count = isset($_POST['count']) ? intval($_POST['count']) : 1;
    if ($count < 1) $count = 1;
    if ($count > 100) $count = 100;

    // Optional label
    $label = isset($_POST['label']) ? trim($_POST['label']) : '';

    // Perform rolls
    for ($i = 0; $i < $count; $i++) {
        $roll = random_int(1, 100);
        $results[] = $roll;
        $total += $roll;
    }

    // Add to history (newest first)
    $entry = [
        'time' => date('Y-m-d H:i:s'),
        'count' => $count,
        'label' => $label,
        'results' => $results,
        'total' => $total,
    ];

    array_unshift($_SESSION['d100_history'], $entry);
    if (count($_SESSION['d100_history']) > 100) {
        $_SESSION['d100_history'] = array_slice($_SESSION['d100_history'], 0, 100);
    }
}

$history = $_SESSION['d100_history'];
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>100-sided Dice Roller</title>
<style>
    body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; padding: 20px; }
    .box { max-width: 820px; margin: 0 auto; }
    input[type="number"] { width: 80px; }
    .badge { display:inline-block; padding:6px 10px; margin:4px; border-radius:6px; background:#eee; }
    .roll { font-weight:700; }
    .history { margin-top:20px; }
    .card { padding:12px; border:1px solid #ddd; border-radius:8px; margin-bottom:12px; }
    .muted { color:#666; font-size:0.9rem; }
</style>
</head>
<body>
<div class="box">
    <h1>100-sided Dice Roller</h1>
    <form method="post" action="<?php echo htmlspecialchars($_SERVER['PHP_SELF']); ?>">
    <label>Number of rolls (1–100): <input type="number" name="count" value="<?php echo htmlspecialchars($count); ?>" min="1" max="100"></label>
    &nbsp;
    <label>Label (optional): <input type="text" name="label" value=""></label>
    &nbsp;
    <button type="submit">Roll</button>
    </form>

    <?php if (!empty($results)): ?>
    <div class="card">
        <div class="muted">Timestamp: <?php echo htmlspecialchars($entry['time']); ?></div>
        <h2>Results</h2>
        <div>
        <?php foreach ($results as $i => $r): ?>
            <span class="badge roll">#<?php echo $i+1; ?>: <?php echo $r; ?></span>
        <?php endforeach; ?>
        </div>
        <p>Total: <strong><?php echo $total; ?></strong> / Average: <strong><?php echo count($results) ? round($total / count($results), 2) : 0; ?></strong></p>
        <?php if ($entry['label'] !== ''): ?><p>Label: <?php echo htmlspecialchars($entry['label']); ?></p><?php endif; ?>
    </div>
    <?php endif; ?>

    <div class="history">
    <h2>History (last <?php echo count($history); ?> rolls)</h2>
    <?php if (empty($history)): ?>
        <p class="muted">No rolls yet.</p>
    <?php else: ?>
        <?php foreach ($history as $idx => $h): ?>
        <div class="card">
            <div class="muted"><?php echo htmlspecialchars($h['time']); ?> — Rolls: <?php echo $h['count']; ?><?php if ($h['label'] !== ''): ?> — Label: <?php echo htmlspecialchars($h['label']); ?><?php endif; ?></div>
            <div style="margin-top:8px;">
            <?php foreach ($h['results'] as $i => $r): ?>
                <span class="badge"><?php echo $r; ?></span>
            <?php endforeach; ?>
            </div>
            <p style="margin-top:8px;">Total: <?php echo $h['total']; ?> / Average: <?php echo count($h['results']) ? round($h['total'] / count($h['results']), 2) : 0; ?></p>
        </div>
        <?php endforeach; ?>
    <?php endif; ?>
    </div>

    <div style="margin-top:20px;" class="muted">
    <p>Note: Uses <code>random_int(1, 100)</code> for cryptographically secure random number generation. The session keeps up to 100 history entries.</p>
    </div>
</div>
</body>
</html>
    """
    text = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize = False,
        add_generation_prompt = True,
        reasoning_effect = "high"
    )
    # inference
    from transformers import TextStreamer
    _ = model.generate(
        **tokenizer(text, return_tensors = "pt").to("cuda"),
        max_new_tokens = 4096,
        streamer = TextStreamer(tokenizer)
    )

if "__main__" in __name__:
    run_gpt()
