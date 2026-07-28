import React, { useState, useRef, useEffect } from 'react';
import './ChatWidget.css';

const API_URL = 'http://localhost:3002/api/chat';

// ─── Icônes SVG inline ───────────────────
const IconChat = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
);

const IconClose = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);

const IconSend = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);

const IconLink = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
    <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
  </svg>
);

// ─── Message individuel ──────────────────
const Message = ({ msg }) => (
  <div className={`message message--${msg.role}`}>
    {msg.role === 'assistant' && (
      <div className="message__avatar">A</div>
    )}
    <div className="message__content">
      <div className="message__bubble">{msg.text}</div>
      {msg.sources && msg.sources.length > 0 && (
        <div className="message__sources">
          <span className="sources__label">Sources</span>
          {msg.sources.map((s, i) => (
            <a key={i} href={s.url} target="_blank" rel="noreferrer" className="sources__link">
              <IconLink /> {s.titre}
            </a>
          ))}
        </div>
      )}
    </div>
  </div>
);

// ─── Indicateur de frappe ────────────────
const TypingIndicator = () => (
  <div className="message message--assistant">
    <div className="message__avatar">A</div>
    <div className="message__content">
      <div className="message__bubble message__bubble--typing">
        <span/><span/><span/>
      </div>
    </div>
  </div>
);

// ─── Widget principal ────────────────────
export default function ChatWidget() {
  const [isOpen, setIsOpen]     = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Bonjour ! Je suis l\'assistant Astrée Assurances. Comment puis-je vous aider aujourd\'hui ?',
      sources: []
    }
  ]);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const bottomRef               = useRef(null);
  const inputRef                = useRef(null);

  // Auto-scroll vers le bas
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Focus input à l'ouverture
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  const envoyerMessage = async () => {
    const texte = input.trim();
    if (!texte || loading) return;

    setInput('');
    setError(null);
    setMessages(prev => [...prev, { role: 'user', text: texte, sources: [] }]);
    setLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: texte })
      });

      if (!response.ok) {
        throw new Error(`Erreur serveur : ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        text: data.reponse,
        sources: data.sources || []
      }]);

    } catch (err) {
      setError("Une erreur est survenue. Veuillez réessayer.");
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: "Désolé, je rencontre une difficulté technique. Veuillez réessayer ou contacter Astrée au +216 71 104 555.",
        sources: []
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      envoyerMessage();
    }
  };

  const viderConversation = () => {
    setMessages([{
      role: 'assistant',
      text: 'Bonjour ! Je suis l\'assistant Astrée Assurances. Comment puis-je vous aider aujourd\'hui ?',
      sources: []
    }]);
    setError(null);
  };

  // Questions suggérées
  const suggestions = [
    "Comment déclarer un sinistre ?",
    "Quelles sont les garanties auto ?",
    "Comment nous contacter ?",
  ];

  return (
    <>
      {/* ── Fenêtre de chat ── */}
      <div className={`chat-window ${isOpen ? 'chat-window--open' : ''}`}>

        {/* Header */}
        <div className="chat-header">
          <div className="chat-header__info">
            <div className="chat-header__avatar">A</div>
            <div>
              <div className="chat-header__name">Assistant Astrée</div>
              <div className="chat-header__status">
                <span className="status-dot"/>En ligne
              </div>
            </div>
          </div>
          <div className="chat-header__actions">
            <button className="btn-icon" onClick={viderConversation} title="Nouvelle conversation">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.49"/>
              </svg>
            </button>
            <button className="btn-icon" onClick={() => setIsOpen(false)} title="Fermer">
              <IconClose />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <Message key={i} msg={msg} />
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Suggestions (uniquement si 1 seul message = début) */}
        {messages.length === 1 && (
          <div className="chat-suggestions">
            {suggestions.map((s, i) => (
              <button key={i} className="suggestion-btn" onClick={() => {
                setInput(s);
                setTimeout(() => inputRef.current?.focus(), 100);
              }}>
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="chat-input">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Posez votre question..."
            rows={1}
            disabled={loading}
          />
          <button
            className={`send-btn ${input.trim() && !loading ? 'send-btn--active' : ''}`}
            onClick={envoyerMessage}
            disabled={!input.trim() || loading}
            title="Envoyer"
          >
            <IconSend />
          </button>
        </div>

        <div className="chat-footer">Propulsé par Astrée Assurances IA</div>
      </div>

      {/* ── Bouton flottant ── */}
      <button
        className={`chat-fab ${isOpen ? 'chat-fab--open' : ''}`}
        onClick={() => setIsOpen(o => !o)}
        title={isOpen ? 'Fermer' : 'Assistant Astrée'}
      >
        {isOpen ? <IconClose /> : <IconChat />}
        {!isOpen && messages.length > 1 && (
          <span className="chat-fab__badge">{messages.filter(m => m.role === 'assistant').length - 1}</span>
        )}
      </button>
    </>
  );
}