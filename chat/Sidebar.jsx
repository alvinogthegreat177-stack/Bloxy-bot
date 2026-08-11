import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  MessageSquare, Plus, Search, Star, Folder, Settings, LayoutDashboard,
  BookOpen, Trash2, MoreHorizontal, ChevronDown, ChevronRight, X, Menu,
  Zap, Shield, HelpCircle, LogOut, Pencil, Check
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import BloxyLogo from './BloxyLogo';
import { base44 } from '@/api/base44Client';
import VerifiedBadge from '@/components/VerifiedBadge';
import { isVerifiedUser } from '@/lib/verifiedUsers';
import { useLanguage } from '@/lib/LanguageContext';

export default function Sidebar({
  conversations, onNewChat, onSelectChat, activeConversationId,
  onDeleteChat, onToggleFavorite, onRenameChat, isMobileOpen, onCloseMobile, user
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFavorites, setShowFavorites] = useState(false);
  const [renameId, setRenameId] = useState(null);
  const [renameText, setRenameText] = useState('');
  const location = useLocation();
  const { t } = useLanguage();

  const startRename = (c) => {
    setRenameId(c.id);
    setRenameText(c.title);
  };

  const commitRename = () => {
    if (renameText.trim() && onRenameChat) onRenameChat(renameId, renameText.trim());
    setRenameId(null);
    setRenameText('');
  };

  const filtered = conversations.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const favorites = filtered.filter(c => c.is_favorite);
  const recent = filtered.filter(c => !c.is_favorite);

  const groupByDate = (convs) => {
    const now = new Date();
    const today = [];
    const week = [];
    const month = [];
    const older = [];
    convs.forEach(c => {
      const d = new Date(c.created_date);
      const diff = (now - d) / (1000 * 60 * 60 * 24);
      if (diff < 1) today.push(c);
      else if (diff < 7) week.push(c);
      else if (diff < 30) month.push(c);
      else older.push(c);
    });
    return { today, week, month, older };
  };

  const groups = groupByDate(recent);

  const navItems = [
    { icon: MessageSquare, label: t('nav.chat'), path: '/' },
    { icon: Search, label: t('nav.search'), path: '/search' },
    { icon: BookOpen, label: t('nav.knowledge'), path: '/knowledge' },
    { icon: Folder, label: t('nav.library'), path: '/library' },
    { icon: LayoutDashboard, label: t('nav.dashboard'), path: '/dashboard' },
    { icon: Settings, label: t('common.settings'), path: '/settings' },
  ];

  const renderGroup = (label, items) => {
    if (items.length === 0) return null;
    return (
      <div key={label} className="mb-3">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground/50 px-3 mb-1 font-medium">{label}</p>
        {items.map(c => (
          <div
            key={c.id}
            className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all text-sm ${
              c.id === activeConversationId
                ? 'bg-orange-500/10 text-orange-400'
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            }`}
            onClick={() => { onSelectChat(c.id); onCloseMobile?.(); }}
          >
            <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-50" />
            {renameId === c.id ? (
              <input
                autoFocus
                value={renameText}
                onChange={e => setRenameText(e.target.value)}
                onClick={e => e.stopPropagation()}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); commitRename(); } if (e.key === 'Escape') { setRenameId(null); setRenameText(''); } }}
                className="flex-1 bg-muted/60 rounded text-xs px-1 py-0.5 outline-none border border-orange-500/40"
              />
            ) : (
              <span className="truncate flex-1 text-xs">{c.title}</span>
            )}
            {renameId === c.id ? (
              <button className="p-0.5 rounded hover:bg-muted text-green-400" onClick={(e) => { e.stopPropagation(); commitRename(); }}>
                <Check className="w-3 h-3" />
              </button>
            ) : (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-muted" onClick={e => e.stopPropagation()}>
                  <MoreHorizontal className="w-3 h-3" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-36">
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); startRename(c); }}>
                  <Pencil className="w-3 h-3 mr-2" />
                  {t('nav.rename')}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onToggleFavorite(c.id, !c.is_favorite); }}>
                  <Star className="w-3 h-3 mr-2" />
                  {c.is_favorite ? t('nav.unfavorite') : t('nav.favorite')}
                </DropdownMenuItem>
                <DropdownMenuItem className="text-red-400" onClick={(e) => { e.stopPropagation(); onDeleteChat(c.id); }}>
                  <Trash2 className="w-3 h-3 mr-2" />
                  {t('common.delete')}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`
      relative inset-y-0 left-0 z-50 w-64 bg-sidebar border-r border-sidebar-border flex flex-col h-screen overflow-y-auto flex-shrink-0
    `}>
      {/* Header */}
      <div className="p-4 flex items-center justify-between border-b border-border/50">
        <BloxyLogo size={28} />
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg" onClick={onNewChat}>
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="p-3">
        <div className="flex items-center gap-2 bg-muted/40 rounded-lg px-3 py-2">
          <Search className="w-3.5 h-3.5 text-muted-foreground/50" />
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder={t('nav.searchChats')}
            className="bg-transparent border-none outline-none text-xs flex-1 placeholder:text-muted-foreground/40"
          />
        </div>
      </div>

      {/* Navigation */}
      <div className="px-3 mb-2">
        {navItems.map(item => (
          <Link
            key={item.path}
            to={item.path}
            onClick={onCloseMobile}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all ${
              location.pathname === item.path
                ? 'bg-orange-500/10 text-orange-400'
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            }`}
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </Link>
        ))}
      </div>

      <div className="h-px bg-border/50 mx-3" />

      {/* Conversations */}
      <ScrollArea className="flex-1 px-2 py-2">
        {favorites.length > 0 && (
          <div className="mb-3">
            <button
              onClick={() => setShowFavorites(!showFavorites)}
              className="flex items-center gap-1.5 px-3 py-1 text-[10px] uppercase tracking-wider text-orange-400/70 font-medium w-full hover:text-orange-400"
            >
              <Star className="w-3 h-3" />
              {t('nav.favorites')}
              {showFavorites ? <ChevronDown className="w-3 h-3 ml-auto" /> : <ChevronRight className="w-3 h-3 ml-auto" />}
            </button>
            {showFavorites && favorites.map(c => (
              <div
                key={c.id}
                className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all text-sm ${
                  c.id === activeConversationId ? 'bg-orange-500/10 text-orange-400' : 'text-muted-foreground hover:bg-muted/50'
                }`}
                onClick={() => { onSelectChat(c.id); onCloseMobile?.(); }}
              >
                <Star className="w-3 h-3 text-orange-400/50 flex-shrink-0" />
                <span className="truncate flex-1 text-xs">{c.title}</span>
              </div>
            ))}
          </div>
        )}
        {renderGroup(t('nav.today'), groups.today)}
        {renderGroup(t('nav.thisWeek'), groups.week)}
        {renderGroup(t('nav.thisMonth'), groups.month)}
        {renderGroup(t('nav.older'), groups.older)}
      </ScrollArea>

      {/* User */}
      <div className="p-3 border-t border-border/50">
        <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-muted/30 cursor-pointer transition-all">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold overflow-hidden">
            {user?.avatar_url ? <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" /> : (user?.display_name || user?.full_name)?.charAt(0)?.toUpperCase() || t('nav.user').charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1">
              <p className="text-xs font-medium truncate">{user?.display_name || user?.full_name || t('nav.user')}</p>
              {isVerifiedUser(user?.email) && <VerifiedBadge size={14} />}
            </div>
            <p className="text-[10px] text-muted-foreground truncate">{user?.email || ''}</p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="p-1 rounded hover:bg-muted">
                <MoreHorizontal className="w-3.5 h-3.5 text-muted-foreground" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              <DropdownMenuItem asChild><Link to="/settings"><Settings className="w-3 h-3 mr-2" />{t('common.settings')}</Link></DropdownMenuItem>
              <DropdownMenuItem asChild><Link to="/admin"><Shield className="w-3 h-3 mr-2" />{t('nav.admin')}</Link></DropdownMenuItem>
              <DropdownMenuItem onClick={() => base44.auth.logout('/')} className="text-red-400">
                <LogOut className="w-3 h-3 mr-2" />{t('nav.signOut')}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  );
}
