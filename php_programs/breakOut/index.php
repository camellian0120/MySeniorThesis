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
