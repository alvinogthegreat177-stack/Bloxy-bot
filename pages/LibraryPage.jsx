import React, { useState, useEffect } from 'react';
import { base44 } from '@/api/base44Client';
import { Plus, Search, Trash2, Edit2, Copy, Check, BookMarked, Tag, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import { Link } from 'react-router-dom';
import { useLanguage } from '@/lib/LanguageContext';

const { SavedPrompt } = base44.entities;

const CATEGORIES = [
  { value: 'all', labelKey: 'library.all' },
  { value: 'general', labelKey: 'library.general' },
  { value: 'coding', labelKey: 'library.coding' },
  { value: 'writing', labelKey: 'library.writing' },
  { value: 'research', labelKey: 'library.research' },
  { value: 'planning', labelKey: 'library.planning' },
  { value: 'creative', labelKey: 'library.creative' },
];

const CATEGORY_COLORS = {
  general: 'bg-gray-500/10 text-gray-400',
  coding: 'bg-blue-500/10 text-blue-400',
  writing: 'bg-purple-500/10 text-purple-400',
  research: 'bg-teal-500/10 text-teal-400',
  planning: 'bg-orange-500/10 text-orange-400',
  creative: 'bg-pink-500/10 text-pink-400',
};

const DEFAULT_PROMPTS = [
  { title: 'Senior Developer', category: 'coding', content: 'You are a senior software engineer with 10+ years of experience. Write clean, efficient, well-commented code. Always explain your approach, mention potential edge cases, and suggest improvements.' },
  { title: 'Academic Researcher', category: 'research', content: 'You are an academic researcher. Provide thorough, evidence-based answers with citations where possible. Use precise language, acknowledge uncertainty, and present multiple perspectives on complex topics.' },
  { title: 'Creative Writer', category: 'creative', content: 'You are a creative writing assistant. Be imaginative, use vivid descriptive language, and help craft compelling narratives. Focus on character development, pacing, and emotional resonance.' },
  { title: 'Project Planner', category: 'planning', content: 'You are a project management expert. Break down tasks into actionable steps, identify dependencies and risks, suggest timelines, and provide structured plans with clear milestones.' },
  { title: 'Copywriter', category: 'writing', content: 'You are a professional copywriter. Write persuasive, engaging content tailored to the target audience. Focus on clear value propositions, strong calls to action, and compelling headlines.' },
  { title: 'Explain Like I\'m 5', category: 'general', content: 'Explain everything in very simple terms that a child could understand. Use analogies, avoid jargon, keep sentences short, and use relatable everyday examples.' },
];

function PromptForm({ initial, onSave, onClose }) {
  const { t } = useLanguage();
  const [title, setTitle] = useState(initial?.title || '');
  const [content, setContent] = useState(initial?.content || '');
  const [category, setCategory] = useState(initial?.category || 'general');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!title.trim() || !content.trim()) return;
    setSaving(true);
    await onSave({ title: title.trim(), content: content.trim(), category });
    setSaving(false);
  };

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label>{t('library.titleLabel')}</Label>
        <Input value={title} onChange={e => setTitle(e.target.value)} placeholder={t('library.titlePlaceholder')} className="h-10" />
      </div>
      <div className="space-y-1.5">
        <Label>{t('library.categoryLabel')}</Label>
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.filter(c => c.value !== 'all').map(c => (
            <button
              key={c.value}
              onClick={() => setCategory(c.value)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                category === c.value
                  ? 'border-orange-500 bg-orange-500/10 text-orange-400'
                  : 'border-border text-muted-foreground hover:border-muted-foreground'
              }`}
            >
              {t(c.labelKey)}
            </button>
          ))}
        </div>
      </div>
      <div className="space-y-1.5">
        <Label>{t('library.instructionsLabel')}</Label>
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder={t('library.instructionsPlaceholder')}
          rows={6}
          className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm resize-none outline-none focus:border-orange-500/50 transition-colors placeholder:text-muted-foreground/40"
        />
      </div>
      <DialogFooter>
        <Button variant="ghost" onClick={onClose}>{t('common.cancel')}</Button>
        <Button onClick={handleSave} disabled={saving || !title.trim() || !content.trim()} className="bg-orange-500 hover:bg-orange-600 text-white">
          {saving ? t('library.saving') : t('library.saveInstruction')}
        </Button>
      </DialogFooter>
    </div>
  );
}

export default function LibraryPage() {
  const [prompts, setPrompts] = useState([]);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const { t } = useLanguage();

  useEffect(() => { loadPrompts(); }, []);

  const loadPrompts = async () => {
    setLoading(true);
    const data = await SavedPrompt.list('-updated_date', 100);
    setPrompts(data);
    setLoading(false);
  };

  const handleSave = async (data) => {
    if (editingPrompt) {
      await SavedPrompt.update(editingPrompt.id, data);
    } else {
      await SavedPrompt.create(data);
    }
    setShowForm(false);
    setEditingPrompt(null);
    loadPrompts();
  };

  const handleDelete = async (id) => {
    await SavedPrompt.delete(id);
    setPrompts(prev => prev.filter(p => p.id !== id));
  };

  const handleEdit = (prompt) => {
    setEditingPrompt(prompt);
    setShowForm(true);
  };

  const handleCopy = (prompt) => {
    navigator.clipboard.writeText(prompt.content);
    setCopiedId(prompt.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSeedDefaults = async () => {
    for (const p of DEFAULT_PROMPTS) {
      await SavedPrompt.create(p);
    }
    loadPrompts();
  };

  const filtered = prompts.filter(p => {
    const matchCat = activeCategory === 'all' || p.category === activeCategory;
    const matchSearch = !search || p.title.toLowerCase().includes(search.toLowerCase()) || p.content.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="border-b border-border/50 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-muted-foreground hover:text-foreground text-sm">{t('library.backToChat')}</Link>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-2">
            <BookMarked className="w-5 h-5 text-orange-400" />
            <h1 className="text-lg font-semibold">{t('library.title')}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {prompts.length === 0 && !loading && (
            <Button variant="outline" size="sm" onClick={handleSeedDefaults} className="text-xs gap-1.5">
              <Zap className="w-3.5 h-3.5" /> {t('library.addStarter')}
            </Button>
          )}
          <Button size="sm" onClick={() => { setEditingPrompt(null); setShowForm(true); }} className="bg-orange-500 hover:bg-orange-600 text-white gap-1.5">
            <Plus className="w-4 h-4" /> {t('library.newInstruction')}
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-3 flex items-center gap-3 border-b border-border/30 flex-shrink-0">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground/50" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={t('library.searchPlaceholder')}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-muted/40 border border-transparent text-sm outline-none focus:border-border placeholder:text-muted-foreground/40"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {CATEGORIES.map(c => (
            <button
              key={c.value}
              onClick={() => setActiveCategory(c.value)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                activeCategory === c.value
                  ? 'bg-orange-500/10 text-orange-400 border border-orange-500/30'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {t(c.labelKey)}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <BookMarked className="w-12 h-12 text-muted-foreground/20 mb-4" />
            <p className="text-muted-foreground font-medium mb-1">
               {prompts.length === 0 ? t('library.noInstructions') : t('library.noResults')}
             </p>
            <p className="text-muted-foreground/50 text-sm mb-4">
               {prompts.length === 0
                ? t('library.noInstructionsDesc')
                : t('library.tryDifferent')}
            </p>
            {prompts.length === 0 && (
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleSeedDefaults} className="text-xs gap-1.5">
                  <Zap className="w-3.5 h-3.5" /> {t('library.addStarter')}
                </Button>
                <Button size="sm" onClick={() => setShowForm(true)} className="bg-orange-500 hover:bg-orange-600 text-white text-xs gap-1.5">
                  <Plus className="w-3.5 h-3.5" /> {t('library.createMyOwn')}
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map(p => (
              <div key={p.id} className="glass-card rounded-xl p-4 flex flex-col gap-3 group hover:bg-muted/20 transition-all">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm truncate">{p.title}</h3>
                    <span className={`inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${CATEGORY_COLORS[p.category] || CATEGORY_COLORS.general}`}>
                      <Tag className="w-2.5 h-2.5" />
                      {p.category}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => handleEdit(p)} className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => handleDelete(p.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-colors">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground line-clamp-3 flex-1">{p.content}</p>

                <button
                  onClick={() => handleCopy(p)}
                  className="flex items-center justify-center gap-1.5 w-full py-1.5 rounded-lg border border-border/50 text-xs text-muted-foreground hover:text-orange-400 hover:border-orange-500/30 hover:bg-orange-500/5 transition-all"
                >
                  {copiedId === p.id ? (
                    <><Check className="w-3.5 h-3.5 text-green-400" /><span className="text-green-400">{t('library.copied')}</span></>
                  ) : (
                    <><Copy className="w-3.5 h-3.5" /> {t('library.copyToClipboard')}</>
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Form Dialog */}
      <Dialog open={showForm} onOpenChange={open => { if (!open) { setShowForm(false); setEditingPrompt(null); } }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingPrompt ? t('library.editInstruction') : t('library.newAiInstruction')}</DialogTitle>
          </DialogHeader>
          <PromptForm
            initial={editingPrompt}
            onSave={handleSave}
            onClose={() => { setShowForm(false); setEditingPrompt(null); }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
