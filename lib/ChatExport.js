export function exportConversationToMarkdown(conversation, messages) {
  const title = conversation?.title || 'Chat';
  const date = new Date().toLocaleString();
  let md = `# ${title}\n\n_Exported ${date}_\n\n---\n\n`;
  for (const m of messages) {
    if (m.id === 'streaming' || m.id === 'error') continue;
    const role = m.role === 'user' ? '🧑 You' : m.role === 'assistant' ? '🤖 Bloxy-bot' : '⚙️ System';
    md += `### ${role}\n\n${m.content}\n\n`;
  }
  return md;
}

export function downloadText(filename, text) {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
