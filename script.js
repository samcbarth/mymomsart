// Scroll reveal
const observer = new IntersectionObserver(
  entries => entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      observer.unobserve(e.target);
    }
  }),
  { threshold: 0.1 }
);

document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// Lightbox
const cards   = Array.from(document.querySelectorAll('.art-card'));
const lb      = document.getElementById('lightbox');
const lbImg   = document.getElementById('lb-img');
const lbClose = document.getElementById('lb-close');
const lbPrev  = document.getElementById('lb-prev');
const lbNext  = document.getElementById('lb-next');

let current = 0;

function open(i) {
  current = i;
  lbImg.src = cards[i].querySelector('img').src;
  lbImg.alt = cards[i].querySelector('img').alt;
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function close() {
  lb.classList.remove('open');
  lbImg.src = '';
  document.body.style.overflow = '';
}

function nav(dir) {
  current = (current + dir + cards.length) % cards.length;
  lbImg.src = cards[current].querySelector('img').src;
  lbImg.alt = cards[current].querySelector('img').alt;
}

cards.forEach((card, i) => card.addEventListener('click', () => open(i)));
lbClose.addEventListener('click', close);
lbPrev.addEventListener('click', () => nav(-1));
lbNext.addEventListener('click', () => nav(1));
lb.addEventListener('click', e => { if (e.target === lb) close(); });
document.addEventListener('keydown', e => {
  if (!lb.classList.contains('open')) return;
  if (e.key === 'Escape')     close();
  if (e.key === 'ArrowLeft')  nav(-1);
  if (e.key === 'ArrowRight') nav(1);
});
