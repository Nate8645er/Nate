// Gemeinsamer Fable-5-Button: Status anzeigen + echt verifizieren.
async function fableCheck() {
  try {
    const b = await (await fetch('/api/brain')).json();
    const el = document.getElementById('fable');
    if (!el) return;
    el.classList.toggle('on', b.modus === 'api');
    el.textContent = b.modus === 'api' ? '⚡ FABLE 5 AKTIV' : 'FABLE 5 AKTIVIEREN';
    el.title = b.modus === 'api' ? ('Aktiv — Modell ' + b.modell) : 'Klicken, um Fable 5 zu aktivieren';
  } catch (e) {}
}

async function fableKey() {
  const el = document.getElementById('fable');
  const b = await (await fetch('/api/brain')).json();
  if (b.modus === 'api') {
    if (el) el.textContent = '… PRÜFE';
    const v = await (await fetch('/api/brain/verify', { method: 'POST' })).json();
    if (v.ok) {
      alert('Fable 5 ist AKTIV und antwortet.\nModell: ' + v.modell +
            '\nAlle aktiven Mitarbeiter denken jetzt mit dem echten Modell.');
    } else {
      alert('Key ist gesetzt, aber der Testaufruf schlug fehl:\n' + (v.grund || 'unbekannt') +
            '\nBitte Key oder Guthaben pruefen.');
    }
    fableCheck();
    return;
  }
  const key = prompt('Anthropic API-Key eingeben (sk-ant-…).\n' +
                     'Wird nur lokal auf diesem PC gespeichert und sofort getestet:');
  if (!key) return;
  if (el) el.textContent = '… AKTIVIERE';
  const r = await fetch('/api/brain/key', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ schluessel: key.trim() })
  });
  if (r.ok) {
    const d = await r.json();
    if (d.verify && d.verify.ok) {
      alert('Fable 5 AKTIVIERT und verifiziert!\nModell: ' + d.modell +
            '\nAlle aktiven Mitarbeiter denken ab jetzt mit dem echten Modell.\n\n' +
            'Hinweis: Jeder Aufruf kostet echtes API-Guthaben.');
    } else {
      alert('Key gespeichert, aber der Testaufruf schlug fehl:\n' +
            ((d.verify && d.verify.grund) || 'unbekannt') +
            '\nDie Mitarbeiter laufen weiter im Offline-Modus, bis der Key funktioniert.');
    }
  } else {
    alert('Key wurde nicht akzeptiert (zu kurz?).');
  }
  fableCheck();
}

setInterval(fableCheck, 3000);
fableCheck();
