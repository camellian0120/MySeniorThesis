# Qwen3's test

# imports
from unsloth import FastLanguageModel
import torch

# make response qwen
def run_qwen():
    # settings
    models = [
        "unsloth/Qwen3-14B-unsloth-bnb-4bit",
        "unsloth/Qwen3-14B-128K-GGUF",
        "unsloth/Qwen3-32B-unsloth-bnb-4bit",
        "unsloth/Qwen3-32B-128K-GGUF"
    ]
    model = models[0]
    max_seq_length = 40960
    # max_seq_length = 65535

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model,
        max_seq_length = max_seq_length,# Context length
        load_in_4bit = True,            # 4bit uses much less memory
        load_in_8bit = False,           # A bit more accurate, uses 2x memory
    )
    
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
--- index.php
<?php
// index.php
session_start();

// load maze data
$mazes = include __DIR__ . '/maze_data.php';

// choose maze id (固定で sample1 を使うが、選択UIを後で追加可能)
$maze_id = 'sample1';

if (!isset($mazes[$maze_id])) {
    echo "Maze not found.";
    exit;
}

$maze = $mazes[$maze_id];

// initialize session if new or restart requested
if (!isset($_SESSION['maze']) || ($_SESSION['maze_id'] ?? '') !== $maze_id || isset($_GET['restart'])) {
    // store maze as array of strings
    $_SESSION['maze'] = $maze;
    $_SESSION['maze_id'] = $maze_id;
    $_SESSION['steps'] = 0;
    $_SESSION['start_time'] = time();
    // find start position S
    $start = null;
    foreach ($_SESSION['maze'] as $r => $row) {
        $c = strpos($row, 'S');
        if ($c !== false) {
            $start = ['r' => $r, 'c' => $c];
            // replace 'S' with space in stored maze so server treats it as open cell
            $_SESSION['maze'][$r] = substr_replace($_SESSION['maze'][$r], ' ', $c, 1);
            break;
        }
    }
    if (!$start) {
        echo "Start position not found in maze data.";
        exit;
    }
    $_SESSION['player'] = $start;
    // find goal (for convenience)
    $goal = null;
    foreach ($_SESSION['maze'] as $r => $row) {
        $c = strpos($row, 'G');
        if ($c !== false) {
            $goal = ['r' => $r, 'c' => $c];
            // replace 'G' with 'G' left (we keep it for rendering)
            break;
        }
    }
    $_SESSION['goal'] = $goal;
}

// JSON-encode maze for client-side rendering
$maze_json = json_encode($_SESSION['maze'], JSON_HEX_TAG|JSON_HEX_APOS|JSON_HEX_QUOT|JSON_HEX_AMP);
$player_json = json_encode($_SESSION['player']);
$goal_json = json_encode($_SESSION['goal']);
$start_time = $_SESSION['start_time'];
$steps = $_SESSION['steps'];
?>
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PHP 2D 迷路ゲーム</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
  <h1>2D 迷路ゲーム</h1>
  <div class="controls">
    <button id="up">↑</button>
    <div>
      <button id="left">←</button>
      <button id="down">↓</button>
      <button id="right">→</button>
    </div>
    <button id="restart">Restart</button>
  </div>

  <div id="status">
    <span>ステップ: <span id="steps"><?php echo htmlspecialchars($steps, ENT_QUOTES); ?></span></span>
    <span>経過: <span id="elapsed">0s</span></span>
  </div>

  <div id="maze"></div>

  <div id="message" class="message"></div>
</div>

<script>
const maze = <?php echo $maze_json; ?>;
let player = <?php echo $player_json; ?>;
const goal = <?php echo $goal_json; ?>;
let startTime = <?php echo json_encode($start_time); ?>;
let steps = <?php echo json_encode($steps); ?>;

const mazeEl = document.getElementById('maze');
const messageEl = document.getElementById('message');
const stepsEl = document.getElementById('steps');
const elapsedEl = document.getElementById('elapsed');

function renderMaze() {
  // create grid
  mazeEl.innerHTML = '';
  const rows = maze.length;
  const cols = maze[0].length;
  const table = document.createElement('div');
  table.className = 'grid';
  table.style.gridTemplateColumns = `repeat(${cols}, 32px)`;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const ch = maze[r].charAt(c);
      const cell = document.createElement('div');
      cell.className = 'cell';
      if (ch === '#') {
        cell.classList.add('wall');
      } else if (r === goal.r && c === goal.c) {
        cell.classList.add('goal');
        cell.textContent = 'G';
      } else {
        // empty
      }
      if (r === player.r && c === player.c) {
        const p = document.createElement('div');
        p.className = 'player';
        p.textContent = 'P';
        cell.appendChild(p);
      }
      table.appendChild(cell);
    }
  }
  mazeEl.appendChild(table);
}

function setMessage(msg, isError = false) {
  messageEl.textContent = msg;
  messageEl.className = isError ? 'message error' : 'message';
}

// ask server to move; server returns updated player pos and status
async function sendMove(direction) {
  try {
    const res = await fetch('move.php', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({dir: direction})
    });
    if (!res.ok) {
      setMessage('通信エラー: ' + res.status, true);
      return;
    }
    const data = await res.json();
    if (data.error) {
      setMessage('エラー: ' + data.error, true);
      return;
    }
    // update local state
    player = data.player;
    steps = data.steps;
    stepsEl.textContent = steps;
    renderMaze();
    if (data.cleared) {
      const sec = data.elapsed;
      setMessage(`クリア！ ステップ ${steps}、経過時間 ${sec} 秒`);
    } else {
      setMessage('');
    }
  } catch (e) {
    setMessage('例外: ' + e.message, true);
  }
}

// keyboard control
window.addEventListener('keydown', (ev) => {
  if (ev.key === 'ArrowUp') { ev.preventDefault(); sendMove('up'); }
  if (ev.key === 'ArrowDown') { ev.preventDefault(); sendMove('down'); }
  if (ev.key === 'ArrowLeft') { ev.preventDefault(); sendMove('left'); }
  if (ev.key === 'ArrowRight') { ev.preventDefault(); sendMove('right'); }
});

// buttons
document.getElementById('up').addEventListener('click', () => sendMove('up'));
document.getElementById('down').addEventListener('click', () => sendMove('down'));
document.getElementById('left').addEventListener('click', () => sendMove('left'));
document.getElementById('right').addEventListener('click', () => sendMove('right'));

document.getElementById('restart').addEventListener('click', () => {
  // reload with restart param to reset session
  window.location.href = window.location.pathname + '?restart=1';
});

// elapsed timer
function updateElapsed() {
  const now = Math.floor(Date.now() / 1000);
  const elapsed = now - startTime;
  elapsedEl.textContent = elapsed + 's';
}
setInterval(updateElapsed, 1000);

// initial render
renderMaze();
updateElapsed();
</script>
</body>
</html>

--- move.php
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

---  maze_data.php
<?php
// 迷路データを配列で返す（参照 / include して使う）
// 文字: '#' 壁, ' ' 通路, 'S' スタート, 'G' ゴール

return [
    // maze id => array of rows (strings)
    'sample1' => [
        "#############",
        "#S    #     #",
        "# ##  # ### #",
        "#    ##   # #",
        "#### ###  # #",
        "#      #   G#",
        "# ###### ####",
        "#          ##",
        "#############"
    ],
];
    """

    messages = [{"role" : "user", "content" : prompt}]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize = False,
        add_generation_prompt = True, # Must add for generation
        enable_thinking = True, # Disable thinking
    )

    from transformers import TextStreamer
    _ = model.generate(
        **tokenizer(text, return_tensors = "pt").to("cuda"),
        max_new_tokens = 4096, # Increase for longer outputs!
        temperature = 0.6,
        top_p = 0.95,
        top_k = 20,
        streamer = TextStreamer(tokenizer, skip_prompt = True),
    )

if "__main__" in __name__:
    run_qwen()

