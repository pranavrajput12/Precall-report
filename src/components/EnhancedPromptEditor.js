import React, { useState, useCallback } from 'react';
import CodeEditor from '@uiw/react-textarea-code-editor';
import Prism from 'prismjs';
import 'prismjs/components/prism-core';
import 'prismjs/components/prism-clike';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-markup'; // <-- Add this line before markdown
import 'prismjs/components/prism-markdown';
import 'prismjs/themes/prism.css';
import toast from 'react-hot-toast';

const EnhancedPromptEditor = ({ 
  value = '', 
  onChange, 
  placeholder = 'Enter your prompt here...',
  language = 'markdown',
  readOnly = false,
  minHeight = 200,
  maxHeight = 600,
  showLineNumbers = true,
  theme = 'light'
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);

  const handleCodeChange = useCallback((val) => {
    onChange(val);
    setWordCount(val.trim().split(/\s+/).filter(word => word.length > 0).length);
    setCharCount(val.length);
  }, [onChange]);

  const highlightCode = useCallback((code) => {
    try {
      switch (language) {
        case 'javascript':
          return Prism.highlight(code, Prism.languages.javascript, 'javascript');
        case 'python':
          return Prism.highlight(code, Prism.languages.python, 'python');
        case 'markdown':
          return Prism.highlight(code, Prism.languages.markdown, 'markdown');
        default:
          return code;
      }
    } catch (error) {
      console.warn('Syntax highlighting error:', error);
      return code;
    }
  }, [language]);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    toast.success(`${isFullscreen ? 'Exited' : 'Entered'} fullscreen mode`);
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(value);
      toast.success('Prompt copied to clipboard!');
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const formatPrompt = () => {
    // Simple formatting for prompts
    const formatted = value
      .replace(/\n\n+/g, '\n\n') // Remove multiple line breaks
      .replace(/^\s+/gm, '') // Remove leading whitespace
      .replace(/\s+$/gm, '') // Remove trailing whitespace
      .trim();
    
    onChange(formatted);
    toast.success('Prompt formatted!');
  };

  const insertTemplate = (template) => {
    const templates = {
      task: '## Task\n\nDescribe what you want the agent to do:\n\n## Context\n\nProvide relevant context:\n\n## Expected Output\n\nDescribe the expected result:\n\n',
      role: '## Role\n\nYou are a {role} with expertise in {domain}.\n\n## Responsibilities\n\n- {responsibility1}\n- {responsibility2}\n- {responsibility3}\n\n## Guidelines\n\n- {guideline1}\n- {guideline2}\n\n',
      analysis: '## Analysis Task\n\n### Input Data\n{input_description}\n\n### Analysis Required\n1. {analysis_type1}\n2. {analysis_type2}\n3. {analysis_type3}\n\n### Output Format\n{output_format}\n\n### Success Criteria\n{success_criteria}\n\n'
    };

    const templateText = templates[template] || '';
    const newValue = value + (value ? '\n\n' : '') + templateText;
    onChange(newValue);
    toast.success(`${template} template inserted!`);
  };

  return (
    <div className={`enhanced-prompt-editor ${isFullscreen ? 'fullscreen' : ''} ${theme}`}>
      <div className="editor-header">
        <div className="editor-controls">
          <select 
            value={language} 
            onChange={(e) => onChange(e.target.value)}
            className="language-selector"
          >
            <option value="markdown">Markdown</option>
            <option value="javascript">JavaScript</option>
            <option value="python">Python</option>
          </select>
          
          <div className="template-dropdown">
            <select 
              onChange={(e) => {
                if (e.target.value) {
                  insertTemplate(e.target.value);
                  e.target.value = '';
                }
              }}
              className="template-selector"
            >
              <option value="">Insert Template...</option>
              <option value="task">Task Template</option>
              <option value="role">Role Template</option>
              <option value="analysis">Analysis Template</option>
            </select>
          </div>
        </div>

        <div className="editor-actions">
          <button 
            onClick={formatPrompt}
            className="action-btn"
            title="Format Prompt"
          >
            📝 Format
          </button>
          <button 
            onClick={copyToClipboard}
            className="action-btn"
            title="Copy to Clipboard"
          >
            📋 Copy
          </button>
          <button 
            onClick={toggleFullscreen}
            className="action-btn"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? '🗗' : '🗖'} {isFullscreen ? 'Exit' : 'Full'}
          </button>
        </div>
      </div>

      <div className="editor-container">
        <CodeEditor
          value={value}
          language={language}
          placeholder={placeholder}
          onChange={handleCodeChange}
          highlight={highlightCode}
          padding={15}
          style={{
            fontSize: 14,
            backgroundColor: theme === 'dark' ? '#1a1a1a' : '#ffffff',
            color: theme === 'dark' ? '#ffffff' : '#000000',
            fontFamily: 'ui-monospace, SFMono-Regular, SF Mono, Consolas, Liberation Mono, Menlo, monospace',
            minHeight: isFullscreen ? '80vh' : `${minHeight}px`,
            maxHeight: isFullscreen ? '80vh' : `${maxHeight}px`,
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            lineHeight: '1.6',
          }}
          data-color-mode={theme}
          readOnly={readOnly}
        />
      </div>

      <div className="editor-footer">
        <div className="editor-stats">
          <span className="stat">Words: {wordCount}</span>
          <span className="stat">Characters: {charCount}</span>
          <span className="stat">Lines: {value.split('\n').length}</span>
        </div>
        
        <div className="editor-hints">
          <span className="hint">💡 Use Ctrl+/ for quick formatting</span>
          <span className="hint">🎯 Templates help structure prompts</span>
        </div>
      </div>

      <style>{`
        .enhanced-prompt-editor {
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          overflow: hidden;
          background: white;
          transition: all 0.3s ease;
        }

        .enhanced-prompt-editor.fullscreen {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          border-radius: 0;
          border: none;
        }

        .enhanced-prompt-editor.dark {
          background: #1a1a1a;
          border-color: #374151;
        }

        .editor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: #f8fafc;
          border-bottom: 1px solid #e2e8f0;
        }

        .enhanced-prompt-editor.dark .editor-header {
          background: #2d3748;
          border-bottom-color: #4a5568;
        }

        .editor-controls {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .language-selector,
        .template-selector {
          padding: 6px 12px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
          font-size: 12px;
          cursor: pointer;
        }

        .enhanced-prompt-editor.dark .language-selector,
        .enhanced-prompt-editor.dark .template-selector {
          background: #374151;
          border-color: #4a5568;
          color: white;
        }

        .editor-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          padding: 6px 12px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          transition: background 0.2s;
        }

        .action-btn:hover {
          background: #2563eb;
        }

        .editor-container {
          position: relative;
        }

        .editor-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 16px;
          background: #f8fafc;
          border-top: 1px solid #e2e8f0;
          font-size: 12px;
        }

        .enhanced-prompt-editor.dark .editor-footer {
          background: #2d3748;
          border-top-color: #4a5568;
        }

        .editor-stats {
          display: flex;
          gap: 16px;
        }

        .stat {
          color: #6b7280;
          font-weight: 500;
        }

        .enhanced-prompt-editor.dark .stat {
          color: #9ca3af;
        }

        .editor-hints {
          display: flex;
          gap: 16px;
        }

        .hint {
          color: #6b7280;
          font-size: 11px;
        }

        .enhanced-prompt-editor.dark .hint {
          color: #9ca3af;
        }

        @media (max-width: 768px) {
          .editor-header {
            flex-direction: column;
            gap: 12px;
          }

          .editor-hints {
            display: none;
          }

          .editor-footer {
            flex-direction: column;
            gap: 8px;
          }
        }
      `}</style>
    </div>
  );
};

export default EnhancedPromptEditor; 