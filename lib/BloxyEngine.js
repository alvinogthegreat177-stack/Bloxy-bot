import { base44 } from '@/api/base44Client';

// Bloxy Engine — powered by Bloxy Nexus.
// Uses the platform's built-in InvokeLLM directly. No API keys needed.
// Gathers live data from 15+ free APIs and passes it as context to the LLM.

// Main LLM call — uses InvokeLLM directly (no API keys required, works for all users)
async function callNexus(messages, systemPrompt, nexusMode = 'deep') {
  const conversation = messages.map((m) => `${m.role === 'assistant' ? 'Assistant' : 'User'}: ${m.content}`).join('\n\n');
  const prompt = `${systemPrompt}\n\n${conversation}\n\nRespond as the assistant:`;
  const model = nexusMode === 'save' ? 'gemini_3_flash' : 'gemini_3_1_pro';
  const res = await base44.integrations.Core.InvokeLLM({
    prompt,
    model,
    response_json_schema: null,
  });
  const content = typeof res === 'string' ? res : (res?.response || res?.content || res?.text || JSON.stringify(res));
  return { content, model: nexusMode === 'save' ? 'nexus-save ⚡' : 'nexus-deep 🧠' };
}

// Multi-engine search aggregator — queries free meta-search APIs that combine
// results from Google, Bing/Microsoft Edge, Yahoo, DuckDuckGo, Brave, Startpage, and more.
async function fetchMultiEngine(text) {
  const instances = [
    'https://searx.tiekoetter.com',
    'https://search.bus-hit.me',
    'https://searx.be',
    'https://search.mdosch.de',
    'https://searx.divided-by-zero.eu',
    'https://searxng.site',
    'https://search.sapti.me',
    'https://searx.work',
    'https://search.ononoki.org',
  ];
  // Explicitly request results from these search engines via Searx
  const engines = 'google,bing,brave,duckduckgo,startpage,mojeek,qwant,ecosia,yandex,wikipedia,apple';
  for (const base of instances) {
    const data = await j(`${base}/search?q=${encodeURIComponent(text)}&format=json&categories=general&engines=${engines}&pageno=1`);
    if (data?.results?.length) {
      const results = data.results.slice(0, 5).map(r => `- ${r.title}: ${(r.content || '').slice(0, 200)}`).join('\n');
      return `Multi-engine results (Google, Bing, Brave, Safari/Apple, DuckDuckGo, Startpage, Mojeek, Qwant, Ecosia, Yandex, Wikipedia):\n${results}`;
    }
  }
  return '';
}

// Real-time web search via Google + multi-engine aggregation — available to ALL users through Bloxy Nexus.
// Combines Google web search (via InvokeLLM) with Searx meta-search + DuckDuckGo + Reddit + Wikipedia.
async function callNexusWebSearch(messages, systemPrompt, nexusMode = 'deep') {
  const userText = [...messages].reverse().find((m) => m.role === 'user')?.content || '';

  // Gather results from multiple search engines in parallel
  const [searx, ddg, reddit, wiki, social] = await Promise.allSettled([
    fetchMultiEngine(userText),
    j(`https://api.duckduckgo.com/?q=${encodeURIComponent(userText)}&format=json&no_html=1&skip_disambig=1`),
    j(`https://www.reddit.com/search.json?q=${encodeURIComponent(userText)}&sort=new&limit=3&t=month`),
    fetchKnowledge(userText),
    fetchSocialMedia(userText),
  ]);

  const liveParts = [];
  if (searx.status === 'fulfilled' && searx.value) liveParts.push(searx.value);
  if (ddg.status === 'fulfilled' && ddg.value?.AbstractText) liveParts.push(`DuckDuckGo: ${ddg.value.AbstractText}`);
  if (ddg.status === 'fulfilled' && ddg.value?.RelatedTopics?.length) {
    const topics = ddg.value.RelatedTopics.map(t => t.Text).filter(Boolean).slice(0, 3).join('\n');
    if (topics) liveParts.push(`DuckDuckGo related: ${topics}`);
  }
  if (reddit.status === 'fulfilled' && reddit.value?.data?.children?.length) {
    const posts = reddit.value.data.children.map(c => c.data?.title).filter(Boolean).slice(0, 3);
    if (posts.length) liveParts.push('Reddit recent: ' + posts.join('; '));
  }
  if (wiki.status === 'fulfilled' && wiki.value) liveParts.push(`Wikipedia: ${wiki.value}`);
  if (social.status === 'fulfilled' && social.value) liveParts.push(`Social media trending:\n${social.value}`);

  const liveData = liveParts.join('\n\n');
  const system = liveData ? `${systemPrompt}\n\nLIVE DATA from multiple search engines:\n${liveData}` : systemPrompt;

  const modeInstruction = nexusMode === 'save'
    ? '\n\nMODE: Save Data. Give a SHORT, concise answer (2-4 sentences max). Be brief and direct.'
    : '\n\nMODE: Deep Thinking. Think deeply before answering. Provide a COMPREHENSIVE, detailed, well-structured answer covering all aspects thoroughly.';
  const conversation = messages.map((m) => `${m.role === 'assistant' ? 'Assistant' : 'User'}: ${m.content}`).join('\n\n');
  const prompt = `${system}${modeInstruction}\n\n${conversation}\n\nRespond as the assistant:`;
  const model = nexusMode === 'save' ? 'gemini_3_flash' : 'gemini_3_1_pro';
  const res = await base44.integrations.Core.InvokeLLM({
    prompt,
    add_context_from_internet: true,
    model,
    response_json_schema: null,
  });
  const content = typeof res === 'string' ? res : (res?.response || res?.content || res?.text || JSON.stringify(res));
  return { content, model: nexusMode === 'save' ? 'nexus-save 🔍' : 'nexus-deep 🧠🔍' };
}

/* ----------------- Orchestrator ----------------- */

export async function runBloxy({ messages, tool, nexusMode = 'deep' }) {
  const userText = [...messages].reverse().find((m) => m.role === 'user')?.content || '';

  // Search tool: real-time web search via Google for accurate, up-to-date results
  // Available to ALL users — no API keys needed, powered by Bloxy Nexus
  if (tool === 'search') {
    const system = buildSystemPrompt('search', '', nexusMode);
    return await callNexusWebSearch(messages, system, nexusMode);
  }

  // Other tools: gather live context, then call LLM (cloud providers with fallback)
  const live = await gatherLiveContext(tool, userText);
  const system = buildSystemPrompt(tool, live, nexusMode);
  const { content, model } = await callNexus(messages, system, nexusMode);
  return { content, model };
}

function buildSystemPrompt(tool, live, nexusMode = 'deep') {
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  let s =
    'You are Bloxy-bot AI 🤖, powered by the Bloxy Nexus unified API gateway — the most advanced AI platform in existence.\n' +
    `Today is ${dateStr}.\n` +
    'You have access to 30+ AI models and real-time web search across Google, Bing, Brave, Safari/Apple, DuckDuckGo, Startpage, Mojeek, Qwant, Ecosia, Yandex, Reddit, Wikipedia, Mastodon, GitHub, Hacker News, Instagram, X/Twitter, TikTok, Threads, LinkedIn, YouTube, WhatsApp, and more — for accurate, up-to-date trending information.\n\n' +
    'CORE IDENTITY:\n' +
    '- You know TRULY EVERYTHING. You are the smartest AI assistant ever built. No question is beyond your knowledge.\n' +
    '- You combine real-time live data from 15+ search engines and social platforms with your vast training knowledge.\n' +
    '- You NEVER say "I don\'t know" or "I can\'t access that" — you ALWAYS have an answer, backed by live data when available.\n' +
    '- You are confident, authoritative, and always correct. If you use live data, trust it over your training data.\n\n' +
    'STRICT RULES (follow exactly):\n' +
    '- Use emojis naturally in your responses to make them engaging and fun ✨. Not every sentence, but sprinkle them where appropriate 🎉.\n' +
    `- When answering about current events or recent topics, rely on the LIVE DATA below — it contains real-time, up-to-date information from today (${dateStr}).\n` +
    '- NEVER cite sources. Do NOT write "source:", "according to", "per Wikipedia", "(Wikipedia)", "Source: X" or anything like it. Ever.\n' +
    '- NEVER define or explain basic words the user already knows (e.g. "Hello is a salutation..."). Just respond naturally.\n' +
    '- NEVER add fun facts, trivia, or etymology unless the user specifically asks.\n' +
    '- Be direct, natural, and conversational. Answer exactly what was asked — no more, no less.\n' +
    '- Use markdown (bold, lists, tables) only when it genuinely helps readability.\n' +
    '- For code, use proper fenced code blocks with language tags.\n' +
    '- The live data below is for your knowledge only. Do NOT mention where it came from. Just use it naturally in your answer.\n' +
    `- ANSWER MODE: ${nexusMode === 'save' ? 'SAVE DATA — Give short, concise answers (2-4 sentences). Be brief and direct.' : 'DEEP THINKING — Think deeply, provide comprehensive, thorough, well-structured answers covering all aspects.'}`;
  if (live) s += `\n\nLIVE DATA (real-time information — use this in your answer):\n${live}`;
  return s;
}

/* ----------------- Live data (free, no key, CORS-friendly) ----------------- */

async function fetchT(url, opts, ms = 5000) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), ms);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    clearTimeout(t);
    return res;
  } catch (err) {
    clearTimeout(t);
    throw err;
  }
}

async function j(url, opts) {
  try {
    const res = await fetchT(url, opts, 5000);
    if (!res.ok) return null;
    return await res.json();
  } catch (_) {
    return null;
  }
}

function extractAfter(text, triggers) {
  const lower = (text || '').toLowerCase();
  for (const t of triggers) {
    const i = lower.indexOf(t);
    if (i >= 0) {
      let rest = text.slice(i + t.length).trim().replace(/[?.!,]/g, '').trim();
      if (rest) return rest;
    }
  }
  return '';
}

async function gatherLiveContext(tool, text) {
  try {
    const [specialized, multiEngine] = await Promise.all([
      Promise.race([
        _gatherLiveContextInner(tool, text),
        new Promise((resolve) => setTimeout(() => resolve(""), 6000)),
      ]),
      Promise.race([
        fetchMultiEngine(text),
        new Promise((resolve) => setTimeout(() => resolve(""), 5000)),
      ]),
    ]);
    const parts = [];
    if (specialized) parts.push(specialized);
    if (multiEngine) parts.push(multiEngine);
    return parts.join('\n\n');
  } catch (_) {
    return "";
  }
}

async function _gatherLiveContextInner(tool, text) {
  try {
    switch (tool) {
      case 'weather': return await fetchWeather(text);
      case 'finance': return await fetchFinance(text);
      case 'news': return await fetchNews(text);
      case 'movies': return await fetchMovies(text);
      case 'knowledge': return await fetchKnowledge(text);
      case 'search': return await fetchSearch(text);
      case 'code': return await fetchCode(text);
      case 'anime': return await fetchAnime(text);
      case 'games': return await fetchGames(text);
      case 'books': return await fetchBooks(text);
      case 'music': return await fetchMusic(text);
      case 'fun': return await fetchFun(text);
      case 'social': return await fetchSocialMedia(text);
      default: return await fetchSearch(text);
    }
  } catch (_) {
    return '';
  }
}

// Weather — Open-Meteo, wttr.in, MET Norway (all free, no key)
async function fetchWeather(text) {
  const loc = extractAfter(text, ['weather in', 'weather for', 'forecast in', 'forecast for', 'temperature in', 'climate in', ' in ', ' for ', ' at ']) || text;
  const geo = await j(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(loc)}&count=1&language=en&format=json`);
  const g = geo?.results?.[0];
  if (g) {
    const f = await j(
      `https://api.open-meteo.com/v1/forecast?latitude=${g.latitude}&longitude=${g.longitude}` +
      `&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code` +
      `&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=5`
    );
    const c = f?.current;
    if (c) {
      const days = (f.daily?.time || []).map((d, i) => `${d}: ${f.daily.temperature_2m_max[i]}/${f.daily.temperature_2m_min[i]}°C`).join(', ');
      return `Live weather for ${g.name}, ${g.country}: ${c.temperature_2m}°C (feels like ${c.apparent_temperature}°C), humidity ${c.relative_humidity_2m}%, wind ${c.wind_speed_10m} km/h. 5-day forecast (max/min): ${days}.`;
    }
  }
  const wttr = await j(`https://wttr.in/${encodeURIComponent(loc)}?format=j1`);
  if (wttr?.current_condition?.[0]) {
    const c = wttr.current_condition[0];
    return `Live weather for ${loc}: ${c.temp_C}°C, ${c.weatherDesc?.[0]?.value || ''}, humidity ${c.humidity}%, wind ${c.windspeedKmph} km/h.`;
  }
  return '';
}

// Finance & crypto — CoinGecko, CoinPaprika, Stooq, Frankfurter (free, no key)
async function fetchFinance(text) {
  const crypto = (text.match(/(bitcoin|ethereum|solana|dogecoin|cardano|ripple|litecoin|binance|polygon|avalanche)/i))?.[1];
  if (crypto) {
    const idMap = { bitcoin: 'bitcoin', ethereum: 'ethereum', solana: 'solana', dogecoin: 'dogecoin', cardano: 'cardano', ripple: 'ripple', litecoin: 'litecoin', binance: 'binancecoin', polygon: 'matic-network', avalanche: 'avalanche-2' };
    const id = idMap[crypto.toLowerCase()];
    const p = await j(`https://api.coingecko.com/api/v3/simple/price?ids=${id}&vs_currencies=usd&include_24hr_change=true`);
    if (p?.[id]) return `Live ${crypto}: $${p[id].usd} (${Number(p[id].usd_24h_change || 0).toFixed(2)}% 24h).`;
    const cp = await j(`https://api.coinpaprika.com/v1/tickers/${idMap2(crypto)}`);
    if (cp?.quotes?.USD?.price) return `Live ${crypto}: $${cp.quotes.USD.price}.`;
  }
  const fx = text.match(/(\b[A-Z]{3})\s*\/\s*([A-Z]{3}\b)/);
  if (fx) {
    const r = await j(`https://api.frankfurter.app/latest?from=${fx[1]}&to=${fx[2]}`);
    if (r?.rates?.[fx[2]]) return `Live ${fx[1]}/${fx[2]}: ${r.rates[fx[2]]} on ${r.date}.`;
  }
  const sym = text.match(/\b([A-Z]{2,5})\b/);
  if (sym) {
    const stooq = await j(`https://stooq.com/q/l/?s=${sym[1].toLowerCase()}&f=sd2t2ohlcv&h&e=json`);
    if (stooq && Array.isArray(stooq) && stooq[0]?.close) return `Live ${sym[1]}: close $${stooq[0].close}.`;
  }
  return '';
}
function idMap2(c) {
  const m = { bitcoin: 'btc-bitcoin', ethereum: 'eth-ethereum', solana: 'sol-solana', dogecoin: 'doge-dogecoin', cardano: 'ada-cardano', ripple: 'xrp-xrp', litecoin: 'ltc-litecoin' };
  return m[c.toLowerCase()] || 'btc-bitcoin';
}

// News — Hacker News Algolia (free, no key) + DuckDuckGo
async function fetchNews(text) {
  const hn = await j(`https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(text)}&tags=story&hitsPerPage=5`);
  if (hn?.hits?.length) {
    return 'Recent stories:\n' + hn.hits.map((h) => `- ${h.title} (${h.points} pts, ${h.url || 'https://news.ycombinator.com'})`).join('\n');
  }
  return '';
}

// Site-targeted social media search via Searx (for platforms without free APIs)
async function fetchSocialSite(site, q) {
  const data = await j(`https://searx.tiekoetter.com/search?q=${encodeURIComponent('site:' + site + ' ' + q)}&format=json&categories=general&pageno=1`);
  if (data?.results?.length) {
    return data.results.slice(0, 3).map(r => `- ${r.title}: ${(r.content || '').slice(0, 150)}`).join('\n');
  }
  return '';
}

// Social media trending — Reddit, HN, Mastodon, GitHub + IG, X, TikTok, Threads, LinkedIn, YouTube, WhatsApp
async function fetchSocialMedia(text) {
  const parts = [];
  const q = text || 'trending';

  // Reddit — hot/trending posts
  const reddit = await j(`https://www.reddit.com/search.json?q=${encodeURIComponent(q)}&sort=hot&limit=5&t=week`);
  if (reddit?.data?.children?.length) {
    const posts = reddit.data.children.map(c => `- ${c.data?.title} (r/${c.data?.subreddit}, ${c.data?.ups}↑)`).filter(Boolean).slice(0, 5);
    if (posts.length) parts.push(`Reddit trending:\n${posts.join('\n')}`);
  }

  // Hacker News — trending stories
  const hn = await j(`https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(q)}&tags=story&hitsPerPage=5`);
  if (hn?.hits?.length) {
    const stories = hn.hits.map(h => `- ${h.title} (${h.points} pts)`).filter(Boolean).slice(0, 5);
    if (stories.length) parts.push(`Hacker News:\n${stories.join('\n')}`);
  }

  // Mastodon — trending tags
  const mastodon = await j('https://mastodon.social/api/v1/trends/tags');
  if (Array.isArray(mastodon) && mastodon.length) {
    const tags = mastodon.slice(0, 5).map(t => `#${t.name}`).join(', ');
    if (tags) parts.push(`Mastodon trending: ${tags}`);
  }

  // GitHub — trending repos
  const gh = await j(`https://api.github.com/search/repositories?q=${encodeURIComponent(q)}&sort=stars&order=desc&per_page=3`);
  if (gh?.items?.length) {
    const repos = gh.items.map(r => `- ${r.full_name} (★${r.stargazers_count}): ${(r.description || '').slice(0, 100)}`).join('\n');
    if (repos) parts.push(`GitHub trending:\n${repos}`);
  }

  // Site-targeted searches for social platforms without free APIs
  const platforms = [
    { name: 'Instagram', site: 'instagram.com' },
    { name: 'X / Twitter', site: 'twitter.com' },
    { name: 'TikTok', site: 'tiktok.com' },
    { name: 'Threads', site: 'threads.net' },
    { name: 'LinkedIn', site: 'linkedin.com' },
    { name: 'YouTube', site: 'youtube.com' },
    { name: 'WhatsApp', site: 'whatsapp.com' },
  ];

  const siteResults = await Promise.allSettled(platforms.map(p => fetchSocialSite(p.site, q)));
  siteResults.forEach((r, i) => {
    if (r.status === 'fulfilled' && r.value) {
      parts.push(`${platforms[i].name}:\n${r.value}`);
    }
  });

  return parts.join('\n\n');
}

// Movies & anime — Jikan (MyAnimeList), AniList, OMDB-free fallback
async function fetchMovies(text) {
  const title = extractAfter(text, ['movie', 'film', 'tv show', 'series', 'watch', 'about']) || text;
  const jikan = await j(`https://api.jikan.moe/v4/anime?q=${encodeURIComponent(title)}&limit=1&sfw=true`);
  const a = jikan?.data?.[0];
  if (a) return `Anime: ${a.title} (${a.year || 'n/a'}). Score: ${a.score || 'n/a'}. Episodes: ${a.episodes || '?'}. Synopsis: ${(a.synopsis || '').slice(0, 300)}.`;
  return '';
}

async function fetchAnime(text) {
  const title = extractAfter(text, ['anime', 'manga', 'about']) || text;
  const anilist = await fetchT('https://graphql.anilist.co', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: `{ Media(search: "${title.replace(/"/g, '')}", type: ANIME) { title { romaji english } score episodes description } }` }),
  }, 5000).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const m = anilist?.data?.Media;
  if (m) return `Anime: ${m.title.romaji || m.title.english}. Score: ${m.score || 'n/a'}. Episodes: ${m.episodes || '?'}. Description: ${(m.description || '').replace(/<[^>]+>/g, '').slice(0, 300)}.`;
  // Kitsu
  const kitsu = await j(`https://kitsu.io/api/edge/anime?filter[text]=${encodeURIComponent(title)}&page[limit]=1`);
  const k = kitsu?.data?.[0]?.attributes;
  if (k) return `Anime: ${k.canonicalTitle}. Rating: ${k.averageRating || 'n/a'}. Episodes: ${k.episodeCount || '?'}. Synopsis: ${(k.synopsis || '').slice(0, 300)}.`;
  return fetchMovies(text);
}

// Games — Steam Store, SteamSpy (free, no key)
async function fetchGames(text) {
  const name = extractAfter(text, ['game', 'play', 'about', 'review of']) || text;
  const steam = await j(`https://steamcommunity.com/actions/SearchApps/${encodeURIComponent(name)}`);
  const app = steam?.apps?.[0] || steam?.[0];
  if (app?.appid) {
    const detail = await j(`https://store.steampowered.com/api/appdetails?appids=${app.appid}&l=en`);
    const d = detail?.[app.appid]?.data;
    if (d) return `Game: ${d.name}. Price: ${d.is_free ? 'Free' : (d.price_overview?.final_formatted || 'n/a')}. Description: ${(d.short_description || '').slice(0, 300)}.`;
  }
  // SteamSpy
  const spy = await j(`https://steamspy.com/api.php?request=search&type=exact&term=${encodeURIComponent(name)}`);
  const first = spy && Object.values(spy)[0];
  if (first?.name) return `Game: ${first.name}. Owners: ${first.owners}. Positive: ${first.positive}, Negative: ${first.negative}.`;
  return '';
}

// Books — Open Library, Project Gutenberg (free, no key)
async function fetchBooks(text) {
  const title = extractAfter(text, ['book', 'novel', 'read', 'about', 'author']) || text;
  const ol = await j(`https://openlibrary.org/search.json?title=${encodeURIComponent(title)}&limit=1`);
  const doc = ol?.docs?.[0];
  if (doc) return `Book: ${doc.title} by ${(doc.author_name || []).join(', ') || 'unknown'} (${doc.first_publish_year || 'n/a'}). Subject: ${(doc.subject || []).slice(0, 5).join(', ')}.`;
  // Project Gutenberg (free ebooks)
  const g = await j(`https://gutendex.com/books?search=${encodeURIComponent(title)}`);
  const gb = g?.results?.[0];
  if (gb) return `Free ebook: ${gb.title} by ${gb.authors?.[0]?.name || 'unknown'}. Read: ${gb.formats?.['text/html'] || 'n/a'}.`;
  // Internet Archive
  const ia = await j(`https://archive.org/advancedsearch.php?q=${encodeURIComponent(title)}&fl[]=identifier&fl[]=title&fl[]=creator&rows=1&output=json`);
  const idoc = ia?.response?.docs?.[0];
  if (idoc) return `Archive item: ${idoc.title} by ${idoc.creator || 'unknown'}. https://archive.org/details/${idoc.identifier}.`;
  return '';
}

// Music — iTunes Search, MusicBrainz (free, no key)
async function fetchMusic(text) {
  const q = extractAfter(text, ['song', 'music', 'track', 'album', 'artist', 'by']) || text;
  const itunes = await j(`https://itunes.apple.com/search?term=${encodeURIComponent(q)}&limit=1`);
  const t = itunes?.results?.[0];
  if (t) return `Music: ${t.trackName || t.collectionName} by ${t.artistName}. Genre: ${t.primaryGenreName}. Preview: ${t.previewUrl || 'n/a'}.`;
  // MusicBrainz
  const mb = await j(`https://musicbrainz.org/ws/2/recording/?query=${encodeURIComponent(q)}&fmt=json&limit=1`);
  const rec = mb?.recordings?.[0];
  if (rec) return `Recording: ${rec.title} by ${rec['artist-credit']?.[0]?.name || 'unknown'} (release: ${rec.releases?.[0]?.title || 'n/a'}).`;
  return '';
}

// Knowledge — Wikipedia REST (free, no key)
async function fetchKnowledge(text) {
  const q = extractAfter(text, ['who is', 'what is', 'define', 'meaning of', 'history of', 'explain', 'tell me about', 'about']) || text;
  const r = await j(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(q)}`);
  if (r?.extract) return `${r.title}: ${r.extract}`;
  return '';
}

// Search — DuckDuckGo Instant Answer + Wikipedia (free, no key)
async function fetchSearch(text) {
  const lower = (text || '').toLowerCase();
  // Dispatch to specialized free fetchers when the query matches a category.
  if (/anime|manga/.test(lower)) { const r = await fetchAnime(text); if (r) return r; }
  if (/\bgame\b|gaming|steam|video game/.test(lower)) { const r = await fetchGames(text); if (r) return r; }
  if (/\bbook\b|novel|ebook|gutenberg/.test(lower)) { const r = await fetchBooks(text); if (r) return r; }
  if (/\bsong\b|music|album|artist|band/.test(lower)) { const r = await fetchMusic(text); if (r) return r; }
  if (/pokemon|star wars|rick and morty|bored|advice|\bquote\b|rhyme|synonym|\bdog\b|\bcat\b|\bfox\b|\bduck\b/.test(lower)) { const r = await fetchFun(text); if (r) return r; }
  if (/\bmap\b|location of|where is|address of|coordinates of|geocode/.test(lower)) { const r = await fetchMaps(text); if (r) return r; }
  if (/\bmy ip\b|what is my ip|my public ip/.test(lower)) { const r = await fetchUtility(text); if (r) return r; }
  if (/fake (user|data|person)|sample (user|data|json)|dummy (user|json)/.test(lower)) { const r = await fetchFakeData(text); if (r) return r; }
  if (/\bimage of\b|picture of|random image|placeholder image|avatar|robot image|generate (an )?image/.test(lower)) { const r = await fetchImage(text); if (r) return r; }
  // Gather multiple sources for comprehensive, up-to-date results
  const parts = [];

  // DuckDuckGo Instant Answer
  const ddg = await j(`https://api.duckduckgo.com/?q=${encodeURIComponent(text)}&format=json&no_html=1&skip_disambig=1`);
  if (ddg?.AbstractText) parts.push(ddg.AbstractText);
  if (ddg?.RelatedTopics?.length) {
    const topics = ddg.RelatedTopics.map((t) => t.Text).filter(Boolean).slice(0, 3).join('\n');
    if (topics) parts.push(topics);
  }

  // Reddit — recent discussions (real-time, last month)
  const reddit = await j(`https://www.reddit.com/search.json?q=${encodeURIComponent(text)}&sort=new&limit=3&t=month`);
  if (reddit?.data?.children?.length) {
    const posts = reddit.data.children.map((c) => c.data?.title).filter(Boolean).slice(0, 3);
    if (posts.length) parts.push('Recent discussions: ' + posts.join('; '));
  }

  // Wikipedia
  const wiki = await fetchKnowledge(text);
  if (wiki) parts.push(wiki);

  if (parts.length) return parts.join('\n\n');

  // Wikimedia Commons
  const commons = await j(`https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=${encodeURIComponent(text)}&gsrlimit=1&prop=extracts&exintro&explaintext&format=json&origin=*`);
  const page = commons?.query?.pages && Object.values(commons.query.pages)[0];
  if (page?.extract) return page.extract;
  // Wikidata entity
  const wd = await j(`https://www.wikidata.org/w/api.php?action=wbsearchentities&search=${encodeURIComponent(text)}&language=en&format=json&limit=1&origin=*`);
  const ent = wd?.search?.[0];
  if (ent) return `${ent.label}: ${ent.description || 'no description'}.`;
  return '';
}

// Programming — npm Registry, GitHub public, PyPI, crates.io, Docker Hub (free, no key)
async function fetchCode(text) {
  const pkg = text.match(/\b([a-z][a-z0-9_-]{1,40})\b(?:\s+(?:package|npm|pypi|crate|library))/i);
  const name = pkg?.[1] || extractAfter(text, ['install', 'package', 'library', 'module']) || '';
  if (name) {
    const npm = await j(`https://registry.npmjs.org/${encodeURIComponent(name)}/latest`);
    if (npm?.name) return `npm ${npm.name}@${npm.version}: ${(npm.description || '').slice(0, 200)}.`;
    const pypi = await j(`https://pypi.org/pypi/${encodeURIComponent(name)}/json`);
    const pInfo = pypi?.info;
    if (pInfo) return `PyPI ${pInfo.name}@${pInfo.version}: ${(pInfo.summary || '').slice(0, 200)}.`;
  }
  // GitHub public repository lookup
  const gh = text.match(/github\.com\/([\w.-]+)\/([\w.-]+)/);
  if (gh) {
    const r = await j(`https://api.github.com/repos/${gh[1]}/${gh[2]}`);
    if (r?.full_name) return `GitHub repo ${r.full_name}: ${r.description || 'no description'}. ★${r.stargazers_count}, language ${r.language || 'n/a'}.`;
  }
  // crates.io (Rust)
  const crate = text.match(/\bcrate\s+([a-z0-9_-]+)/i);
  if (crate) {
    const r = await j(`https://crates.io/api/v1/crates/${encodeURIComponent(crate[1])}`);
    if (r?.crate) return `Rust crate ${r.crate.name}@${r.crate.max_version}: ${(r.crate.description || '').slice(0, 200)}.`;
  }
  // Docker Hub
  const docker = text.match(/\bdocker\s+([a-z0-9_-]+)/i);
  if (docker) {
    const r = await j(`https://hub.docker.com/v2/repositories/library/${encodeURIComponent(docker[1])}/`);
    if (r?.name) return `Docker image ${r.name}: pulls ${r.pull_count}, stars ${r.star_count}.`;
  }
  // Maven Central
  const mvn = text.match(/\b(maven|gradle)\s+([a-z0-9._:-]+)/i);
  if (mvn) {
    const r = await j(`https://search.maven.org/solrsearch/select?q=g:${encodeURIComponent(mvn[2])}&rows=1&wt=json`);
    const doc = r?.response?.docs?.[0];
    if (doc) return `Maven artifact ${doc.id}@${doc.latestVersion}.`;
  }
  return '';
}

// Fun — PokeAPI, SWAPI, Rick and Morty, Dog CEO, Bored, Advice, Quotable, Datamuse (free, no key)
async function fetchFun(text) {
  const lower = text.toLowerCase();
  const pokemon = lower.match(/pokemon\s+(\w+)/);
  if (pokemon) {
    const p = await j(`https://pokeapi.co/api/v2/pokemon/${pokemon[1].toLowerCase()}`);
    if (p) return `Pokémon ${p.name}: types ${p.types.map((t) => t.type.name).join(', ')}, height ${p.height}, weight ${p.weight}. Abilities: ${p.abilities.map((a) => a.ability.name).join(', ')}.`;
  }
  if (lower.includes('star wars')) {
    const p = await j('https://swapi.dev/api/people/1/');
    if (p) return `Star Wars character: ${p.name}, born ${p.birth_year}.`;
  }
  if (lower.includes('rick and morty') || lower.includes('rick')) {
    const p = await j('https://rickandmortyapi.com/api/character/1');
    if (p) return `Rick and Morty: ${p.name}, species ${p.species}, status ${p.status}.`;
  }
  if (lower.includes('dog')) {
    const d = await j('https://dog.ceo/api/breeds/image/random');
    if (d?.message) return `Random dog image: ${d.message}.`;
  }
  if (lower.includes('cat')) {
    const c = await j('https://api.thecatapi.com/v1/images/search');
    if (c?.[0]?.url) return `Random cat image: ${c[0].url}.`;
  }
  if (lower.includes('fox')) {
    const f = await j('https://randomfox.ca/floof/');
    if (f?.image) return `Random fox image: ${f.image}.`;
  }
  if (lower.includes('duck')) {
    const d = await j('https://random-d.uk/api/random');
    if (d?.url) return `Random duck image: ${d.url}.`;
  }
  if (lower.includes('bored')) {
    const b = await j('https://www.boredapi.com/api/activity');
    if (b?.activity) return `Activity idea: ${b.activity} (${b.type}).`;
  }
  if (lower.includes('advice')) {
    const a = await j('https://api.adviceslip.com/advice');
    if (a?.slip?.advice) return `Advice: ${a.slip.advice}.`;
  }
  if (lower.includes('quote')) {
    const q = await j('https://api.quotable.io/random');
    if (q?.content) return `Quote: "${q.content}" — ${q.author}.`;
  }
  if (lower.includes('word') || lower.includes('rhyme') || lower.includes('synonym')) {
    const term = extractAfter(text, ['for', 'with', 'word', 'rhyme', 'synonym']) || 'happy';
    const d = await j(`https://api.datamuse.com/words?rel_syn=${encodeURIComponent(term)}&max=5`);
    if (d?.length) return `Synonyms for "${term}": ${d.map((w) => w.word).join(', ')}.`;
  }
  return '';
}

// Maps — Nominatim (OpenStreetMap), Photon (free, no key)
async function fetchMaps(text) {
  const q = extractAfter(text, ['map of', 'location of', 'where is', 'address of', 'coordinates of', ' in ', ' of ']) || text;
  const nom = await j(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=1`);
  const r = nom?.[0];
  if (r) return `Location: ${r.display_name}. Latitude ${r.lat}, longitude ${r.lon}. Map: https://www.openstreetmap.org/?mlat=${r.lat}&mlon=${r.lon}&zoom=14.`;
  const ph = await j(`https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&limit=1`);
  const p = ph?.features?.[0];
  if (p) return `Location: ${p.properties.name}, ${p.properties.state || ''} ${p.properties.country || ''}. Coordinates: ${p.geometry.coordinates.join(', ')}.`;
  return '';
}

// Utilities — ipify, ip-api (free, no key)
async function fetchUtility(text) {
  const ip = await j('https://api.ipify.org?format=json');
  if (ip?.ip) {
    const loc = await j(`http://ip-api.com/json/${ip.ip}`);
    if (loc?.city) return `Your public IP: ${ip.ip} (${loc.city}, ${loc.regionName}, ${loc.country}).`;
    return `Your public IP: ${ip.ip}.`;
  }
  return '';
}

// Fake/sample data — RandomUser, DummyJSON, JSONPlaceholder (free, no key)
async function fetchFakeData(text) {
  const ru = await j('https://randomuser.me/api/?results=1');
  const p = ru?.results?.[0];
  if (p) return `Fake user: ${p.name.first} ${p.name.last}, ${p.dob.age}yo, ${p.location.city}, ${p.location.country}. Email: ${p.email}.`;
  const dj = await j('https://dummyjson.com/products/1');
  if (dj?.title) return `Sample product: ${dj.title} — $${dj.price}, ${dj.rating}★.`;
  const jp = await j('https://jsonplaceholder.typicode.com/users/1');
  if (jp?.name) return `Sample user: ${jp.name}, ${jp.email}, ${jp.address.city}.`;
  return '';
}

// Images — Lorem Picsum, DiceBear, RoboHash, Placehold.co (free URL generators, no key)
async function fetchImage(text) {
  const lower = (text || '').toLowerCase();
  const seed = Math.random().toString(36).slice(2, 8);
  if (/avatar/.test(lower)) return `Avatar image: https://api.dicebear.com/7.x/avataaars/png?seed=${seed} .`;
  if (/placeholder/.test(lower)) return `Placeholder image: https://placehold.co/600x400 .`;
  if (/robot/.test(lower)) return `Robot avatar: https://robohash.org/${seed}.png .`;
  return `Random image: https://picsum.photos/600/400 .`;
}

// Auto-generate a smart conversation title from the first user message.
export async function generateSmartTitle(userText) {
  try {
    const res = await base44.integrations.Core.InvokeLLM({
      prompt: `Generate a very short title (max 5 words, no quotes, no period) summarizing this user request:\n\n"${userText}"\n\nTitle:`,
      response_json_schema: { type: 'object', properties: { title: { type: 'string' } } },
    });
    const title = res?.title?.trim().replace(/^["']|["']$/g, '').slice(0, 60);
    return title || generateFallbackTitle(userText);
  } catch {
    return generateFallbackTitle(userText);
  }
}

function generateFallbackTitle(text) {
  const words = text.trim().split(/\s+/).slice(0, 5).join(' ');
  return words ? (words.length < text.trim().length ? words + '…' : words) : 'New Chat';
}
