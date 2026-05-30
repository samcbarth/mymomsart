const cards    = Array.from(document.querySelectorAll('.art-card'));
const lb       = document.getElementById('lightbox');
const lbImg    = document.getElementById('lb-img');
const lbZoom   = document.getElementById('lb-zoom-area');
const lbTitle  = document.getElementById('lb-title');
const lbDesc   = document.getElementById('lb-desc');
const lbClose  = document.getElementById('lb-close');
const lbPrev   = document.getElementById('lb-prev');
const lbNext   = document.getElementById('lb-next');
const lbLike   = document.getElementById('lb-like');
const lbLabel  = document.getElementById('lb-like-label');

let current = 0;
const liked = new Set(JSON.parse(localStorage.getItem('liked') || '[]'));

// ── Zoom state ──────────────────────────
let scale = 1, panX = 0, panY = 0;
let isDragging = false, dragMoved = false;
let lastMX = 0, lastMY = 0;
let lastTouchDist = 0;
const MIN = 1, MAX = 5;

function applyTransform(animated) {
  lbImg.style.transition = animated ? 'transform 0.22s ease' : 'transform 0s';
  lbImg.style.transform  = `translate(${panX}px,${panY}px) scale(${scale})`;
  lbZoom.style.cursor    = scale > 1 ? (isDragging ? 'grabbing' : 'grab') : 'zoom-in';
}

function clamp() {
  const mxP = (lbImg.offsetWidth  * (scale - 1)) / 2;
  const myP = (lbImg.offsetHeight * (scale - 1)) / 2;
  panX = Math.max(-mxP, Math.min(mxP, panX));
  panY = Math.max(-myP, Math.min(myP, panY));
}

function resetZoom() {
  scale = 1; panX = 0; panY = 0;
  applyTransform(true);
}

// Click → toggle zoom
lbZoom.addEventListener('click', e => {
  if (dragMoved) return;
  if (scale > 1) { resetZoom(); return; }
  const r  = lbImg.getBoundingClientRect();
  const ox = e.clientX - r.left - r.width  / 2;
  const oy = e.clientY - r.top  - r.height / 2;
  scale = 2.5;
  panX  = -ox * (scale - 1) / scale;
  panY  = -oy * (scale - 1) / scale;
  clamp();
  applyTransform(true);
});

// Scroll wheel zoom
lbZoom.addEventListener('wheel', e => {
  e.preventDefault();
  scale = Math.max(MIN, Math.min(MAX, scale * (e.deltaY < 0 ? 1.15 : 0.87)));
  if (scale <= MIN) { scale = 1; panX = 0; panY = 0; }
  clamp();
  applyTransform(false);
}, { passive: false });

// Mouse drag
lbZoom.addEventListener('mousedown', e => {
  if (scale <= 1) return;
  isDragging = true; dragMoved = false;
  lastMX = e.clientX; lastMY = e.clientY;
  applyTransform(false);
  e.preventDefault();
});
window.addEventListener('mousemove', e => {
  if (!isDragging) return;
  const dx = e.clientX - lastMX, dy = e.clientY - lastMY;
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragMoved = true;
  panX += dx; panY += dy;
  lastMX = e.clientX; lastMY = e.clientY;
  clamp(); applyTransform(false);
});
window.addEventListener('mouseup', () => {
  if (!isDragging) return;
  isDragging = false;
  applyTransform(false);
  setTimeout(() => { dragMoved = false; }, 50);
});

// Pinch to zoom
lbZoom.addEventListener('touchstart', e => {
  if (e.touches.length === 2) { lastTouchDist = dist(e.touches); e.preventDefault(); }
}, { passive: false });
lbZoom.addEventListener('touchmove', e => {
  if (e.touches.length !== 2) return;
  e.preventDefault();
  const d = dist(e.touches);
  scale = Math.max(MIN, Math.min(MAX, scale * d / lastTouchDist));
  lastTouchDist = d;
  if (scale <= MIN) { scale = 1; panX = 0; panY = 0; }
  clamp(); applyTransform(false);
}, { passive: false });

function dist(t) {
  return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
}

// ── Likes ───────────────────────────────
function saveLikes() { localStorage.setItem('liked', JSON.stringify([...liked])); }
function updateLikeBtn() {
  const on = liked.has(current);
  lbLike.classList.toggle('liked', on);
  lbLabel.textContent = on ? 'Liked' : 'Like';
}

// ── Navigation ──────────────────────────
function show(i) {
  current = (i + cards.length) % cards.length;
  const card = cards[current];
  const img  = card.querySelector('img');

  resetZoom();

  lbImg.style.transition = 'opacity 0s';
  lbImg.style.opacity    = '0';
  lbImg.onload = () => {
    lbImg.style.transition = 'opacity 0.35s ease';
    lbImg.style.opacity    = '1';
  };
  lbImg.src = img.src.replace('/thumbs/', '/');
  lbImg.alt = img.alt;

  lbTitle.textContent = card.dataset.title || '';
  lbDesc.textContent  = card.dataset.desc  || '';
  updateLikeBtn();
}

function open(i) {
  show(i);
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function close() {
  lb.classList.remove('open');
  lbImg.src = '';
  resetZoom();
  document.body.style.overflow = '';
}

lbLike.addEventListener('click', () => {
  liked.has(current) ? liked.delete(current) : liked.add(current);
  saveLikes(); updateLikeBtn();
});

cards.forEach((c, i) => c.addEventListener('click', () => open(i)));
lbClose.addEventListener('click', close);
lbPrev.addEventListener('click',  () => show(current - 1));
lbNext.addEventListener('click',  () => show(current + 1));
lb.addEventListener('click', e => { if (e.target === lb) close(); });

document.addEventListener('keydown', e => {
  if (!lb.classList.contains('open')) return;
  if (e.key === 'Escape')     close();
  if (e.key === 'ArrowLeft')  show(current - 1);
  if (e.key === 'ArrowRight') show(current + 1);
});
