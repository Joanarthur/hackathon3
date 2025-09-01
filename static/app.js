document.addEventListener('DOMContentLoaded', () => {
  const notes = document.getElementById('notes');
  const genBtn = document.getElementById('generate');
  const saveBtn = document.getElementById('save');
  const clearBtn = document.getElementById('clear');
  const status = document.getElementById('status');
  const cardsContainer = document.getElementById('cards');
  let lastGenerated = [];

  async function renderExisting() {
    try {
      const res = await fetch('/api/cards');
      const json = await res.json();
      const cards = json.cards || [];
      cardsContainer.innerHTML = '';
      cards.forEach(c => appendCard(c, false));
    } catch (e) {
      console.error('Failed to load existing cards:', e);
    }
  }

  function appendCard(c, temporary) {
    const wrap = document.createElement('div');
    wrap.className = 'card ' + (temporary ? 'opacity-90' : '');
    wrap.style.height = '180px';

    const inner = document.createElement('div');
    inner.className = 'card-inner';

    const front = document.createElement('div');
    front.className = 'card-face card-front';
    front.innerHTML = `<div class="text-sm font-medium mb-2">${escapeHtml(c.question)}</div>`;

    const back = document.createElement('div');
    back.className = 'card-face card-back';
    back.innerHTML = `<div class="text-sm">${escapeHtml(c.answer)}</div>`;

    inner.appendChild(front);
    inner.appendChild(back);
    wrap.appendChild(inner);

    wrap.addEventListener('click', () => wrap.classList.toggle('flipped'));

    // prepend newest
    cardsContainer.prepend(wrap);
  }

  function escapeHtml(s) {
    return (s || '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  }

  genBtn.addEventListener('click', async () => {
    const txt = notes.value.trim();
    if (!txt) { status.textContent = 'Paste some notes first.'; return; }
    genBtn.disabled = true; status.textContent = 'Generating...';
    try {
      const res = await fetch('/generate', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({notes: txt})
      });
      const data = await res.json();
      if (data.error) { status.textContent = data.error; return; }
      lastGenerated = data.qa || [];
      // show temporary cards
      lastGenerated.forEach(q => appendCard(q, true));
      status.textContent = `Generated ${lastGenerated.length} cards (click any to flip)`;
    } catch (e) {
      console.error('Generation error:', e);
      status.textContent = 'Generation failed.';
    } finally { genBtn.disabled = false; }
  });

  saveBtn.addEventListener('click', async () => {
    if (!lastGenerated.length) { status.textContent = 'No generated cards to save.'; return; }
    saveBtn.disabled = true; status.textContent = 'Saving...';
    try {
      const res = await fetch('/save', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({qa: lastGenerated})
      });
      const data = await res.json();
      if (data.saved) {
        data.saved.forEach(c => appendCard(c, false));
        status.textContent = `Saved ${data.saved.length} cards.`;
        lastGenerated = [];
      } else {
        status.textContent = 'Nothing saved.';
      }
    } catch (e) {
      console.error('Save error:', e);
      status.textContent = 'Save failed.';
    } finally { saveBtn.disabled = false; }
  });

  clearBtn.addEventListener('click', () => { notes.value=''; status.textContent=''; });

  // load existing cards on page load
  renderExisting();
});
