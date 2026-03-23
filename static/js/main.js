// STUDIO — main.js

// Progress bar animation during pipeline
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('pipelineForm');
  if (!form) return;

  form.addEventListener('submit', function () {
    const progressCard = document.getElementById('progressCard');
    const progressBar = document.getElementById('progressBar');
    const progressMsg = document.getElementById('progressMsg');
    const steps = document.querySelectorAll('.step');

    if (progressCard) progressCard.style.display = 'block';

    const messages = [
      'Generating script with Claude...',
      'Creating voiceover with ElevenLabs...',
      'Generating thumbnail with DALL-E...',
      'Finding stock footage on Pexels...',
      'Assembling video with MoviePy...',
      'Uploading to YouTube...',
    ];

    let current = 0;
    const interval = setInterval(function () {
      if (current >= messages.length) {
        clearInterval(interval);
        return;
      }
      if (progressMsg) progressMsg.textContent = messages[current];
      if (progressBar) progressBar.style.width = ((current + 1) / messages.length * 100) + '%';
      if (steps[current]) {
        steps[current].classList.remove('active');
        steps[current].classList.add('done');
      }
      current++;
      if (steps[current]) steps[current].classList.add('active');
    }, 8000); // Advance every 8 seconds
  });
});

// Auto-dismiss alerts
document.querySelectorAll('.alert').forEach(function (el) {
  setTimeout(function () {
    el.style.opacity = '0';
    el.style.transition = 'opacity 0.5s';
    setTimeout(function () { el.remove(); }, 500);
  }, 4000);
});

// One-click copy for any element with data-copy attribute
document.addEventListener('click', function (e) {
  const btn = e.target.closest('[data-copy]');
  if (!btn) return;
  const targetId = btn.getAttribute('data-copy');
  const target = targetId ? document.getElementById(targetId) : btn.previousElementSibling;
  if (!target) return;
  const text = target.value !== undefined ? target.value : target.innerText;
  navigator.clipboard.writeText(text.trim()).then(function () {
    const original = btn.textContent;
    btn.textContent = '✓ Copied!';
    btn.style.color = '#00c850';
    setTimeout(function () { btn.textContent = original; btn.style.color = ''; }, 1500);
  });
});

// Load active voice into global bar
(function() {
  const bar = document.getElementById('globalVoiceBar');
  const nameEl = document.getElementById('gvName');
  if (!bar || !nameEl) return;
  fetch('/voices/api/active')
    .then(r => r.json())
    .then(d => {
      nameEl.textContent = d.voice_name || 'Not set — click Change';
    })
    .catch(() => { nameEl.textContent = 'Not set'; });
})();
