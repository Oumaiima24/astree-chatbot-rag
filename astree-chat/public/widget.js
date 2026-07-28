(function () {
  // ─── Configuration ───────────────────────────────────────────────
  const API_URL = 'http://localhost:3002/api/chat';
  // ─── Styles ──────────────────────────────────────────────────────
  const styles = `
    #astree-widget-fab {
      position: fixed;
      bottom: 28px;
      right: 28px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #003B7A, #0077B6);
      color: #fff;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 32px rgba(0,59,122,0.35);
      z-index: 99999;
      animation: astree-pulse 2.5s infinite;
      font-family: Inter, system-ui, sans-serif;
    }
    #astree-widget-fab:hover { transform: scale(1.08); }
    #astree-widget-fab.open { animation: none; background: #475569; }

    @keyframes astree-pulse {
      0%   { box-shadow: 0 8px 32px rgba(0,59,122,0.35), 0 0 0 0 rgba(0,119,182,0.4); }
      70%  { box-shadow: 0 8px 32px rgba(0,59,122,0.35), 0 0 0 10px rgba(0,119,182,0); }
      100% { box-shadow: 0 8px 32px rgba(0,59,122,0.35), 0 0 0 0 rgba(0,119,182,0); }
    }

    #astree-widget-window {
      position: fixed;
      bottom: 100px;
      right: 28px;
      width: 380px;
      height: 560px;
      background: #fff;
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0,59,122,0.22);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      z-index: 99998;
      opacity: 0;
      transform: translateY(20px) scale(0.96);
      pointer-events: none;
      transition: opacity 0.25s ease, transform 0.25s ease;
      font-family: Inter, system-ui, sans-serif;
    }
    #astree-widget-window.open {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: all;
    }

    .aw-header {
      background: linear-gradient(135deg, #003B7A, #0077B6);
      padding: 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    .aw-header-info { display: flex; align-items: center; gap: 12px; }
    .aw-avatar {
      width: 40px; height: 40px; border-radius: 50%;
      background: rgba(255,255,255,0.2);
      color: #fff; font-weight: 700; font-size: 16px;
      display: flex; align-items: center; justify-content: center;
      border: 2px solid rgba(255,255,255,0.3);
    }
    .aw-name { color: #fff; font-weight: 600; font-size: 15px; }
    .aw-status { color: rgba(255,255,255,0.75); font-size: 12px; display: flex; align-items: center; gap: 5px; margin-top: 2px; }
    .aw-dot { width: 7px; height: 7px; border-radius: 50%; background: #4ADE80; display: inline-block; }
    .aw-header-btns { display: flex; gap: 6px; }
    .aw-btn {
      background: rgba(255,255,255,0.15); border: none; border-radius: 8px;
      color: #fff; width: 32px; height: 32px;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer;
    }
    .aw-btn:hover { background: rgba(255,255,255,0.25); }

    .aw-messages {
      flex: 1; overflow-y: auto; padding: 20px 16px;
      display: flex; flex-direction: column; gap: 16px;
      scroll-behavior: smooth;
    }
    .aw-messages::-webkit-scrollbar { width: 4px; }
    .aw-messages::-webkit-scrollbar-thumb { background: #E2E8F0; border-radius: 4px; }

    .aw-msg { display: flex; align-items: flex-end; gap: 8px; animation: aw-fade 0.3s ease; }
    .aw-msg.user { flex-direction: row-reverse; }
    @keyframes aw-fade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

    .aw-msg-avatar {
      width: 30px; height: 30px; border-radius: 50%;
      background: linear-gradient(135deg, #003B7A, #0077B6);
      color: #fff; font-size: 12px; font-weight: 700;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .aw-msg-content { max-width: 78%; display: flex; flex-direction: column; gap: 6px; }
    .aw-msg.user .aw-msg-content { align-items: flex-end; }

    .aw-bubble {
      padding: 11px 15px; border-radius: 18px; font-size: 14px;
      line-height: 1.55; color: #1E293B; background: #F1F5F9;
      border-bottom-left-radius: 4px;
    }
    .aw-msg.user .aw-bubble {
      background: linear-gradient(135deg, #003B7A, #0077B6);
      color: #fff; border-bottom-left-radius: 18px; border-bottom-right-radius: 4px;
    }
    .aw-bubble.typing { display: flex; gap: 5px; align-items: center; padding: 14px 18px; }
    .aw-bubble.typing span {
      width: 7px; height: 7px; border-radius: 50%; background: #94A3B8;
      animation: aw-bounce 1.2s infinite;
    }
    .aw-bubble.typing span:nth-child(2) { animation-delay: 0.2s; }
    .aw-bubble.typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes aw-bounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }

    .aw-sources { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
    .aw-sources-label { font-size: 11px; color: #94A3B8; font-weight: 500; }
    .aw-source-link {
      display: inline-flex; align-items: center; gap: 4px;
      font-size: 11px; color: #0077B6; text-decoration: none;
      background: #E8F4FD; padding: 3px 8px; border-radius: 20px;
      font-weight: 500;
    }
    .aw-source-link:hover { background: #BFE8F9; }

    .aw-suggestions {
      padding: 0 16px 12px; display: flex; flex-direction: column; gap: 6px; flex-shrink: 0;
    }
    .aw-suggestion {
      background: #fff; border: 1.5px solid #E2E8F0; border-radius: 20px;
      padding: 8px 14px; font-size: 13px; color: #0077B6;
      cursor: pointer; text-align: left; font-family: Inter, system-ui, sans-serif;
      font-weight: 500;
    }
    .aw-suggestion:hover { background: #E8F4FD; border-color: #00A8E8; }

    .aw-input-area {
      display: flex; align-items: flex-end; gap: 10px;
      padding: 12px 16px; border-top: 1px solid #F1F5F9; background: #fff; flex-shrink: 0;
    }
    .aw-input {
      flex: 1; border: 1.5px solid #E2E8F0; border-radius: 22px;
      padding: 10px 16px; font-size: 14px; font-family: Inter, system-ui, sans-serif;
      resize: none; outline: none; color: #1E293B; background: #F8FAFC;
      max-height: 100px; line-height: 1.5;
    }
    .aw-input:focus { border-color: #0077B6; background: #fff; }
    .aw-input::placeholder { color: #94A3B8; }

    .aw-send {
      width: 42px; height: 42px; border-radius: 50%;
      background: #E2E8F0; border: none; color: #94A3B8;
      cursor: not-allowed; display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; transition: all 0.2s;
    }
    .aw-send.active {
      background: linear-gradient(135deg, #003B7A, #0077B6);
      color: #fff; cursor: pointer;
    }
    .aw-send.active:hover { transform: scale(1.08); }

    .aw-footer {
      text-align: center; font-size: 11px; color: #94A3B8;
      padding: 6px 16px 10px; background: #fff;
    }

    @media (max-width: 480px) {
      #astree-widget-window { width: calc(100vw - 24px); right: 12px; bottom: 90px; height: 70vh; }
      #astree-widget-fab { right: 16px; bottom: 16px; }
    }
  `;

  const styleEl = document.createElement('style');
  styleEl.textContent = styles;
  document.head.appendChild(styleEl);

  let isOpen = false;
  let loading = false;
  let historique = [];
  let messages = [{
    role: 'assistant',
    text: 'Bonjour ! Je suis l\'assistant Astrée Assurances. Comment puis-je vous aider aujourd\'hui ?',
    sources: []
  }];

  const suggestions = [
    'Comment déclarer un sinistre ?',
    'Quelles sont les garanties auto ?',
    'Comment nous contacter ?'
  ];

  const iconChat = `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;
  const iconClose = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
  const iconSend = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`;
  const iconLink = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;
  const iconRefresh = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.49"/></svg>`;

  const fab = document.createElement('button');
  fab.id = 'astree-widget-fab';
  fab.innerHTML = iconChat;

  const win = document.createElement('div');
  win.id = 'astree-widget-window';
  win.innerHTML = `
    <div class="aw-header">
      <div class="aw-header-info">
        <div class="aw-avatar">A</div>
        <div>
          <div class="aw-name">Assistant Astrée</div>
          <div class="aw-status"><span class="aw-dot"></span>En ligne</div>
        </div>
      </div>
      <div class="aw-header-btns">
        <button class="aw-btn" id="aw-reset" title="Nouvelle conversation">${iconRefresh}</button>
        <button class="aw-btn" id="aw-close" title="Fermer">${iconClose}</button>
      </div>
    </div>
    <div class="aw-messages" id="aw-messages"></div>
    <div class="aw-suggestions" id="aw-suggestions"></div>
    <div class="aw-input-area">
      <textarea class="aw-input" id="aw-input" placeholder="Posez votre question..." rows="1"></textarea>
      <button class="aw-send" id="aw-send">${iconSend}</button>
    </div>
    <div class="aw-footer">Propulsé par Astrée Assurances IA</div>
  `;

  document.body.appendChild(fab);
  document.body.appendChild(win);

  const msgContainer  = document.getElementById('aw-messages');
  const input         = document.getElementById('aw-input');
  const sendBtn       = document.getElementById('aw-send');
  const suggestionsEl = document.getElementById('aw-suggestions');

  function renderMessages() {
    msgContainer.innerHTML = '';
    messages.forEach(msg => {
      const div = document.createElement('div');
      div.className = `aw-msg ${msg.role}`;
      let sourcesHtml = '';
      if (msg.sources && msg.sources.length > 0) {
        sourcesHtml = `<div class="aw-sources">
          <span class="aw-sources-label">Sources</span>
          ${msg.sources.map(s => `<a href="${s.url}" target="_blank" class="aw-source-link">${iconLink} ${s.titre}</a>`).join('')}
        </div>`;
      }
      div.innerHTML = msg.role === 'assistant'
        ? `<div class="aw-msg-avatar">A</div>
           <div class="aw-msg-content">
             <div class="aw-bubble">${msg.text}</div>
             ${sourcesHtml}
           </div>`
        : `<div class="aw-msg-content">
             <div class="aw-bubble">${msg.text}</div>
           </div>`;
      msgContainer.appendChild(div);
    });

    if (loading) {
      const typing = document.createElement('div');
      typing.className = 'aw-msg assistant';
      typing.innerHTML = `<div class="aw-msg-avatar">A</div>
        <div class="aw-msg-content"><div class="aw-bubble typing"><span></span><span></span><span></span></div></div>`;
      msgContainer.appendChild(typing);
    }

    msgContainer.scrollTop = msgContainer.scrollHeight;

    suggestionsEl.innerHTML = '';
    if (messages.length === 1) {
      suggestions.forEach(s => {
        const btn = document.createElement('button');
        btn.className = 'aw-suggestion';
        btn.textContent = s;
        btn.onclick = () => { input.value = s; updateSendBtn(); input.focus(); };
        suggestionsEl.appendChild(btn);
      });
    }
  }

  function updateSendBtn() {
    sendBtn.classList.toggle('active', input.value.trim().length > 0 && !loading);
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text || loading) return;

    input.value = '';
    updateSendBtn();
    messages.push({ role: 'user', text, sources: [] });
    historique.push({ role: 'user', text });
    loading = true;
    renderMessages();

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({ message: text, historique: historique.slice(-10) })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      messages.push({ role: 'assistant', text: data.reponse, sources: data.sources || [] });
      historique.push({ role: 'assistant', text: data.reponse });
    } catch {
      messages.push({
        role: 'assistant',
        text: 'Désolé, je rencontre une difficulté technique. Veuillez réessayer ou contacter Astrée au +216 71 104 555.',
        sources: []
      });
    } finally {
      loading = false;
      renderMessages();
    }
  }

  fab.onclick = () => {
    isOpen = !isOpen;
    fab.classList.toggle('open', isOpen);
    win.classList.toggle('open', isOpen);
    fab.innerHTML = isOpen ? iconClose : iconChat;
    if (isOpen) setTimeout(() => input.focus(), 300);
  };

  document.getElementById('aw-close').onclick = () => fab.click();

  document.getElementById('aw-reset').onclick = () => {
    messages = [{ role: 'assistant', text: 'Bonjour ! Je suis l\'assistant Astrée Assurances. Comment puis-je vous aider aujourd\'hui ?', sources: [] }];
    historique = [];
    renderMessages();
  };

  input.addEventListener('input', updateSendBtn);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  sendBtn.onclick = sendMessage;

  renderMessages();
})();