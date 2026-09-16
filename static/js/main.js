function getCsrfToken() {
  return document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=').slice(1).join('=')
    || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
}

// Small, dependency-free UI enhancements.
document.querySelectorAll('[data-toggle]').forEach(button => {
  button.addEventListener('click', async () => {
    button.disabled = true;
    try {
      const response = await fetch(button.dataset.toggle, {
        method: 'POST',
        headers: {'X-CSRFToken': getCsrfToken() || '', 'X-Requested-With': 'XMLHttpRequest'}
      });
      if (!response.ok) throw new Error('save failed');
      const data = await response.json();
      button.classList.toggle('checked', data.completed);
      button.setAttribute('aria-pressed', String(data.completed));
      const row = button.closest('.list-row');
      row?.querySelector('b')?.classList.toggle('struck', data.completed);
      if (data.progress !== undefined) {
        const badge = row?.querySelector('.badge');
        if (badge) badge.textContent = `${data.progress}%`;
      }
    } catch {
      button.disabled = false;
      button.title = 'Could not save change. Please try again.';
    }
    button.disabled = false;
  });
});

const menu = document.querySelector('.menu');
menu?.addEventListener('click', () => {
  const sidebar = document.querySelector('.sidebar');
  sidebar?.classList.toggle('open');
});

document.addEventListener('click', event => {
  const sidebar = document.querySelector('.sidebar');
  if (window.innerWidth <= 580 && sidebar?.classList.contains('open') &&
      !sidebar.contains(event.target) && !menu?.contains(event.target)) {
    sidebar.classList.remove('open');
  }
});

// Friendly delete confirmation without adding another dependency.
document.querySelectorAll('form[action*="delete"]').forEach(form => {
  form.addEventListener('submit', event => {
    if (!window.confirm('Delete this item? This cannot be undone.')) event.preventDefault();
  });
});

// Let success messages fade away naturally.
window.setTimeout(() => {
  document.querySelectorAll('.toast').forEach(toast => {
    toast.style.transition = 'opacity .35s ease, transform .35s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-6px)';
    window.setTimeout(() => toast.remove(), 400);
  });
}, 3600);

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/js/sw.js').catch(() => {});
}

document.querySelector('#ai-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const input = document.querySelector('#ai-input');
  const text = input.value.trim();
  if (!text) return;

  const button = event.target.querySelector('button');
  button.disabled = true;
  button.textContent = 'Thinking…';

  try {
    const response = await fetch('/api/ai/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() || ''},
      body: JSON.stringify({question: text})
    });
    const data = await response.json();
    const box = document.createElement('div');
    box.className = 'chat-message';
    box.innerHTML = '<b>StudyOS AI</b><p></p>';
    box.querySelector('p').textContent = data.answer || data.error || 'No response.';
    event.target.before(box);
    input.value = '';
  } catch {
    const box = document.createElement('div');
    box.className = 'chat-message';
    box.textContent = 'Could not reach StudyOS AI. Please try again.';
    event.target.before(box);
  } finally {
    button.disabled = false;
    button.textContent = 'Send';
  }
});
