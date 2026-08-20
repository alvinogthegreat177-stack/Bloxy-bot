/**
 * Base44 frontend -> Bloxy Nexus direct HTTPS bridge.
 * This is the same engine bridge included in the integrated export ZIP.
 */
const DEFAULT_NEXUS_URL = 'https://bloxy-nexus.onrender.com';
export const NEXUS_URL = (import.meta?.env?.VITE_BLOXY_NEXUS_URL || DEFAULT_NEXUS_URL).replace(/\/+$/, '');

export async function runBloxy({ messages = [], conversationId = null, signal } = {}) {
  const history = messages.slice(-12).map((m) => ({ role: m.role, content: String(m.content ?? '') })).filter((m) => m.content.trim());
  const latestUser = [...history].reverse().find((m) => m.role === 'user');
  if (!latestUser?.content?.trim()) throw new Error('Message is empty');

  const response = await fetch(`${NEXUS_URL}/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ message: latestUser.content, conversation_id: conversationId, stream: false }),
    signal,
  });

  let payload = null;
  try { payload = await response.json(); } catch {}
  if (!response.ok) throw new Error(String(payload?.detail || payload?.error || `Bloxy Nexus returned HTTP ${response.status}`));
  if (!payload?.answer) throw new Error('Bloxy Nexus returned an empty answer');

  return {
    content: String(payload.answer),
    model: payload?.model || payload?.provider || 'Bloxy Nexus',
    sources: payload?.nexus?.sources_consulted || [],
    nexus: payload?.nexus || null,
  };
}
