
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === 'panel-' + tabId);
  });
  window.location.hash = tabId;
}

function selectScenario(serviceKey, scenarioId) {
  switchTab(serviceKey);
  const servicePanel = document.getElementById('panel-' + serviceKey);
  if (!servicePanel) return;

  servicePanel.querySelectorAll('.scenario-nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.scenario === scenarioId);
  });
  servicePanel.querySelectorAll('.scenario-view').forEach(view => {
    view.classList.toggle('active', view.id === 'view-' + scenarioId);
  });

  window.location.hash = serviceKey + '/' + scenarioId;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function activateStep(scenarioId, n) {
  const view = document.getElementById('view-' + scenarioId);
  if (!view) return;

  const box = view.querySelector('.flow-box[data-step="' + n + '"]');
  const isAlreadyActive = box && box.classList.contains('active');

  view.querySelectorAll('.flow-box').forEach(b => b.classList.remove('active'));
  view.querySelectorAll('details.task-card').forEach(c => c.classList.remove('highlighted'));

  if (isAlreadyActive) return;

  if (box) box.classList.add('active');

  view.querySelectorAll('details.task-card').forEach(card => {
    const s = card.dataset.step;
    if (s === 'all' || s === String(n) || s === (n < 10 ? '0' + n : String(n))) {
      card.classList.add('highlighted');
    }
  });

  const target = view.querySelector('details.task-card[data-step="' + n + '"], details.task-card[data-step="' + (n < 10 ? '0' + n : n) + '"]');
  if (target) {
    target.open = true;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

function activateFn(el, taskIds, scenarioId) {
  const view = document.getElementById('view-' + scenarioId) || el.closest('.scenario-view');
  if (!view) return;

  const isAlreadyActive = el.classList.contains('fn-active');
  view.querySelectorAll('.fn-node').forEach(n => n.classList.remove('fn-active'));
  view.querySelectorAll('details.task-card').forEach(c => c.classList.remove('highlighted'));

  if (isAlreadyActive) return;

  el.classList.add('fn-active');
  taskIds.forEach(id => {
    view.querySelectorAll('.task-id').forEach(tid => {
      if (tid.textContent.trim() === id) {
        const card = tid.closest('details.task-card');
        if (card) {
          card.classList.add('highlighted');
          card.open = true;
        }
      }
    });
  });

  const first = view.querySelector('details.task-card.highlighted');
  if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function toggleAllTasks(scenarioId, expand) {
  const view = document.getElementById('view-' + scenarioId);
  if (!view) return;
  view.querySelectorAll('details.task-card').forEach(card => {
    card.open = expand;
  });
}

function filterScenarios(query) {
  const q = query.toLowerCase().trim();
  document.querySelectorAll('.matrix-row').forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
  document.querySelectorAll('.scenario-nav-item').forEach(item => {
    const text = item.textContent.toLowerCase();
    item.style.display = text.includes(q) ? '' : 'none';
  });
}

window.addEventListener('DOMContentLoaded', () => {
  const hash = window.location.hash.replace('#', '');
  if (hash) {
    if (hash.includes('/')) {
      const parts = hash.split('/');
      selectScenario(parts[0], parts[1]);
    } else {
      switchTab(hash);
    }
  }
});
