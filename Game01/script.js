const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');

const scoreEl = document.getElementById('score');
const linesEl = document.getElementById('lines');
const levelEl = document.getElementById('level');
const startBtn = document.getElementById('start-btn');
const pauseBtn = document.getElementById('pause-btn');
const resetBtn = document.getElementById('reset-btn');

const COLS = 10;
const ROWS = 20;
const BLOCK = 30;
const EMPTY = 0;

const COLORS = {
  I: '#38bdf8',
  J: '#60a5fa',
  L: '#fbbf24',
  O: '#facc15',
  S: '#4ade80',
  T: '#c084fc',
  Z: '#f87171'
};

const SHAPES = {
  I: [
    [1, 1, 1, 1]
  ],
  J: [
    [1, 0, 0],
    [1, 1, 1]
  ],
  L: [
    [0, 0, 1],
    [1, 1, 1]
  ],
  O: [
    [1, 1],
    [1, 1]
  ],
  S: [
    [0, 1, 1],
    [1, 1, 0]
  ],
  T: [
    [0, 1, 0],
    [1, 1, 1]
  ],
  Z: [
    [1, 1, 0],
    [0, 1, 1]
  ]
};

let board;
let currentPiece;
let nextPiece;
let score;
let lines;
let level;
let dropInterval;
let lastTime;
let animationId;
let isPaused = false;
let isRunning = false;

function createBoard() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(EMPTY));
}

function randomPiece() {
  const types = Object.keys(SHAPES);
  const type = types[Math.floor(Math.random() * types.length)];
  const matrix = SHAPES[type].map((row) => [...row]);
  return {
    type,
    matrix,
    x: Math.floor((COLS - matrix[0].length) / 2),
    y: -1
  };
}

function resetGame() {
  board = createBoard();
  score = 0;
  lines = 0;
  level = 1;
  currentPiece = randomPiece();
  nextPiece = randomPiece();
  isPaused = false;
  isRunning = true;
  lastTime = 0;
  dropInterval = 700;
  updateHud();
  cancelAnimationFrame(animationId);
  animationId = requestAnimationFrame(gameLoop);
}

function updateHud() {
  scoreEl.textContent = score;
  linesEl.textContent = lines;
  levelEl.textContent = level;
}

function collide(x, y, matrix) {
  for (let row = 0; row < matrix.length; row += 1) {
    for (let col = 0; col < matrix[row].length; col += 1) {
      if (!matrix[row][col]) continue;

      const newX = x + col;
      const newY = y + row;

      if (newX < 0 || newX >= COLS || newY >= ROWS) {
        return true;
      }

      if (newY >= 0 && board[newY][newX]) {
        return true;
      }
    }
  }

  return false;
}

function mergePiece() {
  currentPiece.matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (!value) return;
      const boardY = currentPiece.y + y;
      const boardX = currentPiece.x + x;
      if (boardY >= 0) {
        board[boardY][boardX] = currentPiece.type;
      }
    });
  });
}

function clearLines() {
  let cleared = 0;

  for (let y = ROWS - 1; y >= 0; y -= 1) {
    if (board[y].every((cell) => cell !== EMPTY)) {
      board.splice(y, 1);
      board.unshift(Array(COLS).fill(EMPTY));
      cleared += 1;
      y += 1;
    }
  }

  if (cleared > 0) {
    lines += cleared;
    score += [0, 100, 300, 500, 800][cleared] * level;
    level = Math.floor(lines / 10) + 1;
    dropInterval = Math.max(120, 700 - (level - 1) * 60);
    updateHud();
  }
}

function spawnPiece() {
  currentPiece = nextPiece;
  currentPiece.x = Math.floor((COLS - currentPiece.matrix[0].length) / 2);
  currentPiece.y = -1;
  nextPiece = randomPiece();

  if (collide(currentPiece.x, currentPiece.y, currentPiece.matrix)) {
    endGame();
  }
}

function endGame() {
  isRunning = false;
  cancelAnimationFrame(animationId);
  ctx.fillStyle = 'rgba(5, 10, 18, 0.7)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 28px Segoe UI';
  ctx.textAlign = 'center';
  ctx.fillText('Game Over', canvas.width / 2, canvas.height / 2 - 12);
  ctx.font = '18px Segoe UI';
  ctx.fillText('Press Reset', canvas.width / 2, canvas.height / 2 + 24);
}

function rotateMatrix(matrix) {
  const rotated = matrix[0].map((_, index) =>
    matrix.map((row) => row[index]).reverse()
  );
  return rotated;
}

function rotatePiece() {
  if (!currentPiece || !isRunning || isPaused) return;

  const rotated = rotateMatrix(currentPiece.matrix);
  const kickOffsets = [0, -1, 1, -2, 2];

  for (const offset of kickOffsets) {
    const nextX = currentPiece.x + offset;
    if (!collide(nextX, currentPiece.y, rotated)) {
      currentPiece.matrix = rotated;
      currentPiece.x = nextX;
      return;
    }
  }
}

function movePiece(dx, dy) {
  if (!currentPiece || !isRunning || isPaused) return;

  if (!collide(currentPiece.x + dx, currentPiece.y + dy, currentPiece.matrix)) {
    currentPiece.x += dx;
    currentPiece.y += dy;
    return true;
  }

  if (dy > 0) {
    mergePiece();
    clearLines();
    spawnPiece();
  }

  return false;
}

function dropPiece() {
  if (!currentPiece || !isRunning || isPaused) return;

  if (!movePiece(0, 1)) {
    return;
  }
}

function hardDrop() {
  if (!currentPiece || !isRunning || isPaused) return;

  while (!collide(currentPiece.x, currentPiece.y + 1, currentPiece.matrix)) {
    currentPiece.y += 1;
    score += 2;
  }

  mergePiece();
  clearLines();
  spawnPiece();
  updateHud();
}

function togglePause() {
  if (!isRunning) return;
  isPaused = !isPaused;
  pauseBtn.textContent = isPaused ? 'Resume' : 'Pause';
}

function drawCell(x, y, color, alpha = 1) {
  ctx.fillStyle = color;
  ctx.globalAlpha = alpha;
  ctx.fillRect(x * BLOCK, y * BLOCK, BLOCK, BLOCK);
  ctx.globalAlpha = 1;

  ctx.strokeStyle = 'rgba(255,255,255,0.15)';
  ctx.strokeRect(x * BLOCK + 0.5, y * BLOCK + 0.5, BLOCK - 1, BLOCK - 1);
}

function drawBoard() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let y = 0; y < ROWS; y += 1) {
    for (let x = 0; x < COLS; x += 1) {
      const cell = board[y][x];
      if (cell) {
        drawCell(x, y, COLORS[cell]);
      } else {
        ctx.strokeStyle = 'rgba(255,255,255,0.04)';
        ctx.strokeRect(x * BLOCK + 0.5, y * BLOCK + 0.5, BLOCK - 1, BLOCK - 1);
      }
    }
  }

  if (currentPiece) {
    currentPiece.matrix.forEach((row, y) => {
      row.forEach((value, x) => {
        if (value) {
          const drawX = currentPiece.x + x;
          const drawY = currentPiece.y + y;
          if (drawY >= 0) {
            drawCell(drawX, drawY, COLORS[currentPiece.type]);
          }
        }
      });
    });
  }
}

function gameLoop(timestamp) {
  if (!isRunning) return;

  if (!lastTime) lastTime = timestamp;

  const delta = timestamp - lastTime;

  if (!isPaused && delta >= dropInterval) {
    dropPiece();
    lastTime = timestamp;
  }

  drawBoard();
  animationId = requestAnimationFrame(gameLoop);
}

function handleKeydown(event) {
  const key = event.key;

  if (key === 'p' || key === 'P') {
    togglePause();
    return;
  }

  if (!isRunning || isPaused) return;

  switch (key) {
    case 'ArrowLeft':
      movePiece(-1, 0);
      break;
    case 'ArrowRight':
      movePiece(1, 0);
      break;
    case 'ArrowDown':
      movePiece(0, 1);
      score += 1;
      updateHud();
      break;
    case 'ArrowUp':
      rotatePiece();
      break;
    case ' ':
      event.preventDefault();
      hardDrop();
      break;
    default:
      break;
  }
}

startBtn.addEventListener('click', () => {
  resetGame();
  startBtn.textContent = 'Restart';
});

pauseBtn.addEventListener('click', () => {
  togglePause();
});

resetBtn.addEventListener('click', () => {
  resetGame();
  startBtn.textContent = 'Restart';
});

document.addEventListener('keydown', handleKeydown);

resetGame();
startBtn.textContent = 'Restart';
