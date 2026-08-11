import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Check, RefreshCw, Pencil, Volume2, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import VerifiedBadge from '@/components/VerifiedBadge';
import { isVerifiedUser } from '@/lib/verifiedUsers';
import { base44 } from '@/api/base44Client';
import { getVoiceProfile, stripForSpeech } from '@/lib/aiVoices';
import { useLanguage } from '@/lib/LanguageContext';

function CodeBlock({ children, className }) {
  const [copied, setCopied] = useState(false);
  const { t } = useLanguage();
  const language = className?.replace('language-', '') || '';

  const handleCopy = () => {
    navigator.clipboard.writeText(String(children).trim());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-block my-3">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/50">
        <span className="text-xs text-muted-foreground font-mono">{language || 'code'}</span>
        <Button variant="ghost" size="sm" onClick={handleCopy} className="h-6 px-2 text-xs gap-1">
          {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
          {copied ? t('chat.copied') : t('chat.copy')}
        </Button>
      </div>
      <pre className="text-sm"><code>{children}</code></pre>
    </div>
  );
}

export default function MessageBubble({ message, isStreaming, user, onEdit, onRegenerate, isLast, voiceId = 'river' }) {
  const isUser = message.role === 'user';
  const displayName = user?.display_name || user?.full_name;
  const userInitial = displayName ? displayName.charAt(0).toUpperCase() : 'U';
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.content);
  const [speaking, setSpeaking] = useState(false);
  const { t } = useLanguage();

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveEdit = () => {
    if (!editText.trim()) return;
    onEdit?.(message.id, editText.trim());
    setIsEditing(false);
  };

  const handleTTS = () => {
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const cleanText = stripForSpeech(message.content).substring(0, 5000);
    if (!cleanText) return;
    const profile = getVoiceProfile(voiceId);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = profile.rate;
    utterance.pitch = profile.pitch;
    utterance.lang = profile.lang;
    const voices = window.speechSynthesis.getVoices();
    const match = voices.find(v => v.lang === profile.lang) || voices.find(v => v.lang.startsWith(profile.lang.split('-')[0]));
    if (match) utterance.voice = match;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    setSpeaking(true);
  };

  return (
    <div className={`group flex gap-3 px-4 py-4 ${isUser ? '' : 'bg-muted/30'}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 relative ${
        isUser
          ? 'bg-gradient-to-br from-orange-500 to-blue-500'
          : 'bg-gradient-to-br from-orange-500/20 to-blue-500/20 border border-orange-500/30'
      }`}>
        {isUser ? (
          user?.avatar_url ? (
            <img src={user.avatar_url} alt={user.full_name} className="w-8 h-8 rounded-lg object-cover" />
          ) : (
            <span className="text-white text-sm font-semibold">{userInitial}</span>
          )
        ) : (
          <img
            src="https://media.base44.com/images/public/6a415277171cff3034584f35/6f17cca71_image.png"
            alt="Bloxy"
            className="w-5 h-5 rounded"
          />
        )}
        {isUser && isVerifiedUser(user?.email) && (
          <div className="absolute -bottom-1 -right-1 bg-background rounded-full p-px">
            <VerifiedBadge size={12} />
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0 overflow-x-auto">
        <div className="flex items-center gap-1.5 mb-1">
          <p className="text-xs font-medium text-muted-foreground">
            {isUser ? (displayName || t('chat.you')) : t('chat.bloxyBot')}
          </p>
          {isUser && isVerifiedUser(user?.email) && <VerifiedBadge size={13} />}
          {message.model && !isUser && (
            <span className="text-xs text-muted-foreground opacity-50">· {message.model}</span>
          )}
        </div>
        {isEditing ? (
          <div className="mt-1">
            <textarea
              value={editText}
              onChange={e => setEditText(e.target.value)}
              className="w-full bg-muted/40 rounded-lg p-2.5 text-sm outline-none border border-border/50 resize-none min-h-[60px] focus:border-orange-500/50"
              autoFocus
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSaveEdit(); } }}
            />
            <div className="flex gap-2 mt-1.5">
              <Button size="sm" onClick={handleSaveEdit} className="h-7 text-xs">{t('chat.saveSend')}</Button>
              <Button size="sm" variant="ghost" onClick={() => { setIsEditing(false); setEditText(message.content); }} className="h-7 text-xs">{t('common.cancel')}</Button>
            </div>
          </div>
        ) : (
          <>
            <div className={`message-content text-sm leading-relaxed overflow-x-auto ${isStreaming ? 'typing-cursor' : ''}`}>
              <ReactMarkdown
                components={{
                  code({ inline, className, children, ...props }) {
                    if (!inline && (className || String(children).includes('\n'))) {
                      return <CodeBlock className={className}>{children}</CodeBlock>;
                    }
                    return <code className={className} {...props}>{children}</code>;
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
            {!isStreaming && message.id !== 'error' && (
              <div className="flex items-center gap-1 mt-1.5">
                {isUser ? (
                  <Button variant="ghost" size="sm" onClick={() => { setEditText(message.content); setIsEditing(true); }} className="h-6 px-2 text-xs gap-1 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                    <Pencil className="w-3 h-3" /> {t('chat.edit')}
                  </Button>
                ) : (
                  <>
                    <Button variant="ghost" size="sm" onClick={handleCopy} className="h-6 px-2 text-xs gap-1 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                      {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                      {copied ? t('chat.copied') : t('chat.copy')}
                    </Button>
                    {isLast && (
                      <Button variant="ghost" size="sm" onClick={() => onRegenerate?.(message.id)} className="h-6 px-2 text-xs gap-1 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                        <RefreshCw className="w-3 h-3" /> {t('chat.regenerate')}
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={handleTTS} className={`h-6 px-2 text-xs gap-1 transition-opacity ${speaking ? 'text-orange-400 opacity-100' : 'text-muted-foreground opacity-0 group-hover:opacity-100'}`}>
                      {speaking ? <Square className="w-3 h-3" /> : <Volume2 className="w-3 h-3" />}
                      {speaking ? t('chat.stopListen') : t('chat.listen')}
                    </Button>
                  </>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
