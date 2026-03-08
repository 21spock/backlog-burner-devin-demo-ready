function selectedIssueIds() {
  return Array.from(document.querySelectorAll('.issue-check:checked')).map((el) => Number(el.value));
}

function updateMetrics(metrics) {
  for (const [key, value] of Object.entries(metrics)) {
    const el = document.getElementById(key);
    if (el) el.textContent = String(value);
  }
}

function showMessage(message) {
  window.alert(message);
}

async function postJSON(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed');
  }
  return data;
}

async function loadHealth() {
  try {
    const response = await fetch('/api/health');
    const data = await response.json();
    const el = document.getElementById('health-status');
    if (!el) return;
    if (data.has_devin_key) {
      el.textContent = 'live Devin launch available';
      el.className = 'badge safe_autonomous';
    } else {
      el.textContent = 'demo mode only until DEVIN_API_KEY is set';
      el.className = 'badge needs_clarification';
    }
  } catch (err) {
    console.error(err);
  }
}

async function importDemoData() {
  try {
    const data = await postJSON('/api/import', { use_demo_data: true });
    updateMetrics(data.metrics);
    location.reload();
  } catch (err) {
    showMessage(err.message);
  }
}

async function runTriage() {
  try {
    const ids = selectedIssueIds();
    const data = await postJSON('/api/triage', { issue_ids: ids.length ? ids : null });
    updateMetrics(data.metrics);
    location.reload();
  } catch (err) {
    showMessage(err.message);
  }
}

async function launchDryRun() {
  try {
    const ids = selectedIssueIds();
    if (!ids.length) {
      showMessage('Select at least one issue first.');
      return;
    }
    const data = await postJSON('/api/launch', { issue_ids: ids, dry_run: true });
    updateMetrics(data.metrics);
    location.reload();
  } catch (err) {
    showMessage(err.message);
  }
}

async function launchLive() {
  try {
    const ids = selectedIssueIds();
    if (!ids.length) {
      showMessage('Select at least one issue first.');
      return;
    }
    const data = await postJSON('/api/launch', { issue_ids: ids, dry_run: false });
    updateMetrics(data.metrics);
    if (data.launched && data.launched.some((item) => item.error)) {
      const errors = data.launched.filter((item) => item.error).map((item) => item.error).join('\n\n');
      showMessage(errors);
    }
    location.reload();
  } catch (err) {
    showMessage(err.message);
  }
}

async function syncRuns() {
  try {
    const data = await postJSON('/api/sync', {});
    updateMetrics(data.metrics);
    location.reload();
  } catch (err) {
    showMessage(err.message);
  }
}

window.addEventListener('DOMContentLoaded', loadHealth);
