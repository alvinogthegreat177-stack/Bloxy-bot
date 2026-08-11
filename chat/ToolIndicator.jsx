import React from 'react';
import { Search, Cloud, TrendingUp, Newspaper, Clapperboard, Code, BookOpen, Loader2 } from 'lucide-react';
import { useLanguage } from '@/lib/LanguageContext';

const toolIcons = {
  search: Search,
  weather: Cloud,
  finance: TrendingUp,
  news: Newspaper,
  movies: Clapperboard,
  code: Code,
  knowledge: BookOpen,
};

export default function ToolIndicator({ tool, isActive }) {
  const { t } = useLanguage();
  const Icon = toolIcons[tool] || Search;
  const labels = {
    search: t('tools.searching'),
    weather: t('tools.weather'),
    finance: t('tools.finance'),
    news: t('tools.news'),
    movies: t('tools.movies'),
    code: t('tools.code'),
    knowledge: t('tools.knowledge'),
  };

  if (!isActive) return null;

  return (
    <div className="flex items-center gap-2 px-4 py-2 text-xs text-muted-foreground">
      <div className="flex items-center gap-2 bg-muted/30 rounded-full px-3 py-1.5">
        <Loader2 className="w-3 h-3 animate-spin text-orange-400" />
        <Icon className="w-3 h-3" />
        <span>{labels[tool] || t('tools.processing')}...</span>
      </div>
    </div>
  );
}
