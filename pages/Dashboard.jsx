import React, { useState, useEffect } from 'react';
import { base44 } from '@/api/base44Client';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, MessageSquare, Zap, Star, TrendingUp,
  BarChart3, Activity, Clock, Users
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { useLanguage } from '@/lib/LanguageContext';

const { Conversation, Message } = base44.entities;

export default function Dashboard() {
  const [stats, setStats] = useState({ conversations: 0, messages: 0, favorites: 0 });
  const [chartData, setChartData] = useState([]);
  const [recentChats, setRecentChats] = useState([]);
  const { t } = useLanguage();

  useEffect(() => { loadStats(); }, []);

  const loadStats = async () => {
    const convs = await Conversation.list('-created_date', 50);
    const msgs = await Message.list('-created_date', 50);

    setStats({
      conversations: convs.length,
      messages: msgs.length,
      favorites: convs.filter(c => c.is_favorite).length,
    });

    setRecentChats(convs.slice(0, 5));

    // Build chart data from last 7 days
    const days = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const label = d.toLocaleDateString('en', { weekday: 'short' });
      const dayStr = d.toISOString().split('T')[0];
      const count = msgs.filter(m => m.created_date?.startsWith(dayStr)).length;
      days.push({ day: label, messages: count });
    }
    setChartData(days);
  };

  const statCards = [
    { icon: MessageSquare, label: t('admin.conversations'), value: stats.conversations, color: 'from-orange-500 to-orange-600', iconBg: 'bg-orange-500/10 text-orange-400' },
    { icon: Zap, label: t('admin.messages'), value: stats.messages, color: 'from-blue-500 to-blue-600', iconBg: 'bg-blue-500/10 text-blue-400' },
    { icon: Star, label: t('nav.favorites'), value: stats.favorites, color: 'from-yellow-500 to-yellow-600', iconBg: 'bg-yellow-500/10 text-yellow-400' },
    { icon: Activity, label: t('dashboard.activeToday'), value: chartData.length > 0 ? chartData[chartData.length - 1]?.messages || 0 : 0, color: 'from-green-500 to-green-600', iconBg: 'bg-green-500/10 text-green-400' },
  ];

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="h-12 border-b border-border/50 flex items-center px-4 gap-3 flex-shrink-0">
        <Link to="/"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <BarChart3 className="w-4 h-4 text-orange-400" />
        <span className="text-sm font-medium">{t('nav.dashboard')}</span>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-xl font-bold mb-1">{t('nav.dashboard')}</h1>
          <p className="text-sm text-muted-foreground mb-6">{t('dashboard.subtitle')}</p>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {statCards.map((s, i) => (
              <div key={i} className="glass-card rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${s.iconBg}`}>
                    <s.icon className="w-4 h-4" />
                  </div>
                </div>
                <p className="text-2xl font-bold">{s.value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 glass-card rounded-xl p-5">
              <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-orange-400" />
                {t('dashboard.messageActivity')}
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="msgGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#F97316" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#F97316" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#666' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#666' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: 'hsl(220 15% 10%)', border: '1px solid hsl(220 15% 18%)', borderRadius: 8, fontSize: 12 }}
                  />
                  <Area type="monotone" dataKey="messages" stroke="#F97316" fill="url(#msgGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="glass-card rounded-xl p-5">
              <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-400" />
                {t('dashboard.recentChats')}
              </h3>
              <div className="space-y-2">
                {recentChats.map(c => (
                  <Link to="/" key={c.id} className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-muted/30 transition-all">
                    <MessageSquare className="w-3.5 h-3.5 text-muted-foreground/50" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{c.title}</p>
                      <p className="text-[10px] text-muted-foreground truncate">{c.last_message_preview || t('dashboard.noMessages')}</p>
                    </div>
                    {c.is_favorite && <Star className="w-3 h-3 text-orange-400/50" />}
                  </Link>
                ))}
                {recentChats.length === 0 && (
                  <p className="text-xs text-muted-foreground/50 text-center py-4">{t('dashboard.noConversationsYet')}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
