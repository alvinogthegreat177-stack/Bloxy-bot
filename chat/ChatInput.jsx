import React, { useState, useRef } from 'react';
import { Send, Paperclip, Mic, Sparkles, StopCircle, Loader2, Square, Brain, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { base44 } from '@/api/base44Client';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { useLanguage } from '@/lib/LanguageContext';

export default function ChatInput({ onSend, isLoading, onStop, nexusMode, onToggleNexusMode, draft, onDraftChange, sendOnEnter = true }) {
  const [attachments, setAttachments] = useState([]);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const { t } = useLanguage();
  const { isRecording, isTranscribing, startRecording, stopRecording } = useVoiceRecorder({
    onTranscribed: (text) => onDraftChange((draft ? draft + ' ' : '') + (text || '').trim()),
  });

  const handleSend = () => {
    if (!draft.trim() && attachments.length === 0) return;
    onSend(draft.trim(), attachments);
    onDraftChange('');
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (sendOnEnter && e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e) => {
    onDraftChange(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  };

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    for (const file of files) {
      const { file_url } = await base44.integrations.Core.UploadFile({ file });
      setAttachments(prev => [...prev, { name: file.name, url: file_url }]);
    }
  };

  return (
    <div className="px-4 pb-4 pt-2">
      {attachments.length > 0 && (
        <div className="flex gap-2 mb-2 flex-wrap">
          {attachments.map((a, i) => (
            <div key={i} className="flex items-center gap-1.5 bg-muted/50 rounded-lg px-3 py-1.5 text-xs">
              <Paperclip className="w-3 h-3 text-orange-400" />
              <span className="truncate max-w-[120px]">{a.name}</span>
              <button onClick={() => setAttachments(prev => prev.filter((_, j) => j !== i))} className="text-muted-foreground hover:text-foreground ml-1">×</button>
            </div>
          ))}
        </div>
      )}
      <div className="glass-card rounded-2xl flex items-end gap-2 p-2">
        <input type="file" ref={fileInputRef} className="hidden" multiple onChange={handleFileUpload} />
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 rounded-xl text-muted-foreground hover:text-orange-400 flex-shrink-0"
          onClick={() => fileInputRef.current?.click()}
        >
          <Paperclip className="w-4 h-4" />
        </Button>
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder={t('chat.placeholder')}
          rows={1}
          className="flex-1 bg-transparent border-none outline-none resize-none text-sm py-2 px-1 placeholder:text-muted-foreground/50 min-h-[36px] max-h-[200px]"
        />
        <Button
          variant="ghost"
          size="icon"
          onClick={isRecording ? stopRecording : startRecording}
          className={`h-9 w-9 rounded-xl flex-shrink-0 ${isRecording ? 'text-red-400 bg-red-500/10' : 'text-muted-foreground hover:text-blue-400'}`}
        >
          {isTranscribing ? <Loader2 className="w-4 h-4 animate-spin" /> : isRecording ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </Button>
        {nexusMode && onToggleNexusMode && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleNexusMode}
            className={`h-9 rounded-xl text-xs gap-1 flex-shrink-0 ${nexusMode === 'deep' ? 'text-orange-400 hover:text-orange-300' : 'text-blue-400 hover:text-blue-300'}`}
            title={nexusMode === 'deep' ? t('chat.deepTitle') : t('chat.saveTitle')}
          >
            {nexusMode === 'deep' ? <Brain className="w-3.5 h-3.5" /> : <Zap className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{nexusMode === 'deep' ? t('chat.deep') : t('chat.save')}</span>
          </Button>
        )}
        {isLoading ? (
          <Button
            onClick={onStop}
            size="icon"
            className="h-9 w-9 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-400 flex-shrink-0"
          >
            <StopCircle className="w-4 h-4" />
          </Button>
        ) : (
          <Button
            onClick={handleSend}
            size="icon"
            disabled={!draft.trim() && attachments.length === 0}
            className="h-9 w-9 rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white flex-shrink-0 disabled:opacity-30"
          >
            <Send className="w-4 h-4" />
          </Button>
        )}
      </div>
      <p className="text-[10px] text-muted-foreground/40 text-center mt-2">
        {t('chat.disclaimer')}
      </p>
    </div>
  );
}
