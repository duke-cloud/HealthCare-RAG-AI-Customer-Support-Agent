/* =================================================================
   HealthCare RAG — Chat Interface
   Handles: AJAX messaging, typing indicator, SSE real-time updates,
            suggestion chips, feedback buttons, auto-resize textarea
   ================================================================= */

'use strict';

/* ── CSRF helper ─────────────────────────────────────────────── */
function getCsrf() {
  const cookie = document.cookie.match(/csrftoken=([^;]+)/);
  if (cookie) return cookie[1];
  const meta = document.querySelector('[name=csrfmiddlewaretoken]');
  return meta ? meta.value : '';
}

/* ── POST JSON helper ────────────────────────────────────────── */
function postJSON(url, data) {
  return fetch(url, {
    method:  'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken':  getCsrf(),
    },
    body: JSON.stringify(data),
  });
}

/* ── Escape HTML to prevent XSS ─────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Light markdown → HTML (bold, line-breaks, source chips) ── */
function formatAnswer(text) {
  return escHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\[Source:\s*([^\]]+)\]/g,
      '<span class="source-chip">$1</span>')
    .replace(/\n/g, '<br>');
}

/* ── Scroll chat box to bottom ───────────────────────────────── */
function scrollBottom(el) {
  if (el) requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });
}

/* ================================================================
   Main initialisation — runs after DOM ready
   ================================================================ */
document.addEventListener('DOMContentLoaded', function () {

  const msgBox    = document.getElementById('chatMessages');
  const input     = document.getElementById('chatInput');
  const sendBtn   = document.getElementById('sendBtn');
  const sessionEl = document.getElementById('sessionPk');

  /* Nothing to do if we are not on the chat page */
  if (!msgBox || !input || !sendBtn || !sessionEl) return;

  const sessionPk = sessionEl.value;
  if (!sessionPk) {
    console.error('ChatJS: sessionPk is empty — cannot send messages');
    return;
  }

  const ASK_URL = `/chat/session/${sessionPk}/ask/`;

  /* Scroll to bottom on load */
  scrollBottom(msgBox);

  /* ── Auto-resize textarea ─────────────────────────────────── */
  input.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 160) + 'px';
  });

  /* ── Enter = send, Shift+Enter = new line ─────────────────── */
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);

  /* ── Suggestion chips ─────────────────────────────────────── */
  document.querySelectorAll('.suggestion-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      input.value = this.dataset.q || this.textContent.trim();
      input.dispatchEvent(new Event('input'));   // trigger auto-resize
      input.focus();
    });
  });

  /* ================================================================
     SEND MESSAGE
     ================================================================ */
  function sendMessage() {
    const question = input.value.trim();
    if (!question) return;
    if (sendBtn.disabled) return;

    /* Render user bubble immediately */
    appendUserBubble(question);
    input.value = '';
    input.style.height = '44px';
    setLoading(true);

    const typingEl = appendTyping();

    postJSON(ASK_URL, { question })
      .then(res => {
        if (!res.ok) {
          return res.json().then(err => Promise.reject(err));
        }
        return res.json();
      })
      .then(data => {
        typingEl.remove();
        appendAIBubble(data);
      })
      .catch(err => {
        typingEl.remove();
        const msg = err?.error || 'Connection error — please try again.';
        appendAIBubble({
          answer:    `⚠️ ${msg}`,
          sources:   [],
          confidence: 0,
          risk_level: 'safe',
          escalated:  false,
          method:    'error',
          latency_ms: null,
          msg_id:    null,
        });
      })
      .finally(() => {
        setLoading(false);
        input.focus();
      });
  }

  /* ================================================================
     RENDER HELPERS
     ================================================================ */
  function appendUserBubble(text) {
    const div = document.createElement('div');
    div.className = 'msg-row user';
    div.innerHTML = `
      <div class="msg-avatar user">👤</div>
      <div style="max-width:74%">
        <div class="msg-bubble user">${escHtml(text)}</div>
        <div class="msg-meta" style="justify-content:flex-end">
          ${timeNow()}
        </div>
      </div>`;
    msgBox.appendChild(div);
    scrollBottom(msgBox);
  }

  function appendAIBubble(data) {
    const risk     = data.risk_level || 'safe';
    const esc      = data.escalated;
    const bubbleCls = esc ? 'escalated' : risk === 'phi' ? 'phi-block' : 'ai';
    const conf      = data.confidence ? Math.round(data.confidence * 100) : null;
    const methodMap = {
      claude_api:          '🤖 Claude AI',
      extractive:          '📄 Extractive',
      escalated_clinical:  '⚕️ Escalated',
      blocked_phi:         '🔒 PHI Blocked',
      no_index:            '⚠️ No Index',
      no_results:          '❌ No Results',
      error:               '❌ Error',
    };
    const methodLabel = methodMap[data.method] || data.method || '';

    /* Source chips */
    let sourcesHtml = '';
    if (Array.isArray(data.sources) && data.sources.length) {
      const chips = data.sources
        .map(s => `<span class="source-chip">${escHtml(s.id || s.title || 'doc')}</span>`)
        .join('');
      sourcesHtml = `
        <div class="msg-sources">
          <div style="font-size:10px;color:var(--gray-400);font-weight:700;
                      text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">
            Sources
          </div>
          ${chips}
        </div>`;
    }

    /* Confidence bar */
    const confHtml = conf
      ? `&nbsp;·&nbsp;<span class="confidence-bar">
           <span class="confidence-fill" style="width:${conf}%"></span>
         </span> ${conf}%`
      : '';

    /* Feedback buttons (only if we have a msg_id from the server) */
    const fbHtml = data.msg_id
      ? `<div class="feedback-btns">
           <button class="fb-btn"
             onclick="sendFeedback(${data.msg_id}, 1, this)">👍 Helpful</button>
           <button class="fb-btn"
             onclick="sendFeedback(${data.msg_id}, -1, this)">👎 Not helpful</button>
         </div>`
      : '';

    const div = document.createElement('div');
    div.className = 'msg-row';
    if (data.msg_id) div.dataset.msgId = data.msg_id;

    div.innerHTML = `
      <div class="msg-avatar ai">🏥</div>
      <div style="max-width:74%">
        <div class="msg-bubble ${bubbleCls}">
          ${formatAnswer(data.answer)}
          ${sourcesHtml}
        </div>
        <div class="msg-meta">
          ${timeNow()}
          ${confHtml}
          ${data.latency_ms ? `&nbsp;·&nbsp;${data.latency_ms}ms` : ''}
          ${methodLabel ? `&nbsp;·&nbsp;<span style="color:var(--primary);font-weight:600">${methodLabel}</span>` : ''}
          ${esc ? '&nbsp;<span class="badge badge-yellow">Escalated</span>' : ''}
        </div>
        ${fbHtml}
      </div>`;

    msgBox.appendChild(div);
    scrollBottom(msgBox);
  }

  function appendTyping() {
    const div = document.createElement('div');
    div.className = 'msg-row';
    div.id = 'typing-indicator';
    div.innerHTML = `
      <div class="msg-avatar ai">🏥</div>
      <div class="msg-bubble ai" style="padding:14px 18px">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>`;
    msgBox.appendChild(div);
    scrollBottom(msgBox);
    return div;
  }

  function setLoading(on) {
    sendBtn.disabled = on;
    sendBtn.style.opacity = on ? '0.6' : '1';
  }

  function timeNow() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

});   /* end DOMContentLoaded */

/* ================================================================
   FEEDBACK  (global — also used by server-rendered history bubbles)
   ================================================================ */
function sendFeedback(msgId, rating, btn) {
  fetch(`/chat/message/${msgId}/feedback/`, {
    method:  'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken':  (() => {
        const m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
      })(),
    },
    body: JSON.stringify({ rating }),
  })
  .then(r => r.ok ? r.json() : null)
  .then(() => {
    const row = btn.closest('.msg-row') || btn.parentElement;
    row.querySelectorAll('.fb-btn').forEach(b => {
      b.classList.remove('up', 'dn');
    });
    btn.classList.add(rating > 0 ? 'up' : 'dn');
  })
  .catch(() => {});   /* silent — feedback is non-critical */
}
