/* ═══════════════════════════════════════════════════
   HealthCare RAG — Admin JS (reindex, charts)
═══════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  const reindexBtn = document.getElementById('reindexBtn');
  if (reindexBtn) {
    reindexBtn.addEventListener('click', () => {
      if (!confirm('Re-index all active documents? This may take a few seconds.')) return;
      reindexBtn.disabled = true;
      reindexBtn.innerHTML = '<span class="spinner"></span> Indexing…';
      fetch('/documents/reindex/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() },
      })
      .then(r => r.json())
      .then(d => {
        if (d.status === 'success') {
          showToast(`✅ Indexed ${d.chunks} chunks from ${d.docs} documents!`, 'success');
          setTimeout(() => location.reload(), 1800);
        } else {
          showToast('❌ Indexing failed: ' + (d.message || 'Unknown error'), 'danger');
        }
      })
      .catch(() => showToast('❌ Network error during indexing.', 'danger'))
      .finally(() => {
        reindexBtn.disabled = false;
        reindexBtn.innerHTML = '🔄 Re-index All Documents';
      });
    });
  }
});

function getCsrf() {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? m[1] : '';
}

function showToast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `alert alert-${type}`;
  el.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;min-width:300px;box-shadow:0 8px 24px rgba(0,0,0,.15);animation:slideUp .3s ease';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// Chart.js helpers used in monitoring dashboard
function drawLineChart(id, labels, values, label = 'Queries') {
  const ctx = document.getElementById(id);
  if (!ctx || !window.Chart) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{ label, data: values, borderColor: '#0ea5e9', backgroundColor: 'rgba(14,165,233,.08)',
                   borderWidth: 2, pointRadius: 4, tension: 0.4, fill: true }],
    },
    options: { responsive: true, plugins: { legend: { display: false } },
               scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
  });
}

function drawDoughnutChart(id, labels, values) {
  const ctx = document.getElementById(id);
  if (!ctx || !window.Chart) return;
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data: values,
                   backgroundColor: ['#0ea5e9','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4'],
                   borderWidth: 2, borderColor: '#fff' }],
    },
    options: { responsive: true, cutout: '62%',
               plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } } },
  });
}
