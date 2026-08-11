import React, { useState } from 'react';
import { runBloxy } from '@/lib/bloxyEngine';
import { Search, Loader2, ExternalLink, Sparkles, ArrowLeft, Globe, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { useToast } from '@/components/ui/use-toast';
import { useLanguage } from '@/lib/LanguageContext';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [mode, setMode] = useState('ai'); // ai, academic, research
  const { toast } = useToast();
  const { t } = useLanguage();

  const handleSearch = async () => {
    if (!query.trim()) return;
    const searchQuery = query.trim();
    setIsSearching(true);
    setResults(null);
    setQuery(''); // Clear input immediately after Enter

    const modePrompts = {
      ai: `Search the internet and provide a comprehensive answer to: "${searchQuery}". Include relevant facts, data, and sources. Format with markdown.`,
      academic: `Provide an academic research summary about: "${searchQuery}". Include key studies, findings, methodologies, and cite sources. Format with markdown headers and bullet points.`,
      research: `Do deep research on: "${searchQuery}". Provide an extensive analysis covering multiple perspectives, data points, expert opinions, and actionable insights. Format with markdown.`,
    };

    toast({ title: t('search.searchingToast'), description: `Bloxy Nexus → ${searchQuery}` });

    try {
      const result = await runBloxy({
        messages: [{ role: 'user', content: modePrompts[mode] }],
        tool: 'search',
      });
      setResults(result.content || t('search.noResponse'));
      toast({ title: t('search.searchComplete'), description: t('search.searchCompleteDesc') });
    } catch (err) {
      setResults(`${t('search.searchFailed')} ${err?.message || t('common.unknown')}`);
      toast({ title: t('search.searchFailed'), description: err?.message || t('common.unknown'), variant: 'destructive' });
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="h-12 border-b border-border/50 flex items-center px-4 gap-3 flex-shrink-0">
        <Link to="/">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <Search className="w-4 h-4 text-orange-400" />
        <span className="text-sm font-medium">{t('search.title')}</span>
      </div>

      <div className="flex-1 flex flex-col items-center">
        <div className="w-full max-w-2xl px-6 pt-16">
          {!results && !isSearching && (
            <div className="text-center mb-8">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-orange-500/20 to-blue-500/20 flex items-center justify-center mx-auto mb-4">
                <Globe className="w-7 h-7 text-orange-400" />
              </div>
              <h2 className="text-xl font-bold mb-2">{t('search.aiPoweredSearch')}</h2>
              <p className="text-sm text-muted-foreground">{t('search.subtitle')}</p>
            </div>
          )}

          <div className="glass-card rounded-2xl p-2 flex items-center gap-2 mb-4">
            <Search className="w-4 h-4 text-muted-foreground ml-3" />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder={t('search.placeholder')}
              className="flex-1 bg-transparent border-none outline-none text-sm py-2.5"
            />
            <Button
              onClick={handleSearch}
              disabled={isSearching || !query.trim()}
              className="rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 text-white px-4 h-9"
            >
              {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            </Button>
          </div>

          <div className="flex gap-2 mb-6 justify-center">
            {[
              { key: 'ai', label: t('search.aiSearch'), icon: Sparkles },
              { key: 'academic', label: t('search.academic'), icon: BookOpen },
              { key: 'research', label: t('search.research'), icon: Globe },
            ].map(m => (
              <button
                key={m.key}
                onClick={() => setMode(m.key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs transition-all ${
                  mode === m.key ? 'bg-orange-500/20 text-orange-400' : 'bg-muted/30 text-muted-foreground hover:bg-muted/50'
                }`}
              >
                <m.icon className="w-3 h-3" />
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {isSearching && (
          <div className="flex flex-col items-center gap-3 py-12">
            <Loader2 className="w-6 h-6 animate-spin text-orange-400" />
            <p className="text-sm text-muted-foreground">{t('search.searching')}</p>
          </div>
        )}

        {results && (
          <ScrollArea className="w-full max-w-2xl px-6 flex-1">
            <div className="glass-card rounded-2xl p-6 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-4 h-4 text-orange-400" />
                <span className="text-sm font-medium">{t('search.aiSummary')}</span>
              </div>
              <div className="message-content text-sm">
                <ReactMarkdown>{results}</ReactMarkdown>
              </div>
            </div>
          </ScrollArea>
        )}
      </div>
    </div>
  );
}
