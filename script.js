const cards    = Array.from(document.querySelectorAll('.art-card'));
const lightbox = document.getElementById('lightbox');
const lbImg    = document.getElementById('lb-img');
const lbClose  = document.getElementById('lb-close');
const lbPrev   = document.getElementById('lb-prev');
const lbNext   = document.getElementById('lb-next');

let current = 0;

function visibleCards() {
  return cards.filter(c => {
    const img = c.querySelector('img');
    return img && !c.querySelector('.img-wrap').classList.contains('placeholder');
  });
}

function openLightbox(index) {
  const visible = visibleCards();
  if (!visible.length) return;
  current = index;
  const img = visible[current].querySelector('img');
  lbImg.src = img.src;
  lbImg.alt = img.alt;
  lightbox.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  lightbox.classList.remove('open');
  lbImg.src = '';
  document.body.style.overflow = '';
}

function navigate(dir) {
  const visible = visibleCards();
  if (!visible.length) return;
  current = (current + dir + visible.length) % visible.length;
  const img = visible[current].querySelector('img');
  lbImg.src = img.src;
  lbImg.alt = img.alt;
}

cards.forEach((card, i) => {
  card.addEventListener('click', () => {
    const visible = visibleCards();
    const idx = visible.indexOf(card);
    if (idx !== -1) openLightbox(idx);
  });
});

lbClose.addEventListener('click', closeLightbox);
lbPrev.addEventListener('click', () => navigate(-1));
lbNext.addEventListener('click', () => navigate(1));

lightbox.addEventListener('click', e => {
  if (e.target === lightbox) closeLightbox();
});

document.addEventListener('keydown', e => {
  if (!lightbox.classList.contains('open')) return;
  if (e.key === 'Escape')      closeLightbox();
  if (e.key === 'ArrowLeft')   navigate(-1);
  if (e.key === 'ArrowRight')  navigate(1);
});
