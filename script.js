const cards    = Array.from(document.querySelectorAll('.art-card'));
const lb       = document.getElementById('lightbox');
const lbImg    = document.getElementById('lb-img');
const lbTitle  = document.getElementById('lb-title');
const lbDesc   = document.getElementById('lb-desc');
const lbClose  = document.getElementById('lb-close');
const lbPrev   = document.getElementById('lb-prev');
const lbNext   = document.getElementById('lb-next');
const lbLike   = document.getElementById('lb-like');
const lbLabel  = document.getElementById('lb-like-label');

let current = 0;
const liked = new Set(JSON.parse(localStorage.getItem('liked') || '[]'));

function saveLikes() {
  localStorage.setItem('liked', JSON.stringify([...liked]));
}

function updateLikeBtn() {
  const isLiked = liked.has(current);
  lbLike.classList.toggle('liked', isLiked);
  lbLabel.textContent = isLiked ? 'Liked' : 'Like';
}

function show(i) {
  current = (i + cards.length) % cards.length;
  const card = cards[current];
  const img  = card.querySelector('img');
  lbImg.src  = img.src;
  lbImg.alt  = img.alt;
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
  document.body.style.overflow = '';
}

lbLike.addEventListener('click', () => {
  if (liked.has(current)) {
    liked.delete(current);
  } else {
    liked.add(current);
  }
  saveLikes();
  updateLikeBtn();
});

cards.forEach((card, i) => card.addEventListener('click', () => open(i)));
lbClose.addEventListener('click', close);
lbPrev.addEventListener('click', () => show(current - 1));
lbNext.addEventListener('click', () => show(current + 1));
lb.addEventListener('click', e => { if (e.target === lb) close(); });

document.addEventListener('keydown', e => {
  if (!lb.classList.contains('open')) return;
  if (e.key === 'Escape')     close();
  if (e.key === 'ArrowLeft')  show(current - 1);
  if (e.key === 'ArrowRight') show(current + 1);
});
