// AI voice profiles for text-to-speech.
// Each voice maps to SpeechSynthesis settings (rate, pitch, lang preference).
export const AI_VOICES = [
  { id: 'river', name: 'River', lang: 'en-US', rate: 1.0, pitch: 1.0, desc: 'Calm & neutral' },
  { id: 'honey', name: 'Honey', lang: 'en-US', rate: 0.9, pitch: 1.2, desc: 'Warm & soft' },
  { id: 'sunny', name: 'Sunny', lang: 'en-US', rate: 1.1, pitch: 1.3, desc: 'Bright & upbeat' },
  { id: 'storm', name: 'Storm', lang: 'en-GB', rate: 0.85, pitch: 0.7, desc: 'Formal & deep' },
  { id: 'spark', name: 'Spark', lang: 'en-US', rate: 1.2, pitch: 1.1, desc: 'Energetic & quick' },
];

export function getVoiceProfile(voiceId) {
  return AI_VOICES.find(v => v.id === voiceId) || AI_VOICES[0];
}

// Strip emojis and markdown formatting from text for clean TTS reading.
export function stripForSpeech(text) {
  if (!text) return '';
  return text
    // Remove emojis
    .replace(/[\u{1F600}-\u{1F64F}]/gu, '')
    .replace(/[\u{1F300}-\u{1F5FF}]/gu, '')
    .replace(/[\u{1F680}-\u{1F6FF}]/gu, '')
    .replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '')
    .replace(/[\u{2600}-\u{27BF}]/gu, '')
    .replace(/[\u{FE00}-\u{FE0F}]/gu, '')
    .replace(/[\u{1F900}-\u{1F9FF}]/gu, '')
    .replace(/[\u{1FA00}-\u{1FAFF}]/gu, '')
    .replace(/[\u{1F000}-\u{1F02F}]/gu, '')
    .replace(/[\u{1F0A0}-\u{1F0FF}]/gu, '')
    .replace(/\u200D/g, '')
    // Remove markdown formatting
    .replace(/```[\s\S]*?```/g, ' code block ')
    .replace(/[#*`>_\[\]()]/g, '')
    .replace(/!\[.*?\]\(.*?\)/g, '')
    .replace(/\[(.*?)\]\(.*?\)/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
