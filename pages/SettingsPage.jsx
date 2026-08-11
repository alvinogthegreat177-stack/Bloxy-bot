import React, { useState, useEffect, useRef } from 'react';
import { base44 } from '@/api/base44Client';
import { Link } from 'react-router-dom';
import { ArrowLeft, Settings, User, Palette, Bot, Bell, Shield, Save, Check, BadgeCheck, Camera, Loader2, Download, History, MessageSquare, Trash2 } from 'lucide-react';
import VerifiedBadge from '@/components/VerifiedBadge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { buildChatsCsv, buildPromptsCsv, downloadText } from '@/lib/dataExport';

import { AI_VOICES } from '@/lib/aiVoices';
import { WORLD_LANGUAGES } from '@/lib/worldLanguages';
import { getDeviceInfo } from '@/lib/deviceDetect';
import { NEXUS_NAME } from '@/lib/nexusAPI';
import { useLanguage } from '@/lib/LanguageContext';

const { UserSettings, Conversation, Message, SavedPrompt } = base44.entities;

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [user, setUser] = useState(null);
  const [saved, setSaved] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [exporting, setExporting] = useState(null);
  const [historyConvs, setHistoryConvs] = useState([]);
  const [historyMsgs, setHistoryMsgs] = useState([]);
  const [selectedConv, setSelectedConv] = useState(null);

  const avatarInputRef = useRef(null);
  const { toast } = useToast();
  const { t, setLang, syncFromSettings } = useLanguage();

  useEffect(() => {
    base44.auth.me().then(u => { setUser(u); setDisplayName(u?.display_name || u?.full_name || ''); }).catch(() => {});
    loadSettings();
  }, []);

  const refreshUser = async () => {
    const u = await base44.auth.me();
    setUser(u);
    return u;
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAvatarUploading(true);
    try {
      const { file_url } = await base44.integrations.Core.UploadFile({ file });
      await base44.auth.updateMe({ avatar_url: file_url });
      await refreshUser();
      toast({ title: t('settings.avatarUpdated') });
    } catch (err) {
      toast({ title: t('settings.uploadFailed'), description: err?.message, variant: 'destructive' });
    } finally {
      setAvatarUploading(false);
      if (avatarInputRef.current) avatarInputRef.current.value = '';
    }
  };

  const handleRemoveAvatar = async () => {
    try {
      await base44.auth.updateMe({ avatar_url: '' });
      await refreshUser();
      toast({ title: t('settings.avatarRemoved') });
    } catch (err) {
      toast({ title: t('common.failed'), description: err?.message, variant: 'destructive' });
    }
  };

  const handleDisplayNameSave = async () => {
    const trimmed = displayName.trim();
    if (!trimmed || trimmed === (user?.display_name || user?.full_name)) return;
    try {
      await base44.auth.updateMe({ display_name: trimmed });
      await refreshUser();
      toast({ title: t('settings.nameUpdated') });
    } catch (err) {
      toast({ title: t('common.failed'), description: err?.message, variant: 'destructive' });
    }
  };

  const handleExportChats = async () => {
    setExporting('chats');
    try {
      const convs = await Conversation.list('-updated_date', 500);
      const msgs = await Message.list('-created_date', 2000);
      const csv = buildChatsCsv(convs, msgs);
      downloadText('bloxy-chat-history.csv', csv);
      toast({ title: t('settings.chatsExported'), description: `${convs.length} conversations, ${msgs.length} messages` });
    } catch (err) {
      toast({ title: t('settings.exportFailed'), description: err?.message, variant: 'destructive' });
    } finally {
      setExporting(null);
    }
  };

  const handleExportPrompts = async () => {
    setExporting('prompts');
    try {
      const prompts = await SavedPrompt.list('-created_date', 500);
      const csv = buildPromptsCsv(prompts);
      downloadText('bloxy-saved-prompts.csv', csv);
      toast({ title: t('settings.promptsExported'), description: `${prompts.length} prompts` });
    } catch (err) {
      toast({ title: t('settings.exportFailed'), description: err?.message, variant: 'destructive' });
    } finally {
      setExporting(null);
    }
  };



  const loadSettings = async () => {
    const data = await UserSettings.list('-created_date', 1);
    if (data.length > 0) {
      setSettings(data[0]);
      applyTheme(data[0].theme);
      syncFromSettings(data[0].language);
    } else {
      const created = await UserSettings.create({});
      setSettings(created);
    }
  };

  const applyTheme = (theme) => {
    localStorage.setItem('bloxy_theme', JSON.stringify(theme || 'dark'));
    document.documentElement.classList.toggle('dark', theme !== 'light');
  };

  const handleSave = async () => {
    if (!settings) return;
    const { id, created_date, updated_date, created_by_id, ...data } = settings;
    await UserSettings.update(settings.id, data);
    applyTheme(settings.theme);
    setSaved(true);
    toast({ title: t('settings.saved'), description: t('settings.savedDesc') });
    setTimeout(() => setSaved(false), 2000);
  };

  const update = (key, val) => {
    setSettings(prev => ({ ...prev, [key]: val }));
    if (key === 'theme') applyTheme(val);
    if (key === 'language') setLang(val);
  };

  const loadHistory = async () => {
    const convs = await Conversation.list('-updated_date', 50);
    setHistoryConvs(convs);
    if (convs.length > 0) {
      await loadConvMessages(convs[0].id);
    }
  };

  const loadConvMessages = async (convId) => {
    setSelectedConv(convId);
    const msgs = await Message.filter({ conversation_id: convId }, 'created_date', 200);
    setHistoryMsgs(msgs);
  };

  const handleClearAllHistory = async () => {
    for (const c of historyConvs) {
      await Conversation.delete(c.id).catch(() => {});
    }
    setHistoryConvs([]);
    setHistoryMsgs([]);
    setSelectedConv(null);
    toast({ title: t('settings.allHistoryDeleted') });
  };

  const handleDeleteHistoryConv = async (convId) => {
    await Conversation.delete(convId);
    setHistoryConvs(prev => prev.filter(c => c.id !== convId));
    if (selectedConv === convId) {
      setSelectedConv(null);
      setHistoryMsgs([]);
    }
  };

  if (!settings) return (
    <div className="h-screen flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="h-12 border-b border-border/50 flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link to="/"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
          <Settings className="w-4 h-4 text-orange-400" />
          <span className="text-sm font-medium">{t('settings.title')}</span>
        </div>
        <Button onClick={handleSave} size="sm" className="rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 text-white h-8 text-xs gap-1.5">
          {saved ? <Check className="w-3 h-3" /> : <Save className="w-3 h-3" />}
          {saved ? t('common.saved') : t('common.save')}
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto">
          <Tabs defaultValue="profile" onValueChange={(v) => { if (v === 'history') loadHistory(); }}>
            <TabsList className="bg-muted/30 border border-border/50 rounded-xl mb-6 p-1">
              <TabsTrigger value="profile" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><User className="w-3 h-3 mr-1.5" />{t('settings.profile')}</TabsTrigger>
              <TabsTrigger value="ai" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><Bot className="w-3 h-3 mr-1.5" />{t('settings.ai')}</TabsTrigger>
              <TabsTrigger value="appearance" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><Palette className="w-3 h-3 mr-1.5" />{t('settings.appearance')}</TabsTrigger>
              <TabsTrigger value="history" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><History className="w-3 h-3 mr-1.5" />{t('settings.history')}</TabsTrigger>
              <TabsTrigger value="privacy" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><Shield className="w-3 h-3 mr-1.5" />{t('settings.privacy')}</TabsTrigger>
            </TabsList>

            <TabsContent value="profile">
              <div className="glass-card rounded-xl p-6 space-y-5">
                {/* Profile card with verified badge */}
                <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-orange-500/10 to-blue-500/10 border border-orange-500/20 mb-2">
                  <div className="relative flex-shrink-0">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-500 to-blue-500 flex items-center justify-center text-white text-2xl font-bold overflow-hidden">
                      {user?.avatar_url ? <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" /> : (user?.display_name || user?.full_name)?.charAt(0)?.toUpperCase() || t('nav.user').charAt(0)}
                    </div>
                    {/* Orange scalloped verified badge */}
                    <div className="absolute -bottom-1 -right-1 bg-background rounded-full p-0.5">
                      <VerifiedBadge size={22} />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-base truncate">{user?.display_name || user?.full_name || t('nav.user')}</p>
                      <VerifiedBadge size={20} />
                    </div>
                    <p className="text-xs text-muted-foreground truncate">{user?.email || ''}</p>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span className="text-[10px] bg-orange-500/15 text-orange-400 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                        <VerifiedBadge size={12} />
                        {t('settings.verifiedAccount')}
                      </span>
                      <span className="text-[10px] bg-orange-500/15 text-orange-400 px-2 py-0.5 rounded-full font-medium">{user?.role || 'admin'}</span>
                    </div>
                  </div>
                </div>

                <h3 className="text-sm font-medium">{t('settings.profileSettings')}</h3>
                {/* Profile picture upload */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">{t('settings.profilePicture')}</label>
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-500 to-blue-500 flex items-center justify-center text-white text-lg font-bold overflow-hidden flex-shrink-0">
                      {user?.avatar_url ? <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" /> : (user?.display_name || user?.full_name)?.charAt(0)?.toUpperCase() || t('nav.user').charAt(0)}
                    </div>
                    <input type="file" ref={avatarInputRef} accept="image/*" className="hidden" onChange={handleAvatarUpload} />
                    <Button variant="outline" size="sm" onClick={() => avatarInputRef.current?.click()} disabled={avatarUploading} className="h-8 text-xs gap-1.5">
                      {avatarUploading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Camera className="w-3 h-3" />}
                      {avatarUploading ? t('settings.uploading') : t('settings.changePhoto')}
                    </Button>
                    {user?.avatar_url && (
                      <Button variant="ghost" size="sm" onClick={handleRemoveAvatar} className="h-8 text-xs">{t('settings.remove')}</Button>
                    )}
                  </div>
                </div>
                {/* Display name */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">{t('settings.displayName')}</label>
                  <Input
                    value={displayName}
                    onChange={e => setDisplayName(e.target.value)}
                    onBlur={handleDisplayNameSave}
                    onKeyDown={e => { if (e.key === 'Enter') e.target.blur(); }}
                    placeholder={t('settings.enterName')}
                    className="bg-muted/30 border-border/50"
                  />
                  <p className="text-[10px] text-muted-foreground/50 mt-1">{t('settings.nameDesc')}</p>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">{t('settings.email')}</label>
                  <Input value={user?.email || ''} disabled className="bg-muted/30 border-border/50" />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">{t('settings.language')}</label>
                  <Select value={settings.language} onValueChange={v => update('language', v)}>
                    <SelectTrigger className="bg-muted/30 border-border/50"><SelectValue /></SelectTrigger>
                    <SelectContent className="max-h-[300px]">
                      {WORLD_LANGUAGES.map(lang => (
                        <SelectItem key={lang.code} value={lang.code}>{lang.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="ai">
              <div className="glass-card rounded-xl p-6 space-y-5">
                <h3 className="text-sm font-medium mb-4">{t('settings.aiPreferences')}</h3>
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">{t('settings.aiEngine')}</label>
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-orange-500/5 border border-orange-500/20">
                    <span className="text-base">🔗</span>
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-orange-400">{NEXUS_NAME}</p>
                      <p className="text-[10px] text-muted-foreground">{t('settings.nexusDesc')}</p>
                    </div>
                    <BadgeCheck className="w-3.5 h-3.5 text-green-400" />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">{t('settings.streamResponses')}</p>
                    <p className="text-xs text-muted-foreground">{t('settings.streamDesc')}</p>
                  </div>
                  <Switch checked={settings.stream_responses} onCheckedChange={v => update('stream_responses', v)} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">{t('settings.showTokens')}</p>
                    <p className="text-xs text-muted-foreground">{t('settings.tokensDesc')}</p>
                  </div>
                  <Switch checked={settings.show_token_count} onCheckedChange={v => update('show_token_count', v)} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">{t('settings.sendOnEnter')}</p>
                    <p className="text-xs text-muted-foreground">{t('settings.sendDesc')}</p>
                  </div>
                  <Switch checked={settings.send_on_enter} onCheckedChange={v => update('send_on_enter', v)} />
                </div>
                {/* Nexus Mode */}
                <div className="border-t border-border/50 pt-4 mt-2">
                  <label className="text-xs text-muted-foreground mb-1.5 block">{t('settings.nexusMode')}</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => update('nexus_mode', 'deep')}
                      className={`p-3 rounded-lg border text-left transition-all ${settings.nexus_mode === 'deep' ? 'border-orange-500 bg-orange-500/10' : 'border-border/50 hover:border-border'}`}
                    >
                      <p className="text-sm font-medium flex items-center gap-1.5">🧠 {t('settings.deepThinking')}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">{t('settings.deepDesc')}</p>
                    </button>
                    <button
                      onClick={() => update('nexus_mode', 'save')}
                      className={`p-3 rounded-lg border text-left transition-all ${settings.nexus_mode === 'save' ? 'border-blue-500 bg-blue-500/10' : 'border-border/50 hover:border-border'}`}
                    >
                      <p className="text-sm font-medium flex items-center gap-1.5">⚡ {t('settings.saveData')}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">{t('settings.saveDesc')}</p>
                    </button>
                  </div>
                </div>
                {/* Voice */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">{t('settings.voice')}</label>
                  <Select value={settings.voice} onValueChange={v => update('voice', v)}>
                    <SelectTrigger className="bg-muted/30 border-border/50"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {AI_VOICES.map(v => (
                        <SelectItem key={v.id} value={v.id}>{v.name} — {v.desc}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {/* Bloxy Nexus — no config needed */}
                <div className="border-t border-border/50 pt-4 mt-2">
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-orange-500/5 border border-orange-500/20">
                    <span className="text-base">🔗</span>
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-orange-400">{NEXUS_NAME}</p>
                      <p className="text-[10px] text-muted-foreground">{t('settings.nexusDesc')}</p>
                    </div>
                    <BadgeCheck className="w-3.5 h-3.5 text-green-400" />
                  </div>
                  <p className="text-[10px] text-muted-foreground/60 mt-2">{t('chat.noKeysNeeded')}</p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="appearance">
              <div className="glass-card rounded-xl p-6 space-y-5">
                <h3 className="text-sm font-medium mb-4">{t('settings.appearance')}</h3>
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">{t('settings.theme')}</label>
                  <Select value={settings.theme} onValueChange={v => update('theme', v)}>
                    <SelectTrigger className="bg-muted/30 border-border/50"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="dark">{t('settings.dark')}</SelectItem>
                      <SelectItem value="light">{t('settings.light')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="border-t border-border/50 pt-4">
                  <h4 className="text-xs font-medium mb-2">{t('settings.deviceInfo')}</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-muted/20">
                      <p className="text-muted-foreground text-[10px]">{t('settings.device')}</p>
                      <p className="font-medium capitalize">{(() => { try { return getDeviceInfo().device; } catch { return 'desktop'; } })()}</p>
                    </div>
                    <div className="p-2 rounded-lg bg-muted/20">
                      <p className="text-muted-foreground text-[10px]">{t('settings.browser')}</p>
                      <p className="font-medium">{(() => { try { return getDeviceInfo().browser; } catch { return 'Unknown'; } })()}</p>
                    </div>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-2">{t('settings.deviceDesc')}</p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="history">
              <div className="glass-card rounded-xl p-4 sm:p-6">
                <h3 className="text-sm font-medium mb-4 flex items-center gap-2"><History className="w-4 h-4 text-orange-400" />{t('settings.chatHistory')}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="sm:col-span-1 space-y-1 max-h-[400px] overflow-y-auto">
                    {historyConvs.length === 0 && <p className="text-xs text-muted-foreground">{t('settings.noConversations')}</p>}
                    {historyConvs.map(c => (
                      <div
                        key={c.id}
                        className={`group flex items-center gap-2 p-2.5 rounded-lg cursor-pointer transition-all ${selectedConv === c.id ? 'bg-orange-500/10 text-orange-400' : 'hover:bg-muted/30'}`}
                        onClick={() => loadConvMessages(c.id)}
                      >
                        <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-50" />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium truncate">{c.title}</p>
                          <p className="text-[10px] text-muted-foreground">{c.message_count} msgs · {new Date(c.updated_date || c.created_date).toLocaleDateString()}</p>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteHistoryConv(c.id); }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-destructive/20 text-muted-foreground hover:text-red-400 flex-shrink-0"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="sm:col-span-2 space-y-2 max-h-[400px] overflow-y-auto">
                    {historyMsgs.length === 0 && <p className="text-xs text-muted-foreground">{t('settings.selectConv')}</p>}
                    {historyMsgs.map(m => (
                      <div key={m.id} className={`p-3 rounded-lg ${m.role === 'user' ? 'bg-blue-500/5' : 'bg-muted/20'}`}>
                        <p className={`text-[10px] font-medium mb-1 ${m.role === 'user' ? 'text-blue-400' : 'text-orange-400'}`}>{m.role === 'user' ? t('chat.you') : t('settings.bloxyAI')}</p>
                        <p className="text-xs text-muted-foreground whitespace-pre-wrap break-words">{m.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4 p-3 rounded-lg bg-muted/20 border border-border/30">
                  <div>
                    <p className="text-xs font-medium">{t('settings.pauseHistory')}</p>
                    <p className="text-[10px] text-muted-foreground">{t('settings.pauseDesc')}</p>
                  </div>
                  <Switch checked={settings.history_paused || false} onCheckedChange={v => update('history_paused', v)} />
                </div>
                <div className="flex gap-2 mt-3">
                  <Button variant="outline" size="sm" onClick={loadHistory} className="h-8 text-xs gap-1.5 flex-1">
                    <History className="w-3.5 h-3.5" />{t('common.refresh')}
                  </Button>
                  <Button variant="destructive" size="sm" onClick={handleClearAllHistory} className="h-8 text-xs gap-1.5 flex-1">
                    <Trash2 className="w-3.5 h-3.5" />{t('settings.deleteAll')}
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="privacy">
            <div className="glass-card rounded-xl p-6 space-y-5">
              <h3 className="text-sm font-medium mb-4">{t('settings.privacySecurity')}</h3>
              <p className="text-xs text-muted-foreground">{t('settings.privacyDesc')}</p>
              <div className="glass-card rounded-lg p-4">
                <p className="text-xs font-medium mb-1">{t('settings.dataRetention')}</p>
                <p className="text-[10px] text-muted-foreground">{t('settings.retentionDesc')}</p>
              </div>
              <div className="space-y-3">
                <h4 className="text-sm font-medium flex items-center gap-1.5"><Download className="w-3.5 h-3.5 text-orange-400" />{t('settings.localBackup')}</h4>
                <p className="text-xs text-muted-foreground">{t('settings.backupDesc')}</p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <Button variant="outline" size="sm" onClick={handleExportChats} disabled={exporting === 'chats'} className="h-9 text-xs gap-1.5">
                    {exporting === 'chats' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                    {exporting === 'chats' ? t('settings.exporting') : t('settings.exportChats')}
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleExportPrompts} disabled={exporting === 'prompts'} className="h-9 text-xs gap-1.5">
                    {exporting === 'prompts' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                    {exporting === 'prompts' ? t('settings.exporting') : t('settings.exportPrompts')}
                  </Button>
                </div>
              </div>
            </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
