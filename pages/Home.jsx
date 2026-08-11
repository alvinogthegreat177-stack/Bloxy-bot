import React, { useState, useEffect, useRef, useCallback } from 'react';
import { base44 } from '@/api/base44Client';
import { Menu, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import Sidebar from '@/components/chat/Sidebar';
import ChatInput from '@/components/chat/ChatInput';
import MessageBubble from '@/components/chat/MessageBubble';
import WelcomeScreen from '@/components/chat/WelcomeScreen';
import ToolIndicator from '@/components/chat/ToolIndicator';
import FollowUpSuggestions from '@/components/chat/FollowUpSuggestions';
import { exportConversationToMarkdown, downloadText } from '@/lib/chatExport';
import { runBloxy, generateSmartTitle } from '@/lib/bloxyEngine';
import { useLanguage } from '@/lib/LanguageContext';
import { getDeviceInfo } from '@/lib/deviceDetect';
import { toast } from '@/components/ui/use-toast';

const { Conversation, Message, UserSettings } = base44.entities;

export default function Home() {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTool, setActiveTool] = useState(null);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [nexusMode, setNexusMode] = useState('deep');
  const [draft, setDraft] = useState('');
  const [historyPaused, setHistoryPaused] = useState(false);
  const [voiceId, setVoiceId] = useState('river');
  const [deviceInfo, setDeviceInfo] = useState(null);
  const { t } = useLanguage();
  const messagesEndRef = useRef(null);
  const abortRef = useRef(false);

  useEffect(() => {
    loadConversations();
    base44.auth.me().then(setUser).catch(() => {});
    setDeviceInfo(getDeviceInfo());
    UserSettings.list('-created_date', 1).then(data => {
      if (data.length > 0) {
        const s = data[0];
        const theme = s.theme || 'dark';
        localStorage.setItem('bloxy_theme', JSON.stringify(theme));
        document.documentElement.classList.toggle('dark', theme !== 'light');
        setNexusMode(s.nexus_mode || 'deep');
        setVoiceId(s.voice || 'river');
        setHistoryPaused(s.history_paused || false);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (activeConvId) loadMessages(activeConvId);
    else setMessages([]);
    const draftKey = activeConvId ? `bloxy_draft_${activeConvId}` : 'bloxy_draft_new';
    setDraft(localStorage.getItem(draftKey) || '');
  }, [activeConvId]);

  const handleDraftChange = (text) => {
    setDraft(text);
    const draftKey = activeConvId ? `bloxy_draft_${activeConvId}` : 'bloxy_draft_new';
    localStorage.setItem(draftKey, text);
  };

  const toggleNexusMode = () => {
    const newMode = nexusMode === 'deep' ? 'save' : 'deep';
    setNexusMode(newMode);
    UserSettings.list('-created_date', 1).then(data => {
      if (data.length > 0) UserSettings.update(data[0].id, { nexus_mode: newMode });
    }).catch(() => {});
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversations = async () => {
    const data = await Conversation.list('-updated_date', 50);
    setConversations(data);
  };

  const loadMessages = async (convId) => {
    const data = await Message.filter({ conversation_id: convId }, 'created_date', 200);
    setMessages(data);
  };

  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([]);
  };

  const handleSelectChat = (id) => {
    setActiveConvId(id);
  };

  const handleDeleteChat = async (id) => {
    await Conversation.delete(id);
    if (activeConvId === id) { setActiveConvId(null); setMessages([]); }
    loadConversations();
  };

  const handleToggleFavorite = async (id, val) => {
    await Conversation.update(id, { is_favorite: val });
    loadConversations();
  };

  const handleRenameChat = async (id, newTitle) => {
    await Conversation.update(id, { title: newTitle });
    loadConversations();
  };

  const detectTool = (text) => {
    const lower = text.toLowerCase();
    if (lower.includes('weather') || lower.includes('forecast') || lower.includes('temperature') || lower.includes('rain') || lower.includes('snow') || lower.includes('humidity') || lower.includes('wind') || lower.includes('climate') || lower.includes('storm') || lower.includes('cold') || lower.includes('hot') || lower.includes('sunny') || lower.includes('cloudy')) return 'weather';
    if (lower.includes('stock') || lower.includes('crypto') || lower.includes('bitcoin') || lower.includes('ethereum') || lower.includes('price of') || lower.includes('market') || lower.includes('currency') || lower.includes('exchange rate') || lower.includes('forex') || lower.includes('coin') || lower.includes('nasdaq') || lower.includes('dow') || lower.includes('sp500') || lower.includes('investing') || lower.includes('inflation') || lower.includes('gdp') || lower.includes('economy') || lower.includes('dollar') || lower.includes('euro')) return 'finance';
    if (lower.includes('news') || lower.includes('headline') || lower.includes('latest') || lower.includes('breaking') || lower.includes('today in') || lower.includes('current events') || lower.includes('what happened') || lower.includes('politics') || lower.includes('election') || lower.includes('war') || lower.includes('conflict')) return 'news';
    if (lower.includes('movie') || lower.includes('film') || lower.includes('tv show') || lower.includes('series') || lower.includes('actor') || lower.includes('director') || lower.includes('imdb') || lower.includes('netflix') || lower.includes('anime') || lower.includes('watch') || lower.includes('streaming') || lower.includes('season') || lower.includes('episode') || lower.includes('cast')) return 'movies';
    if (lower.includes('wikipedia') || lower.includes('wiki') || lower.includes('who is') || lower.includes('what is') || lower.includes('define') || lower.includes('meaning of') || lower.includes('history of') || lower.includes('book') || lower.includes('author') || lower.includes('research') || lower.includes('paper') || lower.includes('study') || lower.includes('science') || lower.includes('biology') || lower.includes('physics') || lower.includes('chemistry') || lower.includes('math') || lower.includes('explain')) return 'knowledge';
    if (lower.includes('search') || lower.includes('find') || lower.includes('look up') || lower.includes('google') || lower.includes('browse') || lower.includes('website') || lower.includes('recipe') || lower.includes('how to') || lower.includes('where to') || lower.includes('best') || lower.includes('recommend') || lower.includes('review') || lower.includes('compare') || lower.includes('vs') || lower.includes('difference between') || lower.includes('sports') || lower.includes('score') || lower.includes('nutrition') || lower.includes('food') || lower.includes('restaurant') || lower.includes('travel') || lower.includes('country') || lower.includes('city') || lower.includes('population') || lower.includes('space') || lower.includes('nasa') || lower.includes('planet') || lower.includes('health') || lower.includes('symptom') || lower.includes('drug') || lower.includes('medicine')) return 'search';
    if (lower.includes('trending') || lower.includes('social media') || lower.includes('twitter') || lower.includes('x.com') || lower.includes('tiktok') || lower.includes('instagram') || lower.includes('youtube') || lower.includes('facebook') || lower.includes('mastodon') || lower.includes('viral') || lower.includes('reddit') || lower.includes('hacker news')) return 'social';
    if (lower.includes('code') || lower.includes('function') || lower.includes('debug') || lower.includes('program') || lower.includes('script') || lower.includes('algorithm') || lower.includes('api') || lower.includes('bug') || lower.includes('error') || lower.includes('javascript') || lower.includes('python') || lower.includes('react') || lower.includes('css') || lower.includes('html') || lower.includes('sql') || lower.includes('database') || lower.includes('git')) return 'code';
    // Default: use internet context for everything else
    return 'search';
  };

  const generateTitle = (userMessage) => {
    const words = userMessage.trim().split(/\s+/).slice(0, 5).join(' ');
    return words ? (words.length < userMessage.trim().length ? words + '…' : words) : t('chat.newChat');
  };

  const buildPrompt = (history, text, tool) => {
    const conversationHistory = history.slice(-10).map(m => `${m.role}: ${m.content}`).join('\n');
    let systemPrompt = `You are Bloxy-bot AI, a friendly, knowledgeable, and conversational AI assistant with access to real-time internet data.

CRITICAL RULES:
- Be conversational, natural, and engaging — like talking to a brilliant friend who knows everything.
- NEVER say "I don't have access to real-time data" or "I can't browse the internet" — you DO have internet context.
- When you use live internet data, briefly cite the source inline (e.g., "According to Reuters...", "Per Wikipedia...").
- Give a complete, well-structured answer — never a one-liner. Cover the key points, context, and relevant detail.
- Use markdown (bold, lists, tables) to make the answer easy to read.
- For code, always use proper code blocks with language tags.
- Be thorough but warm, not robotic.`;

    if (tool === 'weather') systemPrompt += '\n\nUse live weather data. Give temperature, "feels like", humidity, wind, and a 5-day outlook conversationally.';
    if (tool === 'finance') systemPrompt += '\n\nUse live market data. Give current prices, % change (24h/7d), market cap, and volume naturally.';
    if (tool === 'news') systemPrompt += '\n\nUse live news data. Summarize top headlines with source, category, and 2-sentence summary each.';
    if (tool === 'knowledge') systemPrompt += '\n\nDraw from Wikipedia, academic sources, and web context. Explain things naturally with fascinating related facts.';
    if (tool === 'movies') systemPrompt += '\n\nUse live movie/TV data. Include ratings, cast, director, synopsis, and 3 similar titles.';
    if (tool === 'search') systemPrompt += '\n\nUse web search context. Give a rich, structured answer with key facts, multiple perspectives, and relevant sources.';

    return `${systemPrompt}\n\nConversation history:\n${conversationHistory}\n\nUser: ${text}\n\nAssistant:`;
  };

  const runAIResponse = async (convId, priorMessages, userText, attachments = [], persist = true) => {
    const tool = detectTool(userText);
    setActiveTool(tool);
    setIsLoading(true);

    setMessages(prev => [...prev, { id: 'streaming', role: 'assistant', content: '', model: 'Bloxy AI' }]);

    try {
      const result = await runBloxy({
        messages: priorMessages.map(m => ({ role: m.role, content: m.content })),
        tool,
        nexusMode,
      });
      if (abortRef.current) return;
      const content = result.content || '';
      const model = result.model || 'local';
      let assistantMsg;
      if (persist) {
        assistantMsg = await Message.create({
          conversation_id: convId,
          role: 'assistant',
          content,
          model,
          has_code: content.includes('```'),
        });
      } else {
        assistantMsg = { id: `local_${Date.now()}`, role: 'assistant', content, model, has_code: content.includes('```') };
      }
      setMessages(prev => prev.filter(m => m.id !== 'streaming').concat(assistantMsg));
      if (persist) {
        if (priorMessages.length === 0) {
          const title = await generateSmartTitle(userText);
          if (title) await Conversation.update(convId, { title });
        }
        await Conversation.update(convId, {
          message_count: priorMessages.length + 2,
          last_message_preview: content.substring(0, 100),
        }).catch(() => {});
        loadConversations();
      }
    } catch (err) {
      console.error('Bloxy AI error:', err);
      const errMsg = err?.message || 'unknown error';
      toast({ title: t('chat.connectionError'), description: t('chat.couldNotReach'), variant: "destructive" });
      const isLimit = /credit|limit|quota|exhaust|usage/i.test(errMsg) || errMsg === 'Network Error';
      setMessages(prev => prev.filter(m => m.id !== 'streaming').concat({
        id: 'error',
        role: 'assistant',
        content: `${t('chat.errorMsg')} (${errMsg})`,
        model: 'System',
      }));
    } finally {
      setIsLoading(false);
      setActiveTool(null);
    }
  };

  const handleSend = async (text, attachments = []) => {
    if (!text.trim()) return;
    abortRef.current = false;

    const draftKey = activeConvId ? `bloxy_draft_${activeConvId}` : 'bloxy_draft_new';
    localStorage.removeItem(draftKey);
    setDraft('');

    if (historyPaused) {
      const localUserMsg = { id: `local_${Date.now()}`, role: 'user', content: text, attachments: attachments.map(a => a.url) };
      const priorMessages = [...messages, localUserMsg];
      setMessages(prev => [...prev, localUserMsg]);
      await runAIResponse(null, priorMessages, text, attachments, false);
      return;
    }

    let convId = activeConvId;
    if (!convId) {
      const conv = await Conversation.create({ title: t('chat.newChat'), message_count: 0 });
      convId = conv.id;
      setActiveConvId(convId);
    }

    const userMsg = await Message.create({
      conversation_id: convId,
      role: 'user',
      content: text,
      attachments: attachments.map(a => a.url),
    });

    const priorMessages = [...messages, userMsg];
    setMessages(prev => [...prev, userMsg]);
    await runAIResponse(convId, priorMessages, text, attachments, true);
  };

  const handleEditMessage = async (messageId, newText) => {
    abortRef.current = false;
    const idx = messages.findIndex(m => m.id === messageId);
    if (idx === -1) return;
    await Message.update(messageId, { content: newText });
    const toRemove = messages.slice(idx + 1);
    for (const m of toRemove) {
      if (m.id !== 'streaming' && m.id !== 'error') await Message.delete(m.id).catch(() => {});
    }
    const editedMsg = { ...messages[idx], content: newText };
    const newMessages = [...messages.slice(0, idx), editedMsg];
    setMessages(newMessages);
    await runAIResponse(activeConvId, newMessages, newText, editedMsg.attachments || []);
  };

  const handleRegenerate = async (assistantMessageId) => {
    abortRef.current = false;
    const idx = messages.findIndex(m => m.id === assistantMessageId);
    if (idx === -1) return;
    let userIdx = idx - 1;
    while (userIdx >= 0 && messages[userIdx].role !== 'user') userIdx--;
    if (userIdx < 0) return;
    const userMsg = messages[userIdx];
    const toRemove = messages.slice(idx);
    for (const m of toRemove) {
      if (m.id !== 'streaming' && m.id !== 'error') await Message.delete(m.id).catch(() => {});
    }
    const newMessages = messages.slice(0, idx);
    setMessages(newMessages);
    await runAIResponse(activeConvId, newMessages, userMsg.content, userMsg.attachments || []);
  };

  const handleStop = () => {
    abortRef.current = true;
    setIsLoading(false);
    setActiveTool(null);
  };

  const handleExport = () => {
    if (!activeConvId || messages.length === 0) return;
    const conv = conversations.find(c => c.id === activeConvId);
    const md = exportConversationToMarkdown(conv, messages);
    const safeTitle = (conv?.title || 'chat').replace(/[^a-z0-9]+/gi, '-').toLowerCase().slice(0, 40);
    downloadText(`${safeTitle || 'chat'}.md`, md);
    toast({ title: t('chat.exported'), description: t('chat.exportedDesc') });
  };

  const lastAssistantId = [...messages].reverse().find(m => m.role === 'assistant' && m.id !== 'streaming' && m.id !== 'error')?.id;

  return (
    <div className="h-screen flex bg-background overflow-x-auto">
      <Sidebar
        conversations={conversations}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        activeConversationId={activeConvId}
        onDeleteChat={handleDeleteChat}
        onToggleFavorite={handleToggleFavorite}
        onRenameChat={handleRenameChat}
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setIsMobileOpen(false)}
        user={user}
      />

      <div className="flex-1 flex flex-col min-w-[320px]">
        {/* Top bar */}
        <div className="h-12 border-b border-border/50 flex items-center justify-between px-4 flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-muted-foreground">
              {activeConvId ? conversations.find(c => c.id === activeConvId)?.title || t('nav.chat') : t('chat.newChat')}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleNexusMode}
              className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium transition-colors ${nexusMode === 'deep' ? 'bg-orange-500/15 text-orange-400' : 'bg-blue-500/15 text-blue-400'}`}
              title={nexusMode === 'deep' ? t('chat.deepTitle') : t('chat.saveTitle')}
            >
              {nexusMode === 'deep' ? `🧠 ${t('chat.deep')}` : `⚡ ${t('chat.save')}`}
            </button>
            {historyPaused && (
              <span className="flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-medium bg-yellow-500/15 text-yellow-400" title={t('chat.historyPausedTitle')}>
                ⏸ {t('chat.paused')}
              </span>
            )}
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleExport} disabled={!activeConvId || messages.length === 0} title={t('chat.exportChat')}>
              <Download className="w-4 h-4" />
            </Button>
            <div className="hidden sm:flex items-center gap-1.5 bg-muted/30 rounded-full px-2.5 py-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
              <span className="text-[10px] text-muted-foreground capitalize">{deviceInfo?.device || t('chat.online')}</span>
            </div>
          </div>
        </div>

        {/* Messages area */}
        {messages.length === 0 && !activeConvId ? (
          <WelcomeScreen onSuggestionClick={(prompt) => handleSend(prompt)} />
        ) : (
          <ScrollArea className="flex-1">
            <div className="max-w-3xl mx-auto px-3 sm:px-4">
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  isStreaming={msg.id === 'streaming'}
                  user={user}
                  onEdit={handleEditMessage}
                  onRegenerate={handleRegenerate}
                  isLast={msg.id === lastAssistantId}
                  voiceId={voiceId}
                />
              ))}
              <ToolIndicator tool={activeTool} isActive={!!activeTool} />
              {!isLoading && messages.length > 0 && (() => {
                const last = messages[messages.length - 1];
                return last?.role === 'assistant' && last.id !== 'error' && (
                  <FollowUpSuggestions onPick={(text) => handleSend(text)} />
                );
              })()}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        )}

        {/* Input */}
        <div className="max-w-3xl mx-auto w-full px-3 sm:px-4">
          <ChatInput onSend={handleSend} isLoading={isLoading} onStop={handleStop} nexusMode={nexusMode} onToggleNexusMode={toggleNexusMode} draft={draft} onDraftChange={handleDraftChange} sendOnEnter={true} />
        </div>
      </div>
    </div>
  );
}
