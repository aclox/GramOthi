const CACHE_NAME = 'sd-cache-v2';
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/auth.html',
  '/src/styles.css',
  '/src/app.js',
  '/src/auth.js',
  '/src/idb.js'
];

self.addEventListener('install', (event)=>{
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache=>cache.addAll(CORE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event)=>{
  event.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k))))
  );
  self.clients.claim();
});

// Cache-first for same-origin, network-first for media (audio/video)
self.addEventListener('fetch', (event)=>{
  const url = new URL(event.request.url);
  if (url.origin === location.origin){
    event.respondWith(
      caches.match(event.request).then(cached=>cached || fetch(event.request))
    );
    return;
  }
  if (event.request.destination === 'audio' || event.request.destination === 'video'){
    event.respondWith(
      fetch(event.request).then(res=>{
        const copy = res.clone();
        caches.open(CACHE_NAME).then(c=>c.put(event.request, copy));
        return res;
      }).catch(()=>caches.match(event.request))
    );
    return;
  }
  event.respondWith(
    caches.match(event.request).then(cached=>cached || fetch(event.request))
  );
});

self.addEventListener('message', async (event)=>{
  const data = event.data;
  if (data?.type === 'PREFETCH'){
    const urls = data.payload || [];
    const cache = await caches.open(CACHE_NAME);
    for (const u of urls){
      try{
        const res = await fetch(u, { mode:'no-cors' });
        await cache.put(u, res);
        const clientsList = await self.clients.matchAll();
        clientsList.forEach(c=>c.postMessage({ type:'PREFETCH_DONE', url:u }));
      }catch(e){/* ignore */}
    }
  }
});

// Tabs navigation
const tabButtons = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
tabButtons.forEach(btn => btn.addEventListener('click', () => {
  tabButtons.forEach(b => b.classList.remove('active'));
  panels.forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  const id = btn.dataset.tab;
  document.getElementById(`tab-${id}`).classList.add('active');
}));

// PWA install prompt
let deferredPrompt;
const installBtn = document.getElementById('installBtn');
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  installBtn.hidden = false;
});
installBtn?.addEventListener('click', async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  installBtn.hidden = true;
  deferredPrompt = null;
});

// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js');
  });
}

// Minimal IndexedDB wrapper usage (see idb.js)
const db = window.dashboardDB;

// Classes
const joinForm = document.getElementById('joinClassForm');
const classList = document.getElementById('classList');
joinForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const code = document.getElementById('classCode').value.trim();
  if (!code) return;
  await db.save('classes', { id: code, joinedAt: Date.now() });
  document.getElementById('classCode').value = '';
  renderClasses();
});

async function renderClasses(){
  const classes = await db.getAll('classes');
  classList.innerHTML = '';
  classes.forEach(c => {
    const li = document.createElement('li');
    li.textContent = c.id;
    const b = document.createElement('button');
    b.className='btn-outline btn';
    b.textContent='Leave';
    b.onclick = async ()=>{await db.delete('classes', c.id); renderClasses();};
    li.appendChild(b);
    classList.appendChild(li);
  });
}
renderClasses();

// Slides demo cards
const slides = [
  { id:'s1', title:'Intro to AI', size:'240KB' },
  { id:'s2', title:'Digital Logic', size:'180KB' },
  { id:'s3', title:'Renewable Basics', size:'210KB' }
];
const slidesContainer = document.getElementById('slidesContainer');
slides.forEach(s=>{
  const card = document.createElement('div');
  card.className='card';
  card.innerHTML = `<strong>${s.title}</strong><div class="chip">${s.size}</div>`;
  slidesContainer.appendChild(card);
});

// Audio demo
const audioSamples = [
  { id:'a1', title:'Sample Lecture 1', src:'https://cdn.pixabay.com/download/audio/2021/09/02/audio_36a3b9.mp3?filename=tiny-robot-116500.mp3' }
];
const audioList = document.getElementById('audioList');
const audioPlayer = document.getElementById('audioPlayer');
const audioProgress = document.getElementById('audioProgress');
audioSamples.forEach(a=>{
  const li = document.createElement('li');
  li.innerHTML = `<span>${a.title}</span>`;
  const play = document.createElement('button');
  play.className='btn';
  play.textContent='Play';
  play.onclick = ()=>{ audioPlayer.src = a.src; audioPlayer.play(); };
  li.appendChild(play);
  audioList.appendChild(li);
});

// Visual progress for audio
audioPlayer?.addEventListener('timeupdate', ()=>{
  if (!audioPlayer.duration) return;
  const pct = Math.min(100, (audioPlayer.currentTime / audioPlayer.duration) * 100);
  audioProgress.style.width = pct + '%';
});

// Quiz demo (offline-capable)
const quizContainer = document.getElementById('quizContainer');
const quiz = {
  id:'q1',
  question:'Which one prioritizes low bandwidth?',
  options:['Audio-first streaming','4K video','Uncompressed PDFs','Live screen share'],
  answer:0
};
function renderQuiz(){
  const saved = window.localStorage.getItem('quiz-q1');
  if (saved){
    quizContainer.innerHTML = `<p>Submitted. Your answer: <strong>${quiz.options[Number(saved)]}</strong></p>`;
    return;
  }
  const html = [`<p>${quiz.question}</p>`]
    .concat(quiz.options.map((o,i)=>`<label><input name="q" type="radio" value="${i}"> ${o}</label>`))
    .join('');
  quizContainer.innerHTML = html + '<button id="submitQuiz" class="btn" style="margin-top:10px">Submit</button>';
  document.getElementById('submitQuiz').onclick = ()=>{
    const choice = document.querySelector('input[name="q"]:checked');
    if(!choice) return;
    window.localStorage.setItem('quiz-q1', choice.value);
    renderQuiz();
  };
}
renderQuiz();

// Offline downloads demo (cache prefetch)
const prefetchBtn = document.getElementById('prefetchBtn');
const downloadList = document.getElementById('downloadList');
prefetchBtn?.addEventListener('click', async ()=>{
  if (!navigator.serviceWorker?.controller){
    alert('Service worker not active yet. Try again in a moment.');
    return;
  }
  const msg = { type:'PREFETCH', payload:[
    'https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg'
  ]};
  navigator.serviceWorker.controller.postMessage(msg);
});

navigator.serviceWorker?.addEventListener('message', async (ev)=>{
  if (ev.data?.type === 'PREFETCH_DONE'){
    const url = ev.data.url;
    const li = document.createElement('li');
    li.innerHTML = `<span class="chip downloaded">Cached</span> <a href="${url}" target="_blank">Open</a>`;
    downloadList.appendChild(li);
  }
});

// Floating action button quick prefetch and toast
const fab = document.getElementById('fab');
const toast = document.getElementById('toast');
function showToast(message){
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(()=>toast.classList.remove('show'), 2200);
}
fab?.addEventListener('click', ()=>{
  prefetchBtn?.click();
  showToast('Downloading example bundle…');
});

navigator.serviceWorker?.addEventListener('message', (ev)=>{
  if (ev.data?.type === 'PREFETCH_DONE'){
    showToast('Cached: ' + (ev.data.url || 'resource'));
  }
});


