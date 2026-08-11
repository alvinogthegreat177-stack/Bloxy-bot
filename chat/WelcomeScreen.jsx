import React, { useState } from 'react';
import { Search, Code, BookOpen, Newspaper, Cloud, TrendingUp, Clapperboard, Zap, Utensils, Globe, FlaskConical, Dumbbell, Music, Plane, Heart, Cpu } from 'lucide-react';
import { useLanguage } from '@/lib/LanguageContext';

const ALL_SUGGESTIONS = [
  { icon: Code, labelKey: 'welcome.writeCode', prompt: 'Help me write a Python function to parse JSON and filter results', color: 'text-blue-400', bg: 'bg-blue-500/10' },
  { icon: Cloud, labelKey: 'welcome.checkWeather', prompt: "What's the weather forecast for London this week?", color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
  { icon: TrendingUp, labelKey: 'welcome.cryptoPrices', prompt: 'What are the current prices of Bitcoin, Ethereum, and Solana?', color: 'text-green-400', bg: 'bg-green-500/10' },
  { icon: Newspaper, labelKey: 'welcome.latestNews', prompt: 'What are the top world headlines right now?', color: 'text-red-400', bg: 'bg-red-500/10' },
  { icon: Clapperboard, labelKey: 'welcome.movieInfo', prompt: 'What are the best movies of 2025 so far?', color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  { icon: BookOpen, labelKey: 'welcome.explainAnything', prompt: 'Explain how black holes work in simple terms', color: 'text-purple-400', bg: 'bg-purple-500/10' },
  { icon: Utensils, labelKey: 'welcome.recipeNutrition', prompt: 'Give me a healthy high-protein dinner recipe with macros', color: 'text-orange-400', bg: 'bg-orange-500/10' },
  { icon: Globe, labelKey: 'welcome.countryFacts', prompt: 'Tell me about Japan — population, economy, culture, and fun facts', color: 'text-teal-400', bg: 'bg-teal-500/10' },
  { icon: FlaskConical, labelKey: 'welcome.scienceSpace', prompt: 'What is NASA working on right now? Any upcoming launches?', color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
  { icon: Dumbbell, labelKey: 'welcome.sportsScores', prompt: 'What happened in soccer this week? Top results and standings', color: 'text-lime-400', bg: 'bg-lime-500/10' },
  { icon: Music, labelKey: 'welcome.musicArtists', prompt: "Who is the most streamed artist right now and what's their top song?", color: 'text-pink-400', bg: 'bg-pink-500/10' },
  { icon: Plane, labelKey: 'welcome.travelGuide', prompt: 'Plan me a 5-day trip to Tokyo with must-see spots', color: 'text-sky-400', bg: 'bg-sky-500/10' },
  { icon: Heart, labelKey: 'welcome.healthWellness', prompt: 'What are the symptoms of vitamin D deficiency and how to fix it?', color: 'text-rose-400', bg: 'bg-rose-500/10' },
  { icon: Search, labelKey: 'welcome.webSearch', prompt: 'Search for the latest AI breakthroughs in 2025', color: 'text-amber-400', bg: 'bg-amber-500/10' },
  { icon: Cpu, labelKey: 'welcome.techGadgets', prompt: 'What are the best smartphones released in 2025?', color: 'text-violet-400', bg: 'bg-violet-500/10' },
  { icon: Zap, labelKey: 'welcome.quickTask', prompt: 'Help me draft a professional email to my team about a deadline', color: 'text-fuchsia-400', bg: 'bg-fuchsia-500/10' },
];

export default function WelcomeScreen({ onSuggestionClick }) {
  const { t } = useLanguage();
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? ALL_SUGGESTIONS : ALL_SUGGESTIONS.slice(0, 8);

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-8">
      <div className="mb-6 text-center">
        <img
          src="https://media.base44.com/images/public/user_6a4148c2b0002e689ffdfa85/04309971a_image.png"
          alt="Bloxy-bot"
          className="w-16 h-16 rounded-2xl mx-auto mb-4 glow-orange"
        />
        <h1 className="text-2xl font-bold mb-2">
          <span className="gradient-text">Bloxy-bot</span> AI
        </h1>
        <p className="text-muted-foreground text-sm max-w-md">
          {t('chat.welcomeDesc')}
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-2xl w-full">
        {visible.map((s, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick(s.prompt)}
            className="glass-card rounded-xl p-3 text-left hover:bg-muted/40 transition-all group"
          >
            <div className={`w-8 h-8 rounded-lg ${s.bg} flex items-center justify-center mb-2`}>
              <s.icon className={`w-4 h-4 ${s.color}`} />
            </div>
            <p className="text-xs font-medium mb-0.5">{t(s.labelKey)}</p>
            <p className="text-[10px] text-muted-foreground/60 line-clamp-2">{s.prompt}</p>
          </button>
        ))}
      </div>

      <button
        onClick={() => setShowAll(!showAll)}
        className="mt-4 text-xs text-orange-400 hover:text-orange-300 transition-colors"
      >
        {showAll ? t('chat.showLess') : `↓ ${t('chat.showMore')} (${ALL_SUGGESTIONS.length - 8})`}
      </button>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-[10px] text-muted-foreground/40">
        <span>{t('settings.dataSources')}</span><span>·</span>
        <span>{t('settings.liveSearch')}</span><span>·</span>
        <span>{t('settings.weatherFinance')}</span><span>·</span>
        <span>{t('settings.newsSports')}</span><span>·</span>
        <span>{t('settings.codeScience')}</span><span>·</span>
        <span>{t('settings.visionFiles')}</span>
      </div>
    </div>
  );
}
