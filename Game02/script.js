const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const scoreEl = document.getElementById('score');
const bestEl = document.getElementById('best');
const livesEl = document.getElementById('lives');
const startBtn = document.getElementById('startBtn');
const pauseBtn = document.getElementById('pauseBtn');

const W = canvas.width;
const H = canvas.height;
const PLAYER_SPEED = 5;
const BULLET_SPEED = 7;
const ENEMY_SPEED = 1.5;
const STAR_COUNT = 60;

const game = {
  running: false,
  paused: false,
  score: 0,
  best: Number(localStorage.getItem('sky-best') || 0),
  lives: 3,
  lastTime: 0,
  shootCooldown: 0,
  spawnTimer: 0,
  itemTimer: 0,
  bgScroll: 0,
  stars: [],
  player: {
    x: W / 2,
    y: H - 60,
    w: 54,
    h: 38,
    speed: PLAYER_SPEED,
  },
  bullets: [],
  enemies: [],
  items: [],
  explosions: [],
  keys: { left: false, right: false, shoot: false },
  audioCtx: null,
  audioReady: false,
  focusMode: false,
  ultraReady: true,
  powerLevel: 1,
  powerTimer: 0,
};

function initStars() {
  game.stars = Array.from({ length: STAR_COUNT }, () => ({
    x: Math.random() * W,
    y: Math.random() * H,
    r: Math.random() * 2 + 1,
    speed: Math.random() * 1.5 + 0.2,
  }));
}

function initAudio() {
  if (game.audioReady) {
    if (game.audioCtx && game.audioCtx.state === 'suspended') {
      game.audioCtx.resume();
    }
    return;
  }

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return;

  game.audioCtx = new AudioCtx();
  game.audioReady = true;
}

function playTone({ freq = 440, duration = 0.08, type = 'sine', volume = 0.04, slide = 0 }) {
  if (!game.audioCtx) return;

  const oscillator = game.audioCtx.createOscillator();
  const gain = game.audioCtx.createGain();

  oscillator.type = type;
  oscillator.frequency.setValueAtTime(freq, game.audioCtx.currentTime);
  oscillator.frequency.linearRampToValueAtTime(freq + slide, game.audioCtx.currentTime + duration);

  gain.gain.setValueAtTime(volume, game.audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.0001, game.audioCtx.currentTime + duration);

  oscillator.connect(gain);
  gain.connect(game.audioCtx.destination);

  oscillator.start();
  oscillator.stop(game.audioCtx.currentTime + duration);
}

function playSound(name) {
  if (!game.audioReady) return;
  if (game.audioCtx && game.audioCtx.state === 'suspended') {
    game.audioCtx.resume();
  }

  switch (name) {
    case 'shoot':
      playTone({ freq: 520, duration: 0.06, type: 'square', volume: 0.03, slide: 80 });
      playTone({ freq: 760, duration: 0.04, type: 'triangle', volume: 0.02, slide: 40 });
      break;
    case 'hit':
      playTone({ freq: 220, duration: 0.1, type: 'sawtooth', volume: 0.05, slide: -80 });
      break;
    case 'explosion':
      playTone({ freq: 140, duration: 0.18, type: 'square', volume: 0.05, slide: -40 });
      break;
    case 'hurt':
      playTone({ freq: 180, duration: 0.14, type: 'triangle', volume: 0.04, slide: -60 });
      break;
    default:
      break;
  }
}

function resetGame() {
  game.running = true;
  game.paused = false;
  game.score = 0;
  game.lives = 3;
  game.lastTime = 0;
  game.shootCooldown = 0;
  game.spawnTimer = 0;
  game.itemTimer = 0;
  game.bgScroll = 0;
  game.bullets = [];
  game.enemies = [];
  game.items = [];
  game.explosions = [];
  game.keys.left = false;
  game.keys.right = false;
  game.keys.shoot = false;
  game.player.x = W / 2;
  game.player.y = H - 60;
  game.powerLevel = 1;
  game.powerTimer = 0;
  pauseBtn.textContent = 'Pause';
  updateHud();
}

function updateHud() {
  scoreEl.textContent = game.score;
  bestEl.textContent = game.best;
  livesEl.textContent = game.lives;
}

function createBullet(x, y) {
  return { x, y, w: 4, h: 12, vy: -BULLET_SPEED };
}

function createEnemy(x, y) {
  const types = ['apple', 'orange', 'berry', 'pear', 'lemon', 'melon'];
  const type = types[Math.floor(Math.random() * types.length)];
  const size = 28 + Math.random() * 18;

  return {
    x,
    y,
    w: size,
    h: size,
    vy: ENEMY_SPEED + Math.random() * 1.5,
    hp: 1,
    fruit: type,
  };
}

function createItem(x, y) {
  const types = ['power', 'life', 'shield'];
  return {
    x,
    y,
    w: 18,
    h: 18,
    vy: 2,
    kind: types[Math.floor(Math.random() * types.length)],
  };
}

function spawnEnemy() {
  const width = 28 + Math.random() * 18;
  const x = 20 + Math.random() * (W - width - 20);
  game.enemies.push(createEnemy(x, -30));
}

function spawnItem() {
  const x = 30 + Math.random() * (W - 60);
  game.items.push(createItem(x, -20));
}

function shoot() {
  if (!game.running || game.paused) return;

  const centerX = game.player.x;
  const leftX = centerX - 10;
  const rightX = centerX + 10;

  game.bullets.push(createBullet(leftX, game.player.y - 18));
  game.bullets.push(createBullet(rightX, game.player.y - 18));
  playSound('shoot');
}

function hitTest(a, b) {
  return (
    a.x < b.x + b.w &&
    a.x + a.w > b.x &&
    a.y < b.y + b.h &&
    a.y + a.h > b.y
  );
}

function addExplosion(x, y, color = '#ffb703') {
  game.explosions.push({
    x,
    y,
    r: 8,
    color,
    life: 22,
  });
}

function useUltraAttack() {
  if (!game.running || game.paused || !game.ultraReady) return;

  game.ultraReady = false;
  game.focusMode = true;

  const killCount = game.enemies.length;
  if (killCount > 0) {
    for (const enemy of game.enemies) {
      addExplosion(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, '#7dd3fc');
    }
    game.score += killCount * 25;
    if (game.score > game.best) {
      game.best = game.score;
      localStorage.setItem('sky-best', String(game.best));
    }
    game.enemies = [];
    playSound('explosion');
  }

  updateHud();

  setTimeout(() => {
    game.focusMode = false;
    game.ultraReady = true;
  }, 500);
}

function applyPowerUp(kind) {
  if (kind === 'life') {
    game.lives = Math.min(5, game.lives + 1);
    playSound('hit');
  } else if (kind === 'shield') {
    game.powerLevel = Math.max(game.powerLevel, 2);
    game.powerTimer = 7000;
    playSound('shoot');
  } else {
    game.powerLevel = Math.min(3, game.powerLevel + 1);
    game.powerTimer = 7000;
    playSound('shoot');
  }

  updateHud();
}

function update(delta) {
  if (!game.running || game.paused) return;

  game.bgScroll += delta * 0.12;

  for (const star of game.stars) {
    star.y += star.speed * (delta / 16.67);
    if (star.y > H) {
      star.y = -10;
      star.x = Math.random() * W;
    }
  }

  if (game.keys.left) {
    game.player.x -= game.player.speed;
  }
  if (game.keys.right) {
    game.player.x += game.player.speed;
  }
  game.player.x = Math.max(18, Math.min(W - 18, game.player.x));

  if (game.keys.shoot && game.shootCooldown <= 0) {
    const fireRate = game.powerLevel === 1 ? 150 : game.powerLevel === 2 ? 110 : 80;
    shoot();
    if (game.powerLevel >= 2) {
      const sideOffset = 18;
      const centerX = game.player.x;
      game.bullets.push(createBullet(centerX - sideOffset, game.player.y - 16));
      game.bullets.push(createBullet(centerX + sideOffset, game.player.y - 16));
    }
    game.shootCooldown = fireRate;
  }
  game.shootCooldown = Math.max(0, game.shootCooldown - delta);

  if (game.powerTimer > 0) {
    game.powerTimer -= delta;
    if (game.powerTimer <= 0) {
      game.powerLevel = 1;
    }
  }

  game.bullets.forEach((bullet) => {
    bullet.y += bullet.vy * (delta / 16.67);
  });

  game.bullets = game.bullets.filter((bullet) => bullet.y + bullet.h > 0);

  game.spawnTimer += delta;
  if (game.spawnTimer > 700) {
    spawnEnemy();
    game.spawnTimer = 0;
  }

  game.itemTimer += delta;
  if (game.itemTimer > 5000) {
    spawnItem();
    game.itemTimer = 0;
  }

  game.enemies.forEach((enemy) => {
    enemy.y += enemy.vy * (delta / 16.67);
  });

  game.items.forEach((item) => {
    item.y += item.vy * (delta / 16.67);
  });
  game.items = game.items.filter((item) => item.y < H + 30);

  for (let i = game.bullets.length - 1; i >= 0; i--) {
    const bullet = game.bullets[i];

    for (let j = game.enemies.length - 1; j >= 0; j--) {
      const enemy = game.enemies[j];
      if (hitTest(bullet, enemy)) {
        addExplosion(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, '#ff8fab');
        playSound('hit');
        game.bullets.splice(i, 1);
        game.enemies.splice(j, 1);
        game.score += 10;
        if (game.score > game.best) {
          game.best = game.score;
          localStorage.setItem('sky-best', String(game.best));
        }
        updateHud();
        break;
      }
    }
  }

  for (let i = game.items.length - 1; i >= 0; i--) {
    const item = game.items[i];
    const playerBox = {
      x: game.player.x - game.player.w / 2,
      y: game.player.y - game.player.h / 2,
      w: game.player.w,
      h: game.player.h,
    };

    if (hitTest(playerBox, item)) {
      applyPowerUp(item.kind);
      game.items.splice(i, 1);
    }
  }

  for (let i = game.enemies.length - 1; i >= 0; i--) {
    const enemy = game.enemies[i];
    if (enemy.y + enemy.h > H) {
      game.enemies.splice(i, 1);
      game.lives -= 1;
      playSound('hurt');
      if (game.lives <= 0) {
        game.running = false;
      }
      updateHud();
      continue;
    }

    if (hitTest({ x: game.player.x - game.player.w / 2, y: game.player.y - game.player.h / 2, w: game.player.w, h: game.player.h }, enemy)) {
      game.enemies.splice(i, 1);
      game.lives -= 1;
      playSound('explosion');
      addExplosion(game.player.x, game.player.y, '#ff7373');
      if (game.lives <= 0) {
        game.running = false;
      }
      updateHud();
    }
  }

  game.explosions.forEach((exp) => {
    exp.life -= 1;
    exp.r += 1.7;
  });
  game.explosions = game.explosions.filter((exp) => exp.life > 0);
}

function drawBackground() {
  ctx.fillStyle = '#071827';
  ctx.fillRect(0, 0, W, H);

  for (const star of game.stars) {
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.beginPath();
    ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = 'rgba(111, 227, 255, 0.10)';
  for (let i = 0; i < 8; i++) {
    const y = ((i * 120 + game.bgScroll) % (H + 120)) - 60;
    ctx.fillRect(0, y, W, 2);
  }
}

function drawPlayer() {
  const x = game.player.x - game.player.w / 2;
  const y = game.player.y - game.player.h / 2;

  ctx.save();

  if (game.focusMode) {
    ctx.shadowBlur = 25;
    ctx.shadowColor = '#7dd3fc';
  }

  const bodyGradient = ctx.createLinearGradient(x, y, x + game.player.w, y + game.player.h);
  bodyGradient.addColorStop(0, '#eaf7ff');
  bodyGradient.addColorStop(0.25, '#9fe3ff');
  bodyGradient.addColorStop(0.7, '#3daef4');
  bodyGradient.addColorStop(1, '#163d5b');

  ctx.fillStyle = bodyGradient;
  ctx.beginPath();
  ctx.moveTo(x + game.player.w / 2, y);
  ctx.lineTo(x + game.player.w, y + 16);
  ctx.lineTo(x + game.player.w - 10, y + 20);
  ctx.lineTo(x + game.player.w - 2, y + game.player.h - 6);
  ctx.lineTo(x + game.player.w / 2 + 8, y + game.player.h);
  ctx.lineTo(x + game.player.w / 2 - 8, y + game.player.h);
  ctx.lineTo(x + 2, y + game.player.h - 6);
  ctx.lineTo(x + 10, y + 20);
  ctx.lineTo(x, y + 16);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#d6ecff';
  ctx.beginPath();
  ctx.moveTo(x + 12, y + 9);
  ctx.lineTo(x + game.player.w / 2, y + 3);
  ctx.lineTo(x + game.player.w - 12, y + 9);
  ctx.lineTo(x + game.player.w / 2, y + 17);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#0b1620';
  ctx.fillRect(x + 20, y + 14, 5, 10);
  ctx.fillRect(x + game.player.w - 25, y + 14, 5, 10);

  ctx.fillStyle = '#f8fbff';
  ctx.fillRect(x + 11, y + 23, 9, 8);
  ctx.fillRect(x + 34, y + 23, 9, 8);

  ctx.fillStyle = '#19b9ff';
  ctx.fillRect(x + 19, y + 28, 16, 8);

  ctx.fillStyle = '#7dd3fc';
  ctx.beginPath();
  ctx.moveTo(x + 20, y + 28);
  ctx.lineTo(x + game.player.w / 2, y + 34);
  ctx.lineTo(x + game.player.w - 20, y + 28);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#17324b';
  ctx.beginPath();
  ctx.moveTo(x + 6, y + 18);
  ctx.lineTo(x - 10, y + 26);
  ctx.lineTo(x + 6, y + 26);
  ctx.closePath();
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(x + game.player.w - 6, y + 18);
  ctx.lineTo(x + game.player.w + 10, y + 26);
  ctx.lineTo(x + game.player.w - 6, y + 26);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#ffcc29';
  ctx.fillRect(x + game.player.w / 2 - 5, y + game.player.h - 2, 10, 10);

  if (game.focusMode) {
    ctx.strokeStyle = 'rgba(125, 211, 252, 0.7)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x + game.player.w / 2, y + game.player.h / 2, 38, 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.restore();
}

function drawBullets() {
  ctx.fillStyle = '#fef08a';
  for (const bullet of game.bullets) {
    ctx.fillRect(bullet.x, bullet.y, bullet.w, bullet.h);
  }
}

function drawFruit(enemy) {
  const { x, y, w, h, fruit } = enemy;
  const cx = x + w / 2;
  const cy = y + h / 2;
  const radiusX = w / 2;
  const radiusY = h / 2;

  ctx.save();

  if (fruit === 'apple') {
    ctx.fillStyle = '#ff4d6d';
    ctx.beginPath();
    ctx.ellipse(cx, cy, radiusX, radiusY, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#bf2d4a';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#5fbf5a';
    ctx.fillRect(cx - 2, y - 6, 4, 10);
    ctx.beginPath();
    ctx.arc(cx + 5, y - 10, 6, 0, Math.PI * 2);
    ctx.fill();
  } else if (fruit === 'orange') {
    ctx.fillStyle = '#ff9f1c';
    ctx.beginPath();
    ctx.ellipse(cx, cy, radiusX, radiusY, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#8b5e34';
    ctx.fillRect(cx - 2, y - 6, 4, 10);
    ctx.beginPath();
    ctx.arc(cx + 4, y - 10, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#d97706';
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i;
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + Math.cos(angle) * radiusX, cy + Math.sin(angle) * radiusY);
    }
    ctx.stroke();
  } else if (fruit === 'berry') {
    ctx.fillStyle = '#8b5cf6';
    ctx.beginPath();
    ctx.ellipse(cx, cy, radiusX, radiusY, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#4ade80';
    ctx.fillRect(cx - 2, y - 7, 4, 10);
    ctx.beginPath();
    ctx.arc(cx + 5, y - 12, 5, 0, Math.PI * 2);
    ctx.fill();
  } else if (fruit === 'pear') {
    ctx.fillStyle = '#79d70f';
    ctx.beginPath();
    ctx.moveTo(cx, y + 2);
    ctx.quadraticCurveTo(x + w, y + h * 0.1, x + w * 0.8, y + h);
    ctx.quadraticCurveTo(cx, y + h + 10, x + w * 0.2, y + h);
    ctx.quadraticCurveTo(x, y + h * 0.1, cx, y + 2);
    ctx.fill();
    ctx.fillStyle = '#4c8b2b';
    ctx.fillRect(cx - 2, y - 8, 4, 12);
  } else if (fruit === 'lemon') {
    ctx.fillStyle = '#facc15';
    ctx.beginPath();
    ctx.ellipse(cx, cy, radiusX, radiusY, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#5fbf5a';
    ctx.fillRect(cx - 2, y - 8, 4, 12);
    ctx.beginPath();
    ctx.arc(cx + 5, y - 12, 5, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.fillStyle = '#48c774';
    ctx.beginPath();
    ctx.ellipse(cx, cy, radiusX, radiusY, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#1a8f5b';
    ctx.fillRect(cx - 2, y - 7, 4, 12);
    ctx.beginPath();
    ctx.arc(cx + 5, y - 12, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#d1fae5';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = -2; i <= 2; i++) {
      const offset = i * 7;
      ctx.moveTo(x + radiusX * 0.2 + offset, y + h * 0.25);
      ctx.lineTo(x + radiusX * 0.7 + offset, y + h * 0.75);
    }
    ctx.stroke();
  }

  ctx.restore();
}

function drawEnemies() {
  for (const enemy of game.enemies) {
    drawFruit(enemy);
  }
}

function drawItems() {
  for (const item of game.items) {
    const cx = item.x + item.w / 2;
    const cy = item.y + item.h / 2;

    ctx.save();
    ctx.translate(cx, cy);

    if (item.kind === 'life') {
      ctx.fillStyle = '#34d399';
      ctx.beginPath();
      ctx.arc(0, 0, 9, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.fillRect(-2, -5, 4, 10);
      ctx.fillRect(-5, -2, 10, 4);
    } else if (item.kind === 'shield') {
      ctx.fillStyle = '#60a5fa';
      ctx.beginPath();
      ctx.moveTo(0, -10);
      ctx.lineTo(9, -2);
      ctx.lineTo(6, 10);
      ctx.lineTo(-6, 10);
      ctx.lineTo(-9, -2);
      ctx.closePath();
      ctx.fill();
    } else {
      ctx.fillStyle = '#fbbf24';
      ctx.beginPath();
      ctx.moveTo(0, -10);
      ctx.lineTo(8, -3);
      ctx.lineTo(5, 10);
      ctx.lineTo(-5, 10);
      ctx.lineTo(-8, -3);
      ctx.closePath();
      ctx.fill();
    }

    ctx.restore();
  }
}

function drawExplosions() {
  for (const exp of game.explosions) {
    ctx.beginPath();
    ctx.fillStyle = exp.color;
    ctx.globalAlpha = exp.life / 22;
    ctx.arc(exp.x, exp.y, exp.r, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }
}

function drawGameOver() {
  ctx.fillStyle = 'rgba(0,0,0,0.45)';
  ctx.fillRect(0, 0, W, H);

  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 40px Segoe UI';
  ctx.textAlign = 'center';
  ctx.fillText('Game Over', W / 2, H / 2 - 12);

  ctx.font = '20px Segoe UI';
  ctx.fillText(`Score: ${game.score}`, W / 2, H / 2 + 28);
}

function render() {
  drawBackground();
  drawBullets();
  drawEnemies();
  drawItems();
  drawPlayer();
  drawExplosions();

  if (!game.running) {
    drawGameOver();
  }
}

function tick(timestamp) {
  const delta = timestamp - game.lastTime || 16.67;
  game.lastTime = timestamp;

  update(delta);
  render();

  requestAnimationFrame(tick);
}

function handleKey(event, isPressed) {
  const key = event.key.toLowerCase();

  if (key === 'arrowleft' || key === 'a') {
    game.keys.left = isPressed;
  }
  if (key === 'arrowright' || key === 'd') {
    game.keys.right = isPressed;
  }
  if (key === ' ' || key === 'arrowup' || key === 'w') {
    if (event.key === ' ' || event.key === 'ArrowUp' || event.key === 'w') {
      event.preventDefault();
    }
    game.keys.shoot = isPressed;
    if (isPressed) {
      initAudio();
    }
  }
}

document.addEventListener('keydown', (event) => {
  if (event.key === 'p' || event.key === 'P') {
    if (game.running) {
      game.paused = !game.paused;
      pauseBtn.textContent = game.paused ? 'Resume' : 'Pause';
    }
    return;
  }

  if (event.key === 'f' || event.key === 'F') {
    event.preventDefault();
    useUltraAttack();
    return;
  }

  initAudio();
  handleKey(event, true);
});

document.addEventListener('keyup', (event) => {
  handleKey(event, false);
});

startBtn.addEventListener('click', () => {
  initAudio();
  resetGame();
  requestAnimationFrame(tick);
});

pauseBtn.addEventListener('click', () => {
  if (!game.running) return;
  game.paused = !game.paused;
  pauseBtn.textContent = game.paused ? 'Resume' : 'Pause';
});

initStars();
updateHud();
render();
