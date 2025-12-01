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
