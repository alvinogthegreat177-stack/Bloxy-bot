// AI voice profiles for text-to-speech.
export const AI_VOICES = [
  { id: 'river', name: 'River', lang: 'en-US', rate: 1.0, pitch: 1.0, desc: 'Calm & neutral' },
  { id: 'honey', name: 'Honey', lang: 'en-US', rate: 0.9, pitch: 1.2, desc: 'Warm & soft' },
  { id: 'sunny', name: 'Sunny', lang: 'en-US', rate: 1.1, pitch: 1.3, desc: 'Bright & upbeat' },
  { id: 'storm', name: 'Storm', lang: 'en-GB', rate: 0.85, pitch: 0.7, desc: 'Formal & deep' },
  { id: 'spark', name: 'Spark', lang: 'en-US', rate: 1.2, pitch: 1.1, desc: 'Energetic & quick' },
];

export function getVoiceProfile(voiceId) {
  return AI_VOICES.find((voice) => voice.id === voiceId) || AI_VOICES[0];
}

export function stripForSpeech(text) {
  if (!text) return '';
  return String(text)
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/\bhttps?:\/\/\S+/gi, ' ')
    .replace(/\bwww\.\S+/gi, ' ')
    .replace(/\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b/g, ' ')
    .replace(/^\s{0,3}#{1,6}\s+/gm, '')
    .replace(/^\s*>\s?/gm, '')
    .replace(/^\s*(?:[-*+]|\d+[.)])\s+/gm, '')
    .replace(/[`*_~]/g, '')
    .replace(/[\\/|<>{}\[\]=$^~]/g, ' ')
    .replace(/:+/g, ' ')
    .replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2300}-\u{23FF}\u{FE00}-\u{FE0F}\u{200D}]/gu, '')
    .replace(/(^|\s)[.,!?;]+(?=\s|$)/g, '$1')
    .replace(/[-–—]{2,}/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();
}
