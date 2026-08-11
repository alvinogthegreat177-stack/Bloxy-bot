import React from 'react';
import { Sparkles } from 'lucide-react';
import { useLanguage } from '@/lib/LanguageContext';

export default function FollowUpSuggestions({ onPick }) {
  const { t } = useLanguage();
  const SUGGESTIONS = [
    t('followup.more'),
    t('followup.example'),
    t('followup.summarize'),
  ];
  return (
    <div className="flex flex-wrap gap-2 px-4 py-2">
      {SUGGESTIONS.map(s => (
        <button
          key={s}
          onClick={() => onPick(s)}
          className="text-xs rounded-full border border-border/60 bg-muted/30 hover:bg-muted/50 hover:border-orange-500/40 px-3 py-1.5 transition-colors flex items-center gap-1.5"
        >
          <Sparkles className="w-3 h-3 text-orange-400" />
          {s}
        </button>
      ))}
    </div>
  );
}
