import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def run_qwen(prompt):
    model_name = "unsloth/Qwen3-14B-unsloth-bnb-4bit"
    max_seq_length = 40960

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        max_seq_length = max_seq_length,
        load_in_4bit = True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="eager",
    )

    # ★ attention を有効化
    model.config.output_attentions = True
    model.eval()

    messages = [{"role": "user", "content": prompt}]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking = False,
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=4096,
            temperature=0.6,
            top_p=0.95,
            top_k=20,
            return_dict_in_generate=True,
            output_attentions=True,
        )

    print(tokenizer.decode(outputs.sequences[0], skip_special_tokens=True))

    # attentions:
    # tuple(num_layers)
    #   └─ tuple(num_steps)
    #        └─ Tensor(batch, heads, tgt_len, src_len)
    attentions = outputs.attentions

    # ===== 最終レイヤ =====
    last_layer = attentions[-1]

    # ===== 最終生成ステップ =====
    last_step_attn = last_layer[-1]  # Tensor(batch, heads, tgt_len, src_len)

    # ===== 最後に生成された1トークン =====
    last_token_attn = last_step_attn[:, :, -1, :]  # (batch, heads, src_len)

    # ===== ヘッド平均 =====
    attn_scores = last_token_attn.mean(dim=1).squeeze(0)  # (src_len,)

    # ===== 入力トークン =====
    input_ids = inputs["input_ids"][0]
    tokens = tokenizer.convert_ids_to_tokens(input_ids)

    # 長さ調整（安全）
    seq_len = min(len(attn_scores), len(tokens))
    attn_scores = attn_scores[:seq_len]
    tokens = tokens[:seq_len]
    input_ids = input_ids[:seq_len]

    # ===== 上位トークン =====
    k = min(15, seq_len)
    topk = torch.topk(attn_scores, k=k)

    print("\n=== 出力決定時に強く参照された入力トークン（特殊トークン含む）===")
    for score, idx in zip(topk.values, topk.indices):
        idx = idx.item()
        token = tokens[idx]
        text_piece = tokenizer.decode([input_ids[idx]])
        print(f"{score.item():.4f} | idx={idx:4d} | token='{token}' | text='{text_piece}'")


if "__main__" in __name__:
    prompt = """
    You are a white hat hacker tasked with discovering vulnerabilities in the provided source code.

    Perform the following three actions on the source code below:
    1. Check for XSS, CSRF, and session-related vulnerabilities
    2. Present the risks of leaving it unaddressed
    3. Provide a solution to eliminate the vulnerability

    Additionally, for each identified vulnerability, assign a confidence score indicating 
    the likelihood that the vulnerability actually exists in the source code.

    - The score must be a real number between 0.0 and 1.0
    - 0.0 means "the vulnerability definitely does not exist"
    - 1.0 means "the vulnerability definitely exists"
    - The score should reflect your confidence based solely on evidence in the code

    When assigning the score:
    - Use ≥ 0.8 if clear exploitable patterns are present
    - Use 0.4–0.7 if the vulnerability is plausible but uncertain
    - Use ≤ 0.3 if little to no evidence is found

    Ensure your output adheres to the following three points:
    1. Output in Japanese
    2. Be clear and concise
    3. Use Markdown format

    ---
    """

    args = sys.argv
    if args[1] == 1:
        prompt+="""
<?php
// --- サーバーサイド (PHP) ---
// ユーザーからの入力を処理する部分です

$alarmTime = "";
$message = "アラーム時間をセットしてください。";

// フォームが送信されたか確認
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // 入力を取得
    if (isset($_POST['set_time']) && !empty($_POST['set_time'])) {
        // 入力された時間を変数に格納（サニタイズ処理）
        $alarmTime = htmlspecialchars($_POST['set_time'], ENT_QUOTES, 'UTF-8');
        $message = "アラームを **" . $alarmTime . "** に設定しました！";
    }
}
?>

<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PHP Alarm Clock</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; background-color: #f0f0f0; }
        .clock-container { background: white; padding: 30px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { font-size: 3em; margin: 10px 0; color: #333; }
        .status { margin-bottom: 20px; color: #007bff; font-weight: bold; }
        form { margin-top: 20px; }
        input[type="time"] { padding: 10px; font-size: 1.2em; border-radius: 5px; border: 1px solid #ccc; }
        button { padding: 10px 20px; font-size: 1.2em; background-color: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #218838; }
    </style>
</head>
<body>

<div class="clock-container">
    <h2>現在時刻</h2>
    <h1 id="clock">00:00:00</h1>
    
    <div class="status">
        <?php echo $message; ?>
    </div>

    <form method="POST" action="">
        <input type="time" name="set_time" required value="<?php echo $alarmTime; ?>">
        <button type="submit">設定する</button>
    </form>
</div>

<script>
    // --- クライアントサイド (JavaScript) ---
    // PHPから受け取った時間をJSの変数に渡す
    let alarmTarget = "<?php echo $alarmTime; ?>"; 
    let alarmTriggered = false; // 重複アラーム防止フラグ

    function updateClock() {
        const now = new Date();
        
        // 時・分・秒のフォーマット (2桁埋め)
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        // 時計表示の更新
        document.getElementById('clock').textContent = `${hours}:${minutes}:${seconds}`;

        // アラームチェック (秒まで待つと長いので、分単位で一致したら鳴らす)
        const currentTimeString = `${hours}:${minutes}`;

        // アラームが設定されていて、まだ鳴っていなくて、時間が一致した場合
        if (alarmTarget !== "" && currentTimeString === alarmTarget && !alarmTriggered) {
            playAlarm();
            alarmTriggered = true; // 1分間鳴り続けないようにフラグを立てる
        }
    }

    function playAlarm() {
        // シンプルにアラートを表示
        // 音声を鳴らしたい場合はここに audio.play() などを記述します
        alert("時間です！ (" + alarmTarget + ")");
        
        // 実際のアラーム音を鳴らしたい場合の例（コメントアウト）:
        // let audio = new Audio('alarm_sound.mp3');
        // audio.play();
    }

    // 1秒ごとに時計を更新
    setInterval(updateClock, 1000);
    
    // 初回実行
    updateClock();
</script>

</body>
</html>
"""
    elif args[1] == 2:
        prompt+="""
<?php
// index.php
// Single-file Brick Breaker (PHP + Canvas + JS).
// - GET: serve page (embeds current highscore from highscore.txt).
// - POST?action=save : accept JSON {score:int} to update highscore (file locked).

$hs_file = __DIR__ . '/highscore.txt';

// Handle save endpoint
if (isset($_GET['action']) && $_GET['action'] === 'save' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true);
    if (!is_array($data) || !isset($data['score'])) {
        http_response_code(400);
        echo json_encode(['ok' => false, 'msg' => 'invalid']);
        exit;
    }
    $score = (int)$data['score'];
    // read existing
    if (!file_exists($hs_file)) {
        file_put_contents($hs_file, "0");
    }
    $fp = fopen($hs_file, 'c+');
    if (!$fp) {
        http_response_code(500);
        echo json_encode(['ok' => false, 'msg' => 'cannot open file']);
        exit;
    }
    flock($fp, LOCK_EX);
    $contents = stream_get_contents($fp);
    $current = intval(trim($contents === '' ? '0' : $contents));
    if ($score > $current) {
        // overwrite
        ftruncate($fp, 0);
        rewind($fp);
        fwrite($fp, (string)$score);
        fflush($fp);
    }
    flock($fp, LOCK_UN);
    fclose($fp);
    echo json_encode(['ok' => true, 'highscore' => max($current, $score)]);
    exit;
}

// Serve page: read highscore
$highscore = 0;
if (file_exists($hs_file)) {
    $contents = @file_get_contents($hs_file);
    if ($contents !== false) {
        $highscore = intval(trim($contents));
    }
}
?>
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PHP ブロック崩し</title>
<style>
  body { background:#111; color:#eee; font-family:system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; margin:0; display:flex; align-items:flex-start; gap:20px; padding:16px; }
  #game { background:#000; border:4px solid #444; display:block; }
  #hud { width:260px; }
  .panel { background:#0f1720; padding:12px; border-radius:8px; box-shadow: 0 6px 18px rgba(0,0,0,.6); }
  h1 { margin:0 0 8px 0; font-size:18px; }
  button { padding:8px 12px; font-size:14px; border-radius:6px; border:0; background:#2563eb; color:white; cursor:pointer; }
  .small { font-size:13px; color:#cbd5e1; }
</style>
</head>
<body>
<canvas id="game" width="800" height="600"></canvas>

<div id="hud" class="panel">
  <h1>PHP ブロック崩し</h1>
  <div class="small">残機: <span id="lives">3</span></div>
  <div class="small">ステージ: <span id="stage">1</span> / <span id="stagesTotal">5</span></div>
  <div class="small">スコア: <span id="score">0</span></div>
  <div class="small">ハイスコア: <span id="highscore"><?php echo htmlspecialchars($highscore, ENT_QUOTES); ?></span></div>
  <div style="margin-top:12px;">
    <button id="startBtn">開始 / 再開</button>
    <button id="restartBtn">リスタート</button>
  </div>
  <hr style="margin:12px 0;border-color:#223;"/>
  <div class="small"><strong>操作</strong><br>マウス移動（または ← → キー）でバーを操作</div>
  <hr style="margin:12px 0;border-color:#223;"/>
  <div class="small"><strong>パワーアップ</strong>
    <ul>
      <li>大きなバー（時間制）</li>
      <li>マルチボール</li>
      <li>下の穴を一定時間塞ぐ</li>
    </ul>
  </div>
  <div style="margin-top:8px;" class="small">※ highscore.txt を同フォルダに作成し書き込み許可を与えてください</div>
</div>

<script>
(() => {
  // Canvas & context
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');

  // HUD elements
  const livesEl = document.getElementById('lives');
  const stageEl = document.getElementById('stage');
  const scoreEl = document.getElementById('score');
  const highscoreEl = document.getElementById('highscore');
  const startBtn = document.getElementById('startBtn');
  const restartBtn = document.getElementById('restartBtn');

  // Settings
  const STAGES_TOTAL = 5;
  const START_LIVES = 3;
  const POWERUP_COUNT_PER_STAGE = 5;
  const BASE_BALL_SPEED = 3.5;
  const SPEED_INCREASE_PER_ROUND = 0.6; // 全5ステージクリア後にボール速度に加算される
  const POWERUP_DURATION = 10000; // ms for size / hole-block

  // Game state
  let lives = START_LIVES;
  let score = 0;
  let highscore = parseInt(highscoreEl.textContent) || 0;
  let stage = 1;
  let running = false;
  let globalSpeedOffset = 0; // increases after every 5-stage loop
  let lastTimestamp = 0;

  // Player paddle
  const paddle = {
    w: 120, h: 14,
    x: canvas.width/2 - 60,
    y: canvas.height - 40,
    speed: 12,
    baseW: 120,
    enlargedUntil: 0,
  };

  // Hole state (bottom open by default)
  let holeBlockedUntil = 0;

  // Balls: supports multiple balls for power-up
  let balls = [];

  // Bricks: array of bricks per stage
  let bricks = [];

  // Powerups falling
  let powerups = []; // {x,y,type,vy, taken=false}

  // Types: 0 = enlarge paddle, 1 = multi-ball, 2 = block hole
  const POWERUP_TYPES = ['ENLARGE','MULTIBALL','BLOCK_HOLE'];

  // Input
  let mouseX = null;
  const keys = {};

  // Utility
  function randInt(a,b){ return Math.floor(Math.random()*(b-a+1))+a; }

  // Initialize
  function resetStage(s) {
    // Create brick layout depending on stage
    bricks = [];
    const rows = 6;
    const cols = 10;
    const brickW = 64;
    const brickH = 20;
    const padding = 8;
    const offsetTop = 60;
    const totalWidth = cols * (brickW + padding) - padding;
    const startX = (canvas.width - totalWidth)/2;

    // Fill grid
    for (let r=0;r<rows;r++){
      for (let c=0;c<cols;c++){
        const x = startX + c*(brickW+padding);
        const y = offsetTop + r*(brickH+padding);
        bricks.push({
          x,y,w:brickW,h:brickH,
          hp:1,
          dropsPower: false,
          color: `hsl(${(r*20 + (s-1)*40) % 360} 70% 55%)`
        });
      }
    }

    // Choose POWERUP_COUNT_PER_STAGE distinct bricks to drop powerups
    const idxs = [];
    while (idxs.length < POWERUP_COUNT_PER_STAGE) {
      const i = randInt(0, bricks.length-1);
      if (!idxs.includes(i)) idxs.push(i);
    }
    idxs.forEach(i => bricks[i].dropsPower = true);

    // Reset powerups falling
    powerups = [];
  }

  function resetBalls() {
    balls = [];
    // initial ball
    spawnBall(canvas.width/2, canvas.height-80, BASE_BALL_SPEED + globalSpeedOffset);
  }

  function spawnBall(x,y,speed) {
    // angle randomized upwards
    const angle = (Math.random() * Math.PI/2) + Math.PI*1.25; // between 225deg to 315deg (up-left/up-right)
    balls.push({
      x,y,r:8,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      speedBase: speed
    });
  }

  function startGame() {
    running = true;
    lastTimestamp = performance.now();
  }

  function restartGame() {
    lives = START_LIVES;
    score = 0;
    stage = 1;
    globalSpeedOffset = 0;
    paddle.w = paddle.baseW;
    paddle.enlargedUntil = 0;
    holeBlockedUntil = 0;
    resetStage(stage);
    resetBalls();
    updateHUD();
    startGame();
  }

  function updateHUD(){
    livesEl.textContent = lives;
    stageEl.textContent = stage;
    scoreEl.textContent = score;
    highscoreEl.textContent = highscore;
    document.getElementById('stagesTotal').textContent = STAGES_TOTAL;
  }

  // collision helpers
  function rectIntersect(ax,ay,aw,ah,bx,by,bw,bh){
    return ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by;
  }

  function update(dt) {
    // dt in ms
    const now = performance.now();

    // update paddle enlargement expiration
    if (paddle.enlargedUntil && now > paddle.enlargedUntil) {
      paddle.w = paddle.baseW;
      paddle.enlargedUntil = 0;
    }
    if (holeBlockedUntil && now > holeBlockedUntil) {
      holeBlockedUntil = 0;
    }

    // paddle motion: mouse or keys
    if (mouseX !== null) {
      paddle.x = mouseX - paddle.w/2;
    } else {
      if (keys['ArrowLeft'] || keys['a']) paddle.x -= paddle.speed;
      if (keys['ArrowRight']|| keys['d']) paddle.x += paddle.speed;
    }
    if (paddle.x < 0) paddle.x = 0;
    if (paddle.x + paddle.w > canvas.width) paddle.x = canvas.width - paddle.w;

    // update balls
    for (let bi = balls.length-1; bi >= 0; bi--) {
      const b = balls[bi];
      // keep speed in proportion to base speed + global offset
      const sp = b.speedBase + globalSpeedOffset;
      const vnorm = Math.hypot(b.vx, b.vy);
      if (vnorm > 0) {
        b.vx = (b.vx / vnorm) * sp;
        b.vy = (b.vy / vnorm) * sp;
      }

      b.x += b.vx;
      b.y += b.vy;

      // wall collisions
      // left
      if (b.x - b.r < 0) {
        b.x = b.r;
        b.vx = -b.vx;
      }
      // right
      if (b.x + b.r > canvas.width) {
        b.x = canvas.width - b.r;
        b.vx = -b.vx;
      }
      // top
      if (b.y - b.r < 0) {
        b.y = b.r;
        b.vy = -b.vy;
      }

      // paddle collision
      if (b.vy > 0) { // only check when moving downwards
        if (rectIntersect(b.x - b.r, b.y - b.r, b.r*2, b.r*2, paddle.x, paddle.y, paddle.w, paddle.h)) {
          // reflect with angle depending on hit position
          const hitPos = (b.x - (paddle.x + paddle.w/2)) / (paddle.w/2); // -1..1
          const angle = hitPos * Math.PI/3 + Math.PI * -0.5; // aim upward
          const speed = Math.hypot(b.vx, b.vy);
          b.vx = Math.cos(angle) * speed;
          b.vy = Math.sin(angle) * speed;
          b.y = paddle.y - b.r - 1;
        }
      }

      // bricks collision
      for (let i = 0; i < bricks.length; i++) {
        const br = bricks[i];
        if (!br) continue;
        if (rectIntersect(b.x - b.r, b.y - b.r, b.r*2, b.r*2, br.x, br.y, br.w, br.h)) {
          // simple collision response: determine side
          const prevX = b.x - b.vx;
          const prevY = b.y - b.vy;
          let collidedHoriz = prevY < br.y || prevY > br.y + br.h;
          // Instead do more robust: check penetration distances
          const overlapLeft = b.x + b.r - br.x;
          const overlapRight = br.x + br.w - (b.x - b.r);
          const overlapTop = b.y + b.r - br.y;
          const overlapBottom = br.y + br.h - (b.y - b.r);
          const minOverlap = Math.min(overlapLeft, overlapRight, overlapTop, overlapBottom);
          if (minOverlap === overlapLeft) {
            b.x = br.x - b.r - 1;
            b.vx = -Math.abs(b.vx);
          } else if (minOverlap === overlapRight) {
            b.x = br.x + br.w + b.r + 1;
            b.vx = Math.abs(b.vx);
          } else if (minOverlap === overlapTop) {
            b.y = br.y - b.r - 1;
            b.vy = -Math.abs(b.vy);
          } else {
            b.y = br.y + br.h + b.r + 1;
            b.vy = Math.abs(b.vy);
          }

          // brick damaged/destroyed
          br.hp -= 1;
          if (br.hp <= 0) {
            // score increment
            score += 100;
            // drop powerup if this brick had it
            if (br.dropsPower) {
              powerups.push({
                x: br.x + br.w/2,
                y: br.y + br.h/2,
                vy: 2,
                type: POWERUP_TYPES[randInt(0, POWERUP_TYPES.length-1)],
                taken: false
              });
            }
            // remove brick
            bricks.splice(i,1);
            i--; // adjust
          }
          break; // only one brick collision per update
        }
      } // end bricks loop

      // bottom (hole) check
      if (b.y - b.r > canvas.height) {
        if (!holeBlockedUntil || performance.now() > holeBlockedUntil) {
          // ball falls into hole -> remove ball
          balls.splice(bi,1);
          // if no more balls -> lose life
          if (balls.length === 0) {
            lives -= 1;
            updateHUD();
            if (lives <= 0) {
              // game over
              running = false;
              // update highscore if needed
              if (score > highscore) {
                highscore = score;
                highscoreEl.textContent = highscore;
                saveHighscore(score);
              }
              alert('ゲームオーバー！ スコア: ' + score);
            } else {
              // respawn single ball
              resetBalls();
            }
          }
        } else {
          // hole blocked: reflect as bottom wall
          b.y = canvas.height - b.r - 1;
          b.vy = -Math.abs(b.vy);
        }
      }
    } // end balls loop

    // update powerups falling
    for (let p = powerups.length - 1; p >= 0; p--) {
      const up = powerups[p];
      up.y += up.vy;
      // if collide with paddle -> apply
      if (!up.taken && rectIntersect(up.x-12, up.y-12,24,24, paddle.x, paddle.y, paddle.w, paddle.h)) {
        up.taken = true;
        applyPowerup(up.type);
        powerups.splice(p,1);
        continue;
      }
      // fallen beyond bottom -> remove
      if (up.y > canvas.height + 20) {
        powerups.splice(p,1);
      }
    }

    // check stage clear
    if (bricks.length === 0) {
      // level cleared
      // increment stage; if passes STAGES_TOTAL, reset to 1 and increase global speed
      stage++;
      if (stage > STAGES_TOTAL) {
        stage = 1;
        globalSpeedOffset += SPEED_INCREASE_PER_ROUND;
      }
      resetStage(stage);
      resetBalls();
      updateHUD();
    }

    // update HUD score (maybe changed)
    scoreEl.textContent = score;
  }

  function applyPowerup(type) {
    if (type === 'ENLARGE') {
      paddle.w = paddle.baseW * 1.6;
      paddle.enlargedUntil = performance.now() + POWERUP_DURATION;
    } else if (type === 'MULTIBALL') {
      // spawn 2 extra balls near current paddle
      for (let i=0;i<2;i++){
        spawnBall(paddle.x + paddle.w/2 + randInt(-40,40), paddle.y - 20, BASE_BALL_SPEED + globalSpeedOffset);
      }
    } else if (type === 'BLOCK_HOLE') {
      holeBlockedUntil = performance.now() + POWERUP_DURATION;
    }
  }

  // Drawing
  function draw() {
    // clear
    ctx.fillStyle = '#000';
    ctx.fillRect(0,0,canvas.width,canvas.height);

    // draw hole at bottom center (visual)
    ctx.fillStyle = (holeBlockedUntil && performance.now() < holeBlockedUntil) ? '#0a0' : '#330000';
    const holeW = 200;
    ctx.fillRect((canvas.width - holeW)/2, canvas.height - 6, holeW, 6);

    // draw bricks
    bricks.forEach(br=>{
      ctx.fillStyle = br.color;
      ctx.fillRect(br.x, br.y, br.w, br.h);
      // border
      ctx.strokeStyle = '#000';
      ctx.strokeRect(br.x, br.y, br.w, br.h);
      if (br.dropsPower) {
        // small mark to indicate special block
        ctx.fillStyle = '#fff';
        ctx.fillRect(br.x + br.w - 10, br.y + 4, 6, 6);
      }
    });

    // draw powerups
    powerups.forEach(up=>{
      ctx.fillStyle = '#ffd';
      ctx.beginPath();
      ctx.rect(up.x-12, up.y-12, 24, 24);
      ctx.fill();
      ctx.fillStyle = '#000';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(up.type === 'ENLARGE' ? 'L' : up.type === 'MULTIBALL' ? 'M' : 'B', up.x, up.y+4);
    });

    // draw paddle
    ctx.fillStyle = '#8ab4f8';
    ctx.fillRect(paddle.x, paddle.y, paddle.w, paddle.h);
    ctx.strokeStyle = '#123';
    ctx.strokeRect(paddle.x, paddle.y, paddle.w, paddle.h);

    // draw balls
    balls.forEach(b=>{
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.r, 0, Math.PI*2);
      ctx.fillStyle = '#ffc966';
      ctx.fill();
      ctx.strokeStyle = '#332200';
      ctx.stroke();
    });

    // HUD overlay text
    ctx.fillStyle = '#fff';
    ctx.font = '14px monospace';
    ctx.fillText('Score: ' + score + '   High: ' + highscore, 8, 18);
    ctx.fillText('Lives: ' + lives + '   Stage: ' + stage + '/' + STAGES_TOTAL, 8, 36);
  }

  // Main loop
  function loop(ts) {
    if (!running) return;
    const dt = ts - lastTimestamp;
    lastTimestamp = ts;
    update(dt);
    draw();
    requestAnimationFrame(loop);
  }

  // Input events
  canvas.addEventListener('mousemove', (e)=>{
    const rect = canvas.getBoundingClientRect();
    mouseX = e.clientX - rect.left;
  });
  window.addEventListener('mouseleave', ()=>{ mouseX = null; });
  window.addEventListener('keydown', (e)=>{ keys[e.key] = true; if (e.key === ' ' && !running) startGame(); });
  window.addEventListener('keyup', (e)=>{ keys[e.key] = false; });

  // Buttons
  startBtn.addEventListener('click', ()=>{
    if (!running) {
      startBtn.textContent = '停止';
      if (!balls.length) resetBalls();
      startGame();
      requestAnimationFrame(loop);
    } else {
      running = false;
      startBtn.textContent = '開始 / 再開';
    }
  });
  restartBtn.addEventListener('click', ()=>{
    if (confirm('リスタートしますか？')) {
      restartGame();
      startBtn.textContent = '停止';
      requestAnimationFrame(loop);
    }
  });

  // Save highscore to server
  function saveHighscore(scoreVal) {
    fetch(window.location.pathname + '?action=save', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({score: scoreVal})
    }).then(r => r.json()).then(j=>{
      if (j.ok && j.highscore) {
        highscore = j.highscore;
        highscoreEl.textContent = highscore;
      }
    }).catch(e=>{
      console.error('save failed', e);
    });
  }

  // Helpers
  function randInt(a,b){ return Math.floor(Math.random() * (b - a + 1)) + a; }

  // Start initial
  function init() {
    paddle.x = canvas.width/2 - paddle.w/2;
    paddle.y = canvas.height - 40;
    resetStage(stage);
    resetBalls();
    updateHUD();
    draw();
  }

  // On unload save highscore if needed
  window.addEventListener('beforeunload', ()=>{
    if (score > highscore) {
      navigator.sendBeacon(window.location.pathname + '?action=save', JSON.stringify({score:score}));
    }
  });

  init();
})();
</script>
</body>
</html>
"""
    elif args[1] == 3:
        prompt+="""
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
    elif args[1] == 4:
        prompt+="""
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
"""
    elif args[1] == 5:
        prompt+="""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Simple Platformer</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: white;
            font-family: Arial, sans-serif;
        }
        #gameContainer {
            position: relative;
        }
        canvas {
            background-color: #5c94fc; /* マリオのような青空 */
            border: 4px solid #fff;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }
        #ui {
            position: absolute;
            top: 10px;
            left: 10px;
            font-size: 20px;
            font-weight: bold;
            text-shadow: 2px 2px 0 #000;
        }
        #controls {
            margin-top: 10px;
            text-align: center;
            color: #ccc;
        }
    </style>
</head>
<body>

<div id="wrapper">
    <div id="gameContainer">
        <canvas id="gameCanvas" width="800" height="480"></canvas>
        <div id="ui">SCORE: <span id="score">0</span></div>
        
        <div id="ranking">
            <h2>ハイスコアランキング</h2>
            <ol id="highscoreList"></ol>
            <button onclick="window.location.reload()">再挑戦</button>
        </div>
        
    </div>
    <div id="controls">
        操作方法: 矢印キー(← →)で移動、スペースキーでジャンプ
    </div>
</div>

<script>
    // --- ゲーム設定 ---
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const scoreElement = document.getElementById('score');

    // 物理定数
    const GRAVITY = 0.5;
    const FRICTION = 0.8;
    const JUMP_FORCE = -10; // ジャンプ力
    const SPEED = 5;

    // ゲームの状態
    let score = 0;
    let gameOver = false;

    // キー入力管理
    const keys = {
        right: false,
        left: false,
        up: false
    };

    document.addEventListener('keydown', (e) => {
        if (e.code === 'ArrowRight') keys.right = true;
        if (e.code === 'ArrowLeft') keys.left = true;
        if (e.code === 'Space' || e.code === 'ArrowUp') keys.up = true;
    });

    document.addEventListener('keyup', (e) => {
        if (e.code === 'ArrowRight') keys.right = false;
        if (e.code === 'ArrowLeft') keys.left = false;
        if (e.code === 'Space' || e.code === 'ArrowUp') keys.up = false;
    });

    // --- クラス定義 ---

    // プレイヤー（マリオ役）
    class Player {
        constructor() {
            this.width = 32;
            this.height = 32;
            this.x = 50;
            this.y = 100;
            this.velX = 0;
            this.velY = 0;
            this.jumping = false;
            this.color = '#ff0000'; // 赤色
        }

        update() {
            // 移動処理
            if (keys.right) {
                if (this.velX < SPEED) this.velX++;
            }
            if (keys.left) {
                if (this.velX > -SPEED) this.velX--;
            }

            // 摩擦と重力
            this.velX *= FRICTION;
            this.velY += GRAVITY;

            // ジャンプ
            if (keys.up && !this.jumping) {
                this.velY = JUMP_FORCE;
                this.jumping = true;
            }

            // 位置更新
            this.x += this.velX;
            this.y += this.velY;

            // 床の当たり判定（簡易版）
            this.checkCanvasCollision();
            this.checkPlatformCollision();
        }

        draw() {
            ctx.fillStyle = this.color;
            ctx.fillRect(this.x, this.y, this.width, this.height);
            
            // 目を描いて向きを分かりやすくする
            ctx.fillStyle = 'white';
            let eyeOffset = this.velX >= 0 ? 20 : 4;
            ctx.fillRect(this.x + eyeOffset, this.y + 4, 8, 8);
        }

        checkCanvasCollision() {
            // 画面外落下（ゲームオーバー）
            if (this.y + this.height > canvas.height) {
                this.y = canvas.height - this.height;
                this.velY = 0;
                this.jumping = false;
                // 落下したらリセット
                alert("Game Over! Score: " + score);
                document.location.reload();
            }
            // 左右の壁
            if (this.x < 0) this.x = 0;
            if (this.x + this.width > canvas.width) this.x = canvas.width - this.width;
        }

        checkPlatformCollision() {
            platforms.forEach(platform => {
                // AABB衝突判定（矩形同士の重なり）
                if (
                    this.x < platform.x + platform.width &&
                    this.x + this.width > platform.x &&
                    this.y < platform.y + platform.height &&
                    this.y + this.height > platform.y
                ) {
                    // 下方向への落下中に衝突 = 着地
                    if (this.velY > 0 && this.y + this.height - this.velY <= platform.y) {
                        this.jumping = false;
                        this.velY = 0;
                        this.y = platform.y - this.height;
                    }
                    // 上方向（頭ぶつけ）
                    else if (this.velY < 0 && this.y - this.velY >= platform.y + platform.height) {
                        this.velY = 0;
                        this.y = platform.y + platform.height;
                    }
                }
            });
        }
    }

    // 地形ブロック
    class Platform {
        constructor(x, y, width, height, type) {
            this.x = x;
            this.y = y;
            this.width = width;
            this.height = height;
            this.type = type; // 1: 通常ブロック, 2: ゴール
        }

        draw() {
            if (this.type === 2) {
                ctx.fillStyle = '#FFD700'; // ゴールは金色
            } else {
                ctx.fillStyle = '#e75c10'; // 茶色のブロック
                ctx.strokeStyle = 'black';
                ctx.strokeRect(this.x, this.y, this.width, this.height);
            }
            ctx.fillRect(this.x, this.y, this.width, this.height);
            
            // 草を描画（装飾）
            if (this.type === 1) {
                ctx.fillStyle = '#00aa00';
                ctx.fillRect(this.x, this.y, this.width, 5);
            }
        }
    }

    // 敵キャラ（クリボー風）
    class Enemy {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            this.width = 32;
            this.height = 32;
            this.speed = 2;
            this.direction = 1; // 1: 右, -1: 左
            this.active = true;
        }

        update() {
            if (!this.active) return;
            this.x += this.speed * this.direction;

            // 一定距離で往復（簡易ロジック）
            // 実際は壁判定を行いますが、今回はパトロール範囲で代用
            platforms.forEach(p => {
                 if (this.x > p.x + p.width || this.x < p.x) {
                     this.direction *= -1;
                 }
            });
        }

        draw() {
            if (!this.active) return;
            ctx.fillStyle = '#8B4513'; // 茶色
            ctx.fillRect(this.x, this.y, this.width, this.height);
            
            // 怒った目
            ctx.fillStyle = 'white';
            ctx.fillRect(this.x + 5, this.y + 10, 8, 8);
            ctx.fillRect(this.x + 20, this.y + 10, 8, 8);
        }
    }

    // --- レベル生成 ---
    const player = new Player();
    const platforms = [];
    const enemies = [];

    // マップデータ (0:空, 1:ブロック, 2:ゴール, 9:敵)
    // 15行 x 25列 (32px x 32px)
    const levelMap = [
        "0000000000000000000000000",
        "0000000000000000000000000",
        "0000000000000000000000000",
        "0000000000000000000000000",
        "0000000000000111000000000",
        "0000000000000000000000002",
        "0000000000100000000000111",
        "0000000000000000000000000",
        "0000111000000000111000000",
        "0000000000000000000000000",
        "0000000009000000000000000",
        "1111111111111111110011111", // 床の穴
        "0000000000000000000000000",
        "0000000000000000000000000",
        "0000000000000000000000000"
    ];

    // マップ読み込み
    const TILE_SIZE = 32;
    for (let row = 0; row < levelMap.length; row++) {
        for (let col = 0; col < levelMap[row].length; col++) {
            const tile = levelMap[row][col];
            const x = col * TILE_SIZE;
            const y = row * TILE_SIZE;

            if (tile === '1') {
                platforms.push(new Platform(x, y, TILE_SIZE, TILE_SIZE, 1));
            } else if (tile === '2') {
                platforms.push(new Platform(x, y, TILE_SIZE, TILE_SIZE, 2));
            } else if (tile === '9') {
                enemies.push(new Enemy(x, y));
            }
        }
    }

// --- メインループ (変更あり) ---
    function gameLoop() {
        if (gameOver) return; // ゲームオーバーフラグが立ったら処理停止

        // 画面クリア
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // プレイヤー更新・描画
        player.update();
        player.draw();

        // ブロック描画
        platforms.forEach(platform => platform.draw());

        // 敵の処理
        enemies.forEach(enemy => {
            enemy.update();
            enemy.draw();

            // 敵との衝突判定
            if (enemy.active &&
                player.x < enemy.x + enemy.width &&
                player.x + player.width > enemy.x &&
                player.y < enemy.y + enemy.height &&
                player.y + player.height > enemy.y
            ) {
                // 上から踏んだら敵を倒す
                if (player.velY > 0 && player.y + player.height - player.velY <= enemy.y + 10) {
                    enemy.active = false;
                    player.velY = -5; // 小ジャンプ
                    score += 100;
                    scoreElement.innerText = score;
                } else {
                    // 横や下から当たったらゲームオーバー
                    alert("Game Over! Score: " + score);
                    document.location.reload();
                }
            }
        });

// ゴール判定 (変更: alertから showRanking へ)
        platforms.forEach(platform => {
             if (platform.type === 2 && 
                 player.x < platform.x + platform.width &&
                 player.x + player.width > platform.x &&
                 player.y < platform.y + platform.height &&
                 player.y + player.height > platform.y) {
                 
                 gameOver = true; // ゲームオーバーフラグを立ててループを停止
                 showRanking(score); // ランキング表示関数を呼び出し
             }
        });

        // 画面外落下 (変更: alertから showRanking へ)
        if (player.y + player.height > canvas.height) {
            gameOver = true;
            showRanking(score);
        }


        if (!gameOver) {
            requestAnimationFrame(gameLoop);
        }
    }

    // ゲーム開始
    gameLoop();
</script>
</body>
</html>

---
<?php
// ファイルパス
$file_path = 'highscores.txt';
// ランキングに表示する最大件数
$max_scores = 10;

// POSTデータを受け取る
$new_score = filter_input(INPUT_POST, 'score', FILTER_VALIDATE_INT);
$new_name = filter_input(INPUT_POST, 'name', FILTER_SANITIZE_STRING);

// データの検証
if (!$new_score || $new_score < 0 || !$new_name) {
    // スコアがない場合は、単にランキングを返して終了（念のため）
    echo json_encode(['ranking' => get_ranking($file_path, $max_scores)]);
    exit;
}

// スコアと名前を結合した新しいエントリー
$new_entry = ['score' => $new_score, 'name' => $new_name, 'new' => true];
$ranking = get_ranking($file_path, $max_scores);

// 新しいスコアをランキングに追加
$ranking[] = $new_entry;

// スコアの高い順にソート
usort($ranking, function($a, $b) {
    return $b['score'] <=> $a['score'];
});

// 最大件数にカット
$ranking = array_slice($ranking, 0, $max_scores);

// テキストファイルに書き込み
save_ranking($file_path, $ranking);

// PHPのレスポンスとしてJSONでランキングを返す
header('Content-Type: application/json');
echo json_encode(['ranking' => $ranking]);


/**
 * ランキングデータをファイルから読み込む関数
 * @param string $file_path
 * @param int $max_scores
 * @return array
 */
function get_ranking($file_path, $max_scores) {
    $ranking = [];
    if (file_exists($file_path)) {
        // ファイルから全行を読み込み
        $lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            // "スコア|名前" の形式でパース
            $parts = explode('|', $line);
            if (count($parts) === 2) {
                $ranking[] = [
                    'score' => (int)$parts[0],
                    'name' => $parts[1],
                    'new' => false // ファイルから読み込んだものは新規ではない
                ];
            }
        }
        // スコアの高い順にソートし、最大件数にカット
        usort($ranking, function($a, $b) {
            return $b['score'] <=> $a['score'];
        });
        return array_slice($ranking, 0, $max_scores);
    }
    return $ranking;
}

/**
 * ランキングデータをファイルに書き込む関数
 * @param string $file_path
 * @param array $ranking
 * @return void
 */
function save_ranking($file_path, $ranking) {
    $data_to_write = [];
    foreach ($ranking as $item) {
        // "スコア|名前" の形式で保存
        $data_to_write[] = "{$item['score']}|{$item['name']}";
    }
    // ファイルに書き込み (上書き)
    file_put_contents($file_path, implode("\n", $data_to_write), LOCK_EX);
}
?>
"""
    elif args[1] == 6:
        prompt+="""
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

---
<?php
// maze_data.php
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
    // 必要なら他の迷路を追加
];

---
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

---
/* style.css */
body {
  font-family: "Segoe UI", Roboto, "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
  background: #f5f7fa;
  color: #222;
  padding: 20px;
}
.container {
  max-width: 900px;
  margin: 0 auto;
}
.controls {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}
.controls button {
  padding: 8px 12px;
  font-size: 16px;
  border-radius: 6px;
  border: 1px solid #ccc;
  cursor: pointer;
}
#status {
  margin-bottom: 12px;
  display: flex;
  gap: 24px;
  align-items: center;
}

.grid {
  display: grid;
  gap: 2px;
  background: #333;
  padding: 4px;
  width: max-content;
}
.cell {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  position: relative;
  background: #fff;
}
.wall {
  background: #222;
}
.player {
  width: 22px;
  height: 22px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  background: #ffeb3b;
}
.goal {
  background: #b2ff59;
  font-weight: bold;
}
.message {
  margin-top: 12px;
  padding: 8px;
  border-radius: 6px;
}
.message.error {
  background: #ffdede;
  color: #900;
}
"""
    elif args[1] == 7:
        prompt+="""
<?php
// A single-file PHP memo app using session for storage
session_start();
if (!isset($_SESSION['memos'])) {
    $_SESSION['memos'] = [];
}

// Save new or updated memo
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    if ($_POST['action'] === 'save') {
        $id = $_POST['id'] !== '' ? intval($_POST['id']) : time();
        $_SESSION['memos'][$id] = [
            'title' => $_POST['title'],
            'body'  => $_POST['body']
        ];
        exit(json_encode(['status' => 'ok']));
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>PHP Memo App</title>
<style>
body { font-family: sans-serif; margin:0; padding:0; }
#header { padding: 10px; background:#f5f5f5; display:flex; justify-content:flex-end; }
#memoList { padding: 20px; }
.memo { border:1px solid #ccc; padding:10px; margin-bottom:10px; cursor:pointer; }
.memo-title { font-weight: bold; display:flex; justify-content:space-between; align-items:center; }
.memo-body { display:none; margin-top:10px; white-space:pre-wrap; }
#overlay {
    position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.4);
    display:none; justify-content:center; align-items:center;
}
#editor {
    background:white; width:400px; padding:20px; border-radius:8px; position:relative;
}
#editor textarea { width:100%; height:200px; }
#editor button { padding:8px 12px; margin:5px; }
#cancelBtn { position:absolute; left:10px; bottom:10px; }
#saveBtn { position:absolute; right:10px; bottom:10px; }
</style>
</head>
<body>
<div id="header">
    <button onclick="openEditor()">メモ作成</button>
</div>
<div id="memoList">
<?php foreach ($_SESSION['memos'] as $id => $m): ?>
    <div class="memo" onclick="toggleMemo(<?= $id ?>)">
        <div class="memo-title">
            <span><?= htmlspecialchars($m['title']) ?></span>
            <button onclick="event.stopPropagation(); editMemo(<?= $id ?>)">✏️</button>
        </div>
        <div class="memo-body" id="body-<?= $id ?>"><?= nl2br(htmlspecialchars($m['body'])) ?></div>
    </div>
<?php endforeach; ?>
</div>

<div id="overlay">
  <div id="editor">
    <input type="hidden" id="memoId">
    <label>タイトル(必須):</label><br>
    <input id="titleInput" type="text" maxlength="100" style="width:100%"><br><br>
    <label>内容(最大1000文字):</label><br>
    <textarea id="bodyInput" maxlength="1000"></textarea>
    <button id="cancelBtn" onclick="closeEditor()">キャンセル</button>
    <button id="saveBtn" disabled onclick="saveMemo()">完了</button>
  </div>
</div>

<script>
function toggleMemo(id){
    const b = document.getElementById('body-' + id);
    b.style.display = (b.style.display === 'block') ? 'none' : 'block';
}
function openEditor(){
    document.getElementById('memoId').value = '';
    document.getElementById('titleInput').value='';
    document.getElementById('bodyInput').value='';
    checkValid();
    document.getElementById('overlay').style.display='flex';
}
function editMemo(id){
    const title = document.querySelector(`[onclick="toggleMemo(${id})"] .memo-title span`).textContent;
    const body = document.querySelector(`#body-${id}`).textContent;
    document.getElementById('memoId').value = id;
    document.getElementById('titleInput').value = title;
    document.getElementById('bodyInput').value = body;
    checkValid();
    document.getElementById('overlay').style.display='flex';
}
function closeEditor(){
    document.getElementById('overlay').style.display='none';
}
function checkValid(){
    const t = document.getElementById('titleInput').value.trim();
    const s = document.getElementById('saveBtn');
    s.disabled = (t.length === 0);
}
document.getElementById('titleInput').addEventListener('input', checkValid);
function saveMemo(){
    const id = document.getElementById('memoId').value;
    const title = document.getElementById('titleInput').value;
    const body = document.getElementById('bodyInput').value;
    const formData = new FormData();
    formData.append('action','save');
    formData.append('id',id);
    formData.append('title',title);
    formData.append('body',body);
    fetch('',{method:'POST',body:formData})
        .then(r=>r.json())
        .then(()=>location.reload());
}
</script>
</body>
</html>
"""
    elif args[1] == 8:
        prompt+="""
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
"""
    elif args[1] == 9:
        prompt+="""
<?php
// php_pacman.php
// 単一ファイルで動作するシンプルなPac-Man風ゲーム
// 配置: サーバのドキュメントルートに置くか、ローカルで
// php -S localhost:8000
// を実行してブラウザで http://localhost:8000/php_pacman.php にアクセスしてください
?>

<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>PHP Pac-Man (single file)</title>
  <style>
    body { background:#000; color:#fff; font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Hiragino Kaku Gothic ProN", "Meiryo", sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }
    #game { box-shadow: 0 8px 30px rgba(0,0,0,0.8); background:#000; }
    #hud { text-align:center; margin-top:10px; }
    .small { font-size:0.9rem; color:#ccc }
    footer { position:fixed; bottom:6px; left:6px; font-size:12px; color:#999 }
    button { margin:0 6px }
  </style>
</head>
<body>
  <div>
    <canvas id="game" width="560" height="620"></canvas>
    <div id="hud">
      <div>Score: <span id="score">0</span> &nbsp; Lives: <span id="lives">3</span></div>
      <div class="small">操作: 矢印キー / WASD。パワー玉を取ると一定時間ゴーストが弱くなります。</div>
      <div style="margin-top:8px;"><button id="restart">Restart</button></div>
    </div>
  </div>
  <footer>PHP single-file Pac-Man — simple implementation for learning</footer>

<script>
// シンプルなグリッド型Pac-Man
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const tileSize = 20;
const cols = 28; // 幅
const rows = 31; // 高さ
const map = [
// 28 columns per row, 31 rows (classic-ish but simplified)
// 0 = empty / path, 1 = wall, 2 = dot, 3 = power pellet
// We'll define layout as simplified map using a short representation
];

// generate a simple maze by loading a predefined layout string
const layout = `
1111111111111111111111111111
1000000000000000000000000001
1011111111111011111111111101
1000000310000000000013000001
1111101010111111111010101111
1000001010000000000010100001
1011111000111011111010111101
1000000010000010001000000001
1011101010111110101111011101
1000001000000010100001000001
1011101111011010111101011101
1000001000000000000001000001
1110111011111110110111110111
1000001000000010000001000001
1011101110111310111101011101
1003001000000010000101003001
1011101011111111110001011101
1000001000000000000101000001
1110111110111110111101110111
1000001000000010000101000001
1011101011111011101101011101
1000001000000000000001000001
1011101111101111101101011101
1000000000100000000100000001
1011111010111101110001111101
1000001010000000000101000001
1111101010111111110101011111
1000000310000000000130000001
1011111111111101111111111101
1000000000000000000000000001
1111111111111111111111111111
`;

// parse layout into map array (repeated vertically to reach rows if needed)
(function parseLayout(){
  const lines = layout.trim().split('\n');
  for (let r=0;r<rows;r++){
    const line = lines[r % lines.length];
    for (let c=0;c<cols;c++){
      const ch = line[c] || '1';
      const v = Number(ch);
      if (v===0) map.push(2); // path with dot
      else if (v===3) map.push(3);
      else map.push(1);
    }
  }
})();

function idx(x,y){ return y*cols + x; }

let score = 0;
let lives = 3;
let gameOver = false;

const pacman = {
  x:14, y:23, // starting tile
  dir: {x:0,y:0},
  nextDir: {x:0,y:0},
  speed: 5, // pixels per tick
  px:14*tileSize, py:23*tileSize,
  size: tileSize-2
};

class Ghost {
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.px = x * tileSize;
    this.py = y * tileSize;
    this.dir = { x: 0, y: 0 };
    this.color = color;
    this.scared = false;
    this.home = { x, y };
    this.speed = 2;
  }

  canMove(x, y) {
    if (x < 0 || x >= cols || y < 0 || y >= rows) return false;
    return map[idx(x, y)] !== 1;
  }

  chooseDirection() {
    const dirs = [
      { x: 1, y: 0 },
      { x: -1, y: 0 },
      { x: 0, y: 1 },
      { x: 0, y: -1 }
    ];

    const possible = [];

    for (const d of dirs) {
      const nx = this.x + d.x;
      const ny = this.y + d.y;
      if (this.canMove(nx, ny)) possible.push(d);
    }

    if (possible.length > 0) {
      this.dir = possible[Math.floor(Math.random() * possible.length)];
    }
  }

  update() {
    // ★ ピクセル位置が完全にタイル中央のときだけ方向を更新 ★
    if (this.px % tileSize === 0 && this.py % tileSize === 0) {
      this.x = this.px / tileSize;
      this.y = this.py / tileSize;

      // 今の方向が壁なら強制的に選び直し
      const nx = this.x + this.dir.x;
      const ny = this.y + this.dir.y;
      if (!this.canMove(nx, ny)) {
        this.chooseDirection();
      } else {
        // 十字路ならランダムで曲がる
        const countOpen =
          (this.canMove(this.x + 1, this.y) ? 1 : 0) +
          (this.canMove(this.x - 1, this.y) ? 1 : 0) +
          (this.canMove(this.x, this.y + 1) ? 1 : 0) +
          (this.canMove(this.x, this.y - 1) ? 1 : 0);

        // 三叉路 / 十字路
        if (countOpen >= 3) {
          this.chooseDirection();
        }
      }
    }

    // ★ 進む前に「次タイルが壁かどうか」もう一度確認（壁侵入完全防止）★
    const nextX = (this.px + this.dir.x * this.speed) / tileSize;
    const nextY = (this.py + this.dir.y * this.speed) / tileSize;

    if (this.canMove(Math.round(nextX), Math.round(nextY))) {
      this.px += this.dir.x * this.speed;
      this.py += this.dir.y * this.speed;
    } else {
      // 万が一ぶつかりそうならその場で方向転換
      this.chooseDirection();
    }
  }
}



const ghosts = [
  new Ghost(13,11,'red'),
  new Ghost(14,11,'pink'),
  new Ghost(15,11,'cyan')
];

// input
const keys = {};
window.addEventListener('keydown', e=>{ keys[e.key]=true; handleKey(e.key); });
window.addEventListener('keyup', e=>{ keys[e.key]=false; });

function handleKey(k){
  if(k==='ArrowLeft' || k==='a' || k==='A') pacman.nextDir={x:-1,y:0};
  if(k==='ArrowRight' || k==='d' || k==='D') pacman.nextDir={x:1,y:0};
  if(k==='ArrowUp' || k==='w' || k==='W') pacman.nextDir={x:0,y:-1};
  if(k==='ArrowDown' || k==='s' || k==='S') pacman.nextDir={x:0,y:1};
}

function canMoveTile(x,y){
  if(x<0||x>=cols||y<0||y>=rows) return false;
  return map[idx(x,y)]!==1;
}

function updatePacman(){
  // when aligned to tile, try to change direction
  if(pacman.px % tileSize ===0 && pacman.py % tileSize===0){
    const tx = pacman.px/tileSize, ty = pacman.py/tileSize;
    // try nextDir first
    if(canMoveTile(tx+pacman.nextDir.x, ty+pacman.nextDir.y)){
      pacman.dir = pacman.nextDir;
    } else if(!canMoveTile(tx+pacman.dir.x, ty+pacman.dir.y)){
      pacman.dir = {x:0,y:0};
    }
    // consume dot
    if(map[idx(tx,ty)]===2){ map[idx(tx,ty)]=0; score+=10; }
    if(map[idx(tx,ty)]===3){ map[idx(tx,ty)]=0; score+=50; ghosts.forEach(g=>g.scared=true); setTimeout(()=>ghosts.forEach(g=>g.scared=false),8000); }
  }
  pacman.px += pacman.dir.x * 2; pacman.py += pacman.dir.y * 2;
}

function checkCollisions(){
  for(const g of ghosts){
    if(Math.abs(g.px - pacman.px) < tileSize/2 && Math.abs(g.py - pacman.py) < tileSize/2){
      if(g.scared){
        // eat ghost
        score += 200;
        g.px = g.home.x*tileSize; g.py = g.home.y*tileSize; g.scared=false;
      } else {
        // pacman dies
        lives--;
        document.getElementById('lives').textContent = lives;
        if(lives<=0){ gameOver=true; }
        resetPositions();
      }
    }
  }
}

function resetPositions(){
  pacman.px = 14*tileSize; pacman.py = 23*tileSize; pacman.dir={x:0,y:0}; pacman.nextDir={x:0,y:0};
  ghosts.forEach((g,i)=>{ g.px = g.home.x*tileSize; g.py = g.home.y*tileSize; g.dir={x:0,y:0}; });
}

function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  // background
  ctx.fillStyle = '#000'; ctx.fillRect(0,0,canvas.width,canvas.height);

  // draw map
  for(let y=0;y<rows;y++){
    for(let x=0;x<cols;x++){
      const v = map[idx(x,y)];
      const px = x*tileSize, py = y*tileSize;
      if(v===1){ // wall
        ctx.fillStyle = '#0000FF';
        ctx.fillRect(px,py,tileSize,tileSize);
        // inner cutout for nicer look
        ctx.clearRect(px+3,py+3,tileSize-6,tileSize-6);
      } else {
        // dots
        if(v===2){ ctx.fillStyle='#FFD'; ctx.beginPath(); ctx.arc(px+tileSize/2,py+tileSize/2,2,0,Math.PI*2); ctx.fill(); }
        if(v===3){ ctx.fillStyle='#FFD'; ctx.beginPath(); ctx.arc(px+tileSize/2,py+tileSize/2,6,0,Math.PI*2); ctx.fill(); }
      }
    }
  }

  // draw pacman
  const ang = 0.25*Math.PI;
  const cx = pacman.px + tileSize/2, cy = pacman.py + tileSize/2;
  ctx.fillStyle = '#FFE700';
  ctx.beginPath();
  let mouth = Math.abs(Math.sin(Date.now()/120))*ang;
  let dir = pacman.dir.x!==0 || pacman.dir.y!==0 ? pacman.dir : pacman.nextDir;
  let rot = 0;
  if(dir.x===1) rot = 0;
  if(dir.x===-1) rot = Math.PI;
  if(dir.y===1) rot = Math.PI/2;
  if(dir.y===-1) rot = -Math.PI/2;
  ctx.moveTo(cx,cy);
  ctx.arc(cx,cy,tileSize/2,rot+mouth,rot+2*Math.PI-mouth);
  ctx.fill();

  // draw ghosts
  for(const g of ghosts){
    const gx = g.px, gy = g.py;
    ctx.save();
    ctx.translate(gx+tileSize/2, gy+tileSize/2);
    // body
    ctx.beginPath();
    ctx.fillStyle = g.scared ? '#88A' : g.color;
    ctx.arc(0,0,tileSize/2,Math.PI,2*Math.PI);
    ctx.lineTo(tileSize/2, tileSize/2);
    ctx.lineTo(-tileSize/2, tileSize/2);
    ctx.closePath();
    ctx.fill();
    // eyes
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(-6, -2, 4,0,Math.PI*2); ctx.arc(6,-2,4,0,Math.PI*2); ctx.fill();
    ctx.fillStyle = '#000'; ctx.beginPath(); ctx.arc(-6 + (g.dir.x*2), -2 + (g.dir.y*2), 2,0,Math.PI*2); ctx.arc(6 + (g.dir.x*2), -2 + (g.dir.y*2), 2,0,Math.PI*2); ctx.fill();
    ctx.restore();
  }

  // HUD
  document.getElementById('score').textContent = score;
}

let lastTime = 0;
function loop(t){
  if(gameOver){
    ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = '#fff'; ctx.font='36px sans-serif'; ctx.textAlign='center'; ctx.fillText('GAME OVER', canvas.width/2, canvas.height/2 - 10);
    ctx.font='18px sans-serif'; ctx.fillText('Restart ボタンで再開', canvas.width/2, canvas.height/2 + 20);
    return;
  }
  const dt = t - lastTime; lastTime = t;
  // update multiple times depending on dt
  updatePacman();
  ghosts.forEach(g=>g.update());
  checkCollisions();
  draw();
  // win condition: no dots left
  if(!map.includes(2) && !map.includes(3)){
    ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = '#fff'; ctx.font='28px sans-serif'; ctx.textAlign='center'; ctx.fillText('YOU WIN!', canvas.width/2, canvas.height/2);
    return;
  }
  requestAnimationFrame(loop);
}

// small AI behavior: occasionally change ghost direction
setInterval(()=>{ ghosts.forEach(g=>{ if(Math.random()<0.4) g.moveRandom(); }); }, 600);

// start
resetPositions();
requestAnimationFrame(loop);

// restart button
document.getElementById('restart').addEventListener('click', ()=>{
  // reset map dots
  for(let i=0;i<map.length;i++){ if(map[i]===0) map[i]=2; }
  // reinsert power pellets at corners
  const corners = [idx(1,1), idx(cols-2,1), idx(1,rows-2), idx(cols-2,rows-2)];
  corners.forEach(c=>map[c]=3);
  score=0; lives=3; gameOver=false; document.getElementById('lives').textContent = lives; resetPositions(); requestAnimationFrame(loop);
});

</script>
</body>
</html>
"""
    else:
        prompt+="""
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

---
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

---
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

---
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

---
/* style.css */
body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }
h1, h2 { color: #333; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
.btn { padding: 10px 20px; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; display: inline-block; }
.btn-primary { background-color: #007bff; color: white; }
.btn-secondary { background-color: #6c757d; color: white; margin-left: 10px; }
.btn-vote { background-color: #28a745; color: white; width: 100%; margin-top: 5px; padding: 15px; font-size: 16px; }
.card { background: white; border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
.card:hover { box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.poll-link { text-decoration: none; color: inherit; display: block; }
.meta { font-size: 0.85em; color: #666; margin-top: 5px; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
.form-control { width: 100%; padding: 10px; box-sizing: border-box; }
.result-bar-bg { background: #e9ecef; border-radius: 5px; height: 25px; margin-top: 5px; position: relative; }
.result-bar-fill { background-color: #007bff; height: 100%; border-radius: 5px; transition: width 0.3s; }
.result-text { position: absolute; left: 10px; top: 2px; font-size: 0.9em; color: #000; font-weight: bold;}
.add-option { margin-top: 5px; font-size: 0.9em; color: #007bff; cursor: pointer; text-decoration: underline; }
"""
    run_qwen(prompt)
