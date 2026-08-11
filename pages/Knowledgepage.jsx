import React, { useState, useEffect } from 'react';
import { base44 } from '@/api/base44Client';
import { BookOpen, Plus, Trash2, ArrowLeft, FileText, Star, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Link } from 'react-router-dom';
import { useLanguage } from '@/lib/LanguageContext';

const { SavedPrompt } = base44.entities;

const categoryColors = {
  general: 'bg-gray-500/10 text-gray-400',
  coding: 'bg-blue-500/10 text-blue-400',
  writing: 'bg-purple-500/10 text-purple-400',
  research: 'bg-green-500/10 text-green-400',
  planning: 'bg-orange-500/10 text-orange-400',
  creative: 'bg-pink-500/10 text-pink-400',
};

export default function KnowledgePage() {
  const [prompts, setPrompts] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('general');
  const [filter, setFilter] = useState('all');
  const { t } = useLanguage();

  useEffect(() => { load(); }, []);

  const load = async () => {
    const data = await SavedPrompt.list('-created_date', 50);
    setPrompts(data);
  };

  const handleSave = async () => {
    if (!title.trim() || !content.trim()) return;
    await SavedPrompt.create({ title, content, category });
    setTitle(''); setContent(''); setCategory('general'); setIsOpen(false);
    load();
  };

  const handleDelete = async (id) => {
    await SavedPrompt.delete(id);
    load();
  };

  const filtered = filter === 'all' ? prompts : prompts.filter(p => p.category === filter);

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="h-12 border-b border-border/50 flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link to="/"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
          <BookOpen className="w-4 h-4 text-orange-400" />
          <span className="text-sm font-medium">{t('knowledge.title')}</span>
        </div>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 text-white h-8 text-xs gap-1.5">
              <Plus className="w-3 h-3" /> {t('knowledge.savePrompt')}
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-border/50">
            <DialogHeader><DialogTitle>{t('knowledge.saveAPrompt')}</DialogTitle></DialogHeader>
            <div className="space-y-3 mt-2">
              <Input placeholder={t('knowledge.titlePlaceholder')} value={title} onChange={e => setTitle(e.target.value)} className="bg-muted/30 border-border/50" />
              <Textarea placeholder={t('knowledge.contentPlaceholder')} value={content} onChange={e => setContent(e.target.value)} rows={4} className="bg-muted/30 border-border/50" />
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="bg-muted/30 border-border/50"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">{t('library.general')}</SelectItem>
                  <SelectItem value="coding">{t('library.coding')}</SelectItem>
                  <SelectItem value="writing">{t('library.writing')}</SelectItem>
                  <SelectItem value="research">{t('library.research')}</SelectItem>
                  <SelectItem value="planning">{t('library.planning')}</SelectItem>
                  <SelectItem value="creative">{t('library.creative')}</SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={handleSave} className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white">{t('common.save')}</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="p-4">
        <div className="flex gap-2 flex-wrap">
          {[{ v: 'all', k: 'library.all' }, { v: 'general', k: 'library.general' }, { v: 'coding', k: 'library.coding' }, { v: 'writing', k: 'library.writing' }, { v: 'research', k: 'library.research' }, { v: 'planning', k: 'library.planning' }, { v: 'creative', k: 'library.creative' }].map(f => (
            <button
              key={f.v}
              onClick={() => setFilter(f.v)}
              className={`px-3 py-1.5 rounded-full text-xs capitalize transition-all ${
                filter === f.v ? 'bg-orange-500/20 text-orange-400' : 'bg-muted/30 text-muted-foreground hover:bg-muted/50'
              }`}
            >
              {t(f.k)}
            </button>
          ))}
        </div>
      </div>

      <ScrollArea className="flex-1 px-4 pb-4">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <Sparkles className="w-10 h-10 text-muted-foreground/30 mb-3" />
            <p className="text-sm text-muted-foreground">{t('knowledge.noPrompts')}</p>
            <p className="text-xs text-muted-foreground/50 mt-1">{t('knowledge.noPromptsDesc')}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map(p => (
              <div key={p.id} className="glass-card rounded-xl p-4 group hover:bg-muted/40 transition-all">
                <div className="flex items-start justify-between mb-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${categoryColors[p.category] || categoryColors.general}`}>
                    {p.category}
                  </span>
                  <button onClick={() => handleDelete(p.id)} className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-red-500/20">
                    <Trash2 className="w-3 h-3 text-red-400" />
                  </button>
                </div>
                <h3 className="text-sm font-medium mb-1">{p.title}</h3>
                <p className="text-xs text-muted-foreground line-clamp-3">{p.content}</p>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
