import { downloadText } from '@/lib/chatExport';

function escapeCsv(val) {
  if (val == null) return '';
  const s = String(val);
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function buildChatsCsv(conversations, messages) {
  const rows = [['Conversation', 'Role', 'Model', 'Created', 'Message']];
  for (const conv of conversations) {
    const convMsgs = messages.filter(m => m.conversation_id === conv.id);
    if (convMsgs.length === 0) {
      rows.push([escapeCsv(conv.title), '', '', '', '']);
      continue;
    }
    for (const m of convMsgs) {
      rows.push([
        escapeCsv(conv.title),
        m.role,
        m.model || '',
        m.created_date ? new Date(m.created_date).toISOString() : '',
        escapeCsv(m.content),
      ]);
    }
  }
  return rows.map(r => r.join(',')).join('\n');
}

export function buildPromptsCsv(prompts) {
  const rows = [['Title', 'Category', 'Use Count', 'Content']];
  for (const p of prompts) {
    rows.push([escapeCsv(p.title), p.category || '', String(p.use_count || 0), escapeCsv(p.content)]);
  }
  return rows.map(r => r.join(',')).join('\n');
}

export { downloadText };
