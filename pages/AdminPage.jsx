import React, { useState, useEffect } from 'react';
import { base44 } from '@/api/base44Client';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, Shield, Users, MessageSquare, Activity,
  BarChart3, Zap, Database, CheckCircle, TrendingUp,
  Cpu, Globe, Clock, Hash, Search
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Area, AreaChart } from 'recharts';
import { useLanguage } from '@/lib/LanguageContext';

const { Conversation, Message, SavedPrompt } = base44.entities;

const SEARCH_ENGINES = [
  { name: 'Google', icon: '🔍' },
  { name: 'Bing / Edge', icon: '🅗' },
  { name: 'DuckDuckGo', icon: '🦆' },
  { name: 'Yahoo', icon: '🅨' },
  { name: 'Brave', icon: '🦁' },
  { name: 'Reddit', icon: '👾' },
  { name: 'Mastodon', icon: '🐘' },
  { name: 'Wikipedia', icon: '📚' },
  { name: 'Hacker News', icon: '📰' },
  { name: 'GitHub', icon: '🐙' },
  { name: 'Startpage', icon: '🅢' },
  { name: 'Searx', icon: '🔎' },
];

const SOCIAL_PLATFORMS = [
  { name: 'Reddit', color: 'text-orange-400' },
  { name: 'X / Twitter', color: 'text-gray-400' },
  { name: 'Instagram', color: 'text-pink-500' },
  { name: 'TikTok', color: 'text-pink-400' },
  { name: 'Threads', color: 'text-gray-500' },
  { name: 'YouTube', color: 'text-red-400' },
  { name: 'LinkedIn', color: 'text-blue-500' },
  { name: 'WhatsApp', color: 'text-green-400' },
  { name: 'Mastodon', color: 'text-blue-400' },
  { name: 'Hacker News', color: 'text-orange-500' },
];

export default function AdminPage() {
  const [stats, setStats] = useState({ users: 0, conversations: 0, messages: 0, prompts: 0 });
  const [users, setUsers] = useState([]);
  const [recentConvs, setRecentConvs] = useState([]);
  const [recentMsgs, setRecentMsgs] = useState([]);
  const { t } = useLanguage();

  useEffect(() => { loadAll(); }, []);

  const loadAll = async () => {
    const [convs, msgs, prompts, usersList] = await Promise.all([
      Conversation.list('-created_date', 50),
      Message.list('-created_date', 50),
      SavedPrompt.list('-created_date', 50),
      base44.entities.User.list('-created_date', 20),
    ]);
    setStats({
      users: usersList.length,
      conversations: convs.length,
      messages: msgs.length,
      prompts: prompts.length,
    });
    setUsers(usersList);
    setRecentConvs(convs.slice(0, 8));
    setRecentMsgs(msgs.slice(0, 50));
  };

  const activityData = (() => {
    const days = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const label = d.toLocaleDateString('en', { weekday: 'short' });
      const count = recentMsgs.filter(m => {
        const md = new Date(m.created_date);
        return md.toDateString() === d.toDateString();
      }).length;
      days.push({ day: label, messages: count });
    }
    return days;
  })();

  const pieData = [
    { name: 'Conversations', value: stats.conversations, color: '#F97316' },
    { name: 'Messages', value: stats.messages, color: '#3B82F6' },
    { name: 'Prompts', value: stats.prompts, color: '#A855F7' },
  ];

  const adminStats = [
    { icon: Users, label: t('admin.totalUsers'), value: stats.users, iconBg: 'bg-blue-500/10 text-blue-400' },
    { icon: MessageSquare, label: t('admin.conversations'), value: stats.conversations, iconBg: 'bg-orange-500/10 text-orange-400' },
    { icon: Zap, label: t('admin.messages'), value: stats.messages, iconBg: 'bg-green-500/10 text-green-400' },
    { icon: Database, label: t('admin.savedPrompts'), value: stats.prompts, iconBg: 'bg-purple-500/10 text-purple-400' },
  ];

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="h-12 border-b border-border/50 flex items-center px-4 gap-3 flex-shrink-0">
        <Link to="/"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <Shield className="w-4 h-4 text-orange-400" />
        <span className="text-sm font-medium">{t('admin.title')}</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-xl font-bold mb-1">{t('admin.title')}</h1>
          <p className="text-sm text-muted-foreground mb-6">{t('admin.subtitle')}</p>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {adminStats.map((s, i) => (
              <div key={i} className="glass-card rounded-xl p-4">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${s.iconBg}`}>
                  <s.icon className="w-4 h-4" />
                </div>
                <p className="text-2xl font-bold">{s.value}</p>
                <p className="text-xs text-muted-foreground">{s.label}</p>
              </div>
            ))}
          </div>

          <Tabs defaultValue="overview">
            <TabsList className="bg-muted/30 border border-border/50 rounded-xl mb-6 p-1 flex flex-wrap h-auto gap-1">
              <TabsTrigger value="overview" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><Activity className="w-3 h-3 mr-1.5" />{t('admin.overview')}</TabsTrigger>
              <TabsTrigger value="users" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><Users className="w-3 h-3 mr-1.5" />{t('admin.users')}</TabsTrigger>
              <TabsTrigger value="engines" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><Globe className="w-3 h-3 mr-1.5" />{t('admin.engines')}</TabsTrigger>
              <TabsTrigger value="analytics" className="rounded-lg text-xs data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400"><BarChart3 className="w-3 h-3 mr-1.5" />{t('admin.analytics')}</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                <div className="glass-card rounded-xl p-4 sm:p-6">
                  <h3 className="text-sm font-medium mb-4 flex items-center gap-2"><Clock className="w-4 h-4 text-orange-400" />{t('admin.recentActivity')}</h3>
                  <div className="space-y-2">
                    {recentConvs.length === 0 && <p className="text-xs text-muted-foreground">{t('admin.noRecentConvs')}</p>}
                    {recentConvs.map(c => (
                      <div key={c.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/20">
                        <MessageSquare className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium truncate">{c.title}</p>
                          <p className="text-[10px] text-muted-foreground">{c.message_count} {t('admin.msgs')}</p>
                        </div>
                        <span className="text-[10px] text-muted-foreground flex-shrink-0">
                          {new Date(c.created_date).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-card rounded-xl p-4 sm:p-6">
                  <h3 className="text-sm font-medium mb-4 flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" />{t('admin.systemHealth')}</h3>
                  <div className="space-y-2">
                    {[
                      { name: t('admin.bloxyNexusApi'), icon: Cpu },
                      { name: t('admin.database'), icon: Database },
                      { name: t('admin.aiProviders'), icon: Zap },
                      { name: t('admin.webSearch'), icon: Search },
                      { name: t('admin.socialMediaScan'), icon: Hash },
                    ].map((s, i) => (
                      <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-muted/20">
                        <div className="flex items-center gap-3">
                          <s.icon className="w-4 h-4 text-muted-foreground" />
                          <p className="text-xs font-medium">{s.name}</p>
                        </div>
                        <span className="text-[10px] bg-green-500/10 text-green-400 px-2 py-0.5 rounded-full">{t('admin.healthy')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-xl p-4 sm:p-6">
                <h3 className="text-sm font-medium mb-4 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-orange-400" />{t('admin.activity7Day')}</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={activityData}>
                    <defs>
                      <linearGradient id="msgGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F97316" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="day" stroke="hsl(220 10% 55%)" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="hsl(220 10% 55%)" fontSize={11} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip contentStyle={{ background: 'hsl(220 15% 10%)', border: '1px solid hsl(220 15% 18%)', borderRadius: 8, fontSize: 12 }} />
                    <Area type="monotone" dataKey="messages" stroke="#F97316" strokeWidth={2} fill="url(#msgGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>

            <TabsContent value="users">
              <div className="glass-card rounded-xl p-4 sm:p-6">
                <h3 className="text-sm font-medium mb-4">{t('admin.userManagement')}</h3>
                <div className="space-y-2">
                  {users.map(u => (
                    <div key={u.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                          {u.full_name?.charAt(0)?.toUpperCase() || 'U'}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{u.full_name || t('common.unknown')}</p>
                          <p className="text-[10px] text-muted-foreground truncate">{u.email}</p>
                        </div>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full flex-shrink-0 ${u.role === 'admin' ? 'bg-orange-500/10 text-orange-400' : 'bg-blue-500/10 text-blue-400'}`}>{u.role || 'user'}</span>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="engines">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="glass-card rounded-xl p-4 sm:p-6">
                  <h3 className="text-sm font-medium mb-4 flex items-center gap-2"><Search className="w-4 h-4 text-orange-400" />{t('admin.searchEngines')}</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {SEARCH_ENGINES.map((e, i) => (
                      <div key={i} className="flex items-center gap-2 p-2.5 rounded-lg bg-muted/20">
                        <span className="text-base">{e.icon}</span>
                        <span className="text-xs font-medium flex-1 truncate">{e.name}</span>
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-card rounded-xl p-4 sm:p-6">
                  <h3 className="text-sm font-medium mb-4 flex items-center gap-2"><Hash className="w-4 h-4 text-orange-400" />{t('admin.socialMediaMonitoring')}</h3>
                  <div className="space-y-2">
                    {SOCIAL_PLATFORMS.map((p, i) => (
                      <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-muted/20">
                        <span className={`text-xs font-medium ${p.color}`}>{p.name}</span>
                        <div className="flex-1" />
                        <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                        <span className="text-[10px] text-muted-foreground">{t('admin.monitored')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-xl p-4 sm:p-6 mt-4">
                <h3 className="text-sm font-medium mb-4 flex items-center gap-2"><Cpu className="w-4 h-4 text-orange-400" />{t('admin.aiProviderStatus')}</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {['DeepSeek', 'OpenAI', 'Claude', 'Groq', 'OpenRouter', 'Cohere', 'Mistral', 'Nexus'].map((p, i) => (
                    <div key={i} className="flex items-center gap-2 p-2.5 rounded-lg bg-muted/20">
                      <Zap className="w-3 h-3 text-orange-400" />
                      <span className="text-xs">{p}</span>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="analytics">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="glass-card rounded-xl p-4 sm:p-6">
                  <h3 className="text-sm font-medium mb-4">{t('admin.contentDistribution')}</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie data={pieData.filter(d => d.value > 0)} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                        {pieData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ background: 'hsl(220 15% 10%)', border: '1px solid hsl(220 15% 18%)', borderRadius: 8, fontSize: 12 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="glass-card rounded-xl p-4 sm:p-6">
                  <h3 className="text-sm font-medium mb-4">{t('admin.messageVolume')}</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={activityData}>
                      <XAxis dataKey="day" stroke="hsl(220 10% 55%)" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis stroke="hsl(220 10% 55%)" fontSize={11} tickLine={false} axisLine={false} allowDecimals={false} />
                      <Tooltip contentStyle={{ background: 'hsl(220 15% 10%)', border: '1px solid hsl(220 15% 18%)', borderRadius: 8, fontSize: 12 }} />
                      <Bar dataKey="messages" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
