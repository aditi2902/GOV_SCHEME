import { useState, useRef, useEffect } from 'react';
import { HiOutlinePaperAirplane, HiOutlineChat, HiOutlineUser } from 'react-icons/hi';
import { RiGovernmentLine } from 'react-icons/ri';
import { chatWithAI } from '../api';
import './Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hi! I'm your Government Scheme Assistant. Ask me anything about scholarships, eligibility, documents, or application processes.\n\nTry asking:\n• \"Can I apply for Pragati Scholarship without income certificate?\"\n• \"What schemes are available for engineering students?\"\n• \"How do I apply on the NSP portal?\""
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setInput('');
    setLoading(true);

    try {
      const userText = sessionStorage.getItem('userText') || null;
      const res = await chatWithAI(q, userText);
      setMessages(prev => [...prev, { role: 'assistant', content: res.answer }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I couldn't process your question. Make sure the backend is running.\n\nError: ${err.message}`
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const quickQuestions = [
    "What scholarships are available for female engineering students?",
    "Can I apply without a domicile certificate?",
    "What is the income limit for AICTE scholarships?",
    "How to apply on NSP portal?",
  ];

  return (
    <div className="chat-page">
      <div className="container chat-container">
        <div className="chat-header">
          <h1 className="heading-md">
            <HiOutlineChat /> Ask <span className="text-gradient">AI Assistant</span>
          </h1>
          <p className="chat-subtitle">
            Powered by RAG — answers from actual scheme documents
          </p>
        </div>

        <div className="chat-window glass-card">
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}>
                <div className="chat-avatar">
                  {msg.role === 'user' ? <HiOutlineUser /> : <RiGovernmentLine />}
                </div>
                <div className="chat-bubble">
                  <span className="chat-role">
                    {msg.role === 'user' ? 'You' : 'SarkariSahay AI'}
                  </span>
                  <div className="chat-text" dangerouslySetInnerHTML={{
                    __html: msg.content
                      .replace(/\n/g, '<br/>')
                      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\*(.+?)\*/g, '<em>$1</em>')
                      .replace(/•/g, '&bull;')
                  }} />
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-message assistant">
                <div className="chat-avatar"><RiGovernmentLine /></div>
                <div className="chat-bubble">
                  <span className="chat-role">SarkariSahay AI</span>
                  <div className="chat-typing">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          <form className="chat-input-bar" onSubmit={handleSend}>
            <input
              ref={inputRef}
              type="text"
              className="input chat-input"
              placeholder="Ask about schemes, eligibility, documents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="btn btn-primary chat-send-btn" disabled={loading || !input.trim()}>
              <HiOutlinePaperAirplane />
            </button>
          </form>
        </div>

        {/* Quick Questions */}
        <div className="chat-quick">
          <span className="chat-quick-label">Quick questions:</span>
          <div className="chat-quick-grid">
            {quickQuestions.map((q, i) => (
              <button
                key={i}
                className="chat-quick-btn"
                onClick={() => setInput(q)}
                disabled={loading}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
