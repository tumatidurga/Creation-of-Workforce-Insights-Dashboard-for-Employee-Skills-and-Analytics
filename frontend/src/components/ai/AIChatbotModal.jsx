import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, X, Sparkles, User, RefreshCw, Copy, Download } from 'lucide-react';
import { api } from '../../services/api';

export const AIChatbotModal = ({ isOpen, onClose, userRole = 'EMPLOYEE', currentEmpId = null }) => {
  const [messages, setMessages] = useState([
    {
      id: '1',
      sender: 'ai',
      text: userRole === 'HR_ADMIN'
        ? 'Hello! I am your NEXUS Workforce AI Assistant. Ask me anything about headcount analytics, workforce capacity, payroll calculations, or HR compliance policies.'
        : 'Hello! I am your NEXUS Employee Assistant. Ask me about your attendance, leave balance, upcoming shift, or payroll.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [copyStatus, setCopyStatus] = useState('');
  const [downloadStatus, setDownloadStatus] = useState('');

  const suggestedPrompts = userRole === 'HR_ADMIN' ? [
    "Summarize workforce headcount by department",
    "Summarize attendance anomalies today",
    "What is the projected August payroll cost?",
    "Draft workforce expansion recommendations"
  ] : [
    "How is my attendance this month?",
    "Do I have any attendance alerts?",
    "What is my current leave balance?",
    "What is my next shift?",
    "Show my leave history",
    "Explain my latest payroll information"
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!isOpen) return null;

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || isLoading) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setIsLoading(true);

    try {
      const roleLabel = userRole === 'HR_ADMIN' ? 'HR Administrator' : 'Employee';
      const context = currentEmpId ? { empId: currentEmpId } : undefined;
      const response = await api.sendChatMessage(query, roleLabel, context);
      const aiReplyText = response?.reply || response?.text || 'AI service responded without a usable message.';

      const aiMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: aiReplyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: 'AI service is currently unavailable. Please try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const buildConversationText = () => {
    const header = ['NEXUS AI ASSISTANT', '==================', ''];
    if (!messages || messages.length === 0) {
      header.push('No messages.');
      return header.join('\n');
    }

    const parts = [...header];
    messages.forEach((msg) => {
      const senderLabel = msg.sender === 'user' ? 'User:' : 'Nexus AI:';
      parts.push(senderLabel);
      parts.push(msg.text || '');
      parts.push('');
      parts.push('------------------');
      parts.push('');
    });
    // remove trailing separator
    while (parts.length > 0 && parts[parts.length - 1] === '') parts.pop();
    return parts.join('\n');
  };

  const handleCopyChat = async () => {
    try {
      const text = buildConversationText();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
      }
      setCopyStatus('Copied!');
      setTimeout(() => setCopyStatus(''), 2000);
    } catch (err) {
      console.error('Copy chat failed', err);
      setCopyStatus('Copy failed');
      setTimeout(() => setCopyStatus(''), 2000);
    }
  };

  const handleDownloadChat = () => {
    try {
      const text = buildConversationText();
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      const now = new Date();
      const ts = now.toISOString().slice(0,19).replace(/:/g,'-');
      const filename = `Nexus_AI_Chat_${ts}.txt`;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setDownloadStatus('Downloaded');
      setTimeout(() => setDownloadStatus(''), 2000);
    } catch (err) {
      console.error('Download chat failed', err);
      setDownloadStatus('Download failed');
      setTimeout(() => setDownloadStatus(''), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="flex h-[88vh] w-full max-w-lg flex-col rounded-2xl bg-white shadow-2xl dark:bg-slate-900 dark:text-white border border-slate-200 dark:border-slate-800">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 p-4 dark:border-slate-800 bg-gradient-to-r from-indigo-900 via-slate-900 to-slate-900 text-white rounded-t-2xl">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-md">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold flex items-center gap-1.5">
                NEXUS AI HR ASSISTANT
                <Sparkles className="h-3 w-3 text-amber-300" />
              </h3>
              <p className="text-[10px] text-slate-300">Enterprise workforce assistant</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button onClick={handleCopyChat} title="Copy chat" className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">
              <Copy className="h-5 w-5" />
            </button>
            <button onClick={handleDownloadChat} title="Download chat" className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">
              <Download className="h-5 w-5" />
            </button>
            <span className="text-[11px] text-slate-200 opacity-90">{copyStatus || downloadStatus ? (copyStatus || downloadStatus) : ''}</span>
            <button onClick={onClose} className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Message Container */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4 text-xs">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-2.5 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-white ${
                  msg.sender === 'user' ? 'bg-indigo-600' : 'bg-purple-600'
                }`}
              >
                {msg.sender === 'user' ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
              </div>

              <div
                className={`max-w-[80%] rounded-2xl p-3.5 leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-indigo-600 text-white rounded-tr-none'
                    : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100 rounded-tl-none'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.text}</p>
                <span className="mt-1 block text-[9px] opacity-60 text-right">{msg.timestamp}</span>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-slate-400 font-semibold text-xs">
              <RefreshCw className="h-4 w-4 animate-spin text-purple-600" />
              AI processing enterprise query...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts */}
        <div className="border-t border-slate-100 p-3 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40">
          <div className="text-[10px] font-bold text-slate-400 mb-1.5 uppercase">Suggested AI Queries</div>
          <div className="flex flex-wrap gap-1.5">
            {suggestedPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-medium text-slate-700 hover:border-indigo-500 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2 border-t border-slate-100 p-3 dark:border-slate-800"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask AI about workforce, headcount, or payroll..."
            className="flex-1 rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-white"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-md hover:bg-indigo-700 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
