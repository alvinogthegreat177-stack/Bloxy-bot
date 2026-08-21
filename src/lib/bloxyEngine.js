/** Direct client bridge from the Base44-derived UI to Bloxy Nexus. */
const DEFAULT_NEXUS_URL = 'https://bloxy-nexus.onrender.com';

export const NEXUS_URL = String(import.meta.env.VITE_BLOXY_NEXUS_URL || DEFAULT_NEXUS_URL).replace(/\/+$/, '');

export async function runBloxy({ messages = [], conversationId = null, signal } = {}) {
  const history = messages
    .slice(-12)
    .map((message) => ({ role: message.role, content: String(message.content ?? '') }))
    .filter((message) => message.content.trim());
  const latestUser = [...history].reverse().find((message) => message.role === 'user');
  if (!latestUser?.content?.trim()) throw new Error('Message is empty');

  const response = await fetch(`${NEXUS_URL}/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      message: latestUser.content,
      conversation_id: conversationId,
      stream: false,
    }),
    signal,
  });

  let payload = null;
  try { payload = await response.json(); } catch { payload = null; }
  if (!response.ok) {
    throw new Error(String(payload?.detail || payload?.error || `Bloxy Nexus returned HTTP ${response.status}`));
  }

  const content = payload?.answer ?? payload?.content ?? payload?.response;
  if (!content) throw new Error('Bloxy Nexus returned an empty answer');

  return {
    content: String(content),
    model: payload?.model || payload?.provider || 'Bloxy Nexus',
    sources: payload?.nexus?.sources_consulted || [],
    nexus: payload?.nexus || null,
  };
}

export function generateSmartTitle(userMessage = '') {
  const text = String(userMessage).trim();
  if (!text) return 'New Chat';
  const title = text.replace(/\s+/g, ' ').replace(/[.!?]+$/g, '').split(' ').slice(0, 7).join(' ');
  return title.length > 48 ? `${title.slice(0, 47).trimEnd()}…` : title;
}
