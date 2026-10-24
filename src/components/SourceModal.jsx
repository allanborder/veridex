import React, { useState, useEffect } from 'react';
import { FileText, Download, X, Loader2 } from 'lucide-react';
import { downloadDocument, previewDocument } from '../services/api';

export default function SourceModal({ filename, onClose }) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await previewDocument(filename, 5000);
        if (active) setContent(data);
      } catch (err) {
        if (active) setError(err.message || 'Could not load document content.');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [filename]);

  // Keyboard accessibility: Escape key closes the modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleBackdrop = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div
      onClick={handleBackdrop}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        backgroundColor: 'rgba(0, 0, 0, 0.70)',
        backdropFilter: 'blur(20px) saturate(140%)',
        WebkitBackdropFilter: 'blur(20px) saturate(140%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
    >
      <div
        className="animate-sheet-in"
        style={{
          width: '100%',
          maxWidth: '740px',
          maxHeight: '85vh',
          backgroundColor: 'rgba(16, 18, 24, 0.90)',
          backdropFilter: 'blur(36px) saturate(160%)',
          WebkitBackdropFilter: 'blur(36px) saturate(160%)',
          border: '1px solid rgba(255, 255, 255, 0.14)',
          borderRadius: '26px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 32px 80px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.22)',
          position: 'relative',
        }}
      >
        {/* Top edge physical specular highlight */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '1px',
            background: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Header */}
        <div style={{
          padding: '18px 22px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={18} color="#0A84FF" />
            <div>
              <div style={{ color: '#ffffff', fontWeight: 600, fontSize: '0.94rem' }}>{filename}</div>
              <div style={{ color: '#8E8E93', fontSize: '0.72rem' }}>Authorized Knowledge Evidence</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => downloadDocument(filename)}
              className="apple-btn"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#fff',
                fontSize: '0.76rem',
                cursor: 'pointer'
              }}
            >
              <Download size={13} />
              Download
            </button>
            <button
              onClick={onClose}
              className="apple-btn"
              aria-label="Close"
              style={{
                padding: '6px',
                borderRadius: '10px',
                background: 'transparent',
                border: 'none',
                color: '#8E8E93',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '22px', minHeight: '200px' }}>
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '180px', color: '#8E8E93', gap: '8px', fontSize: '0.85rem' }}>
              <Loader2 size={16} className="animate-spin" />
              Loading authorized source document…
            </div>
          )}
          {error && (
            <div style={{ color: '#FF453A', fontSize: '0.85rem', padding: '1rem' }}>
              {error}
            </div>
          )}
          {content && (
            <div>
              <pre style={{
                margin: 0,
                fontFamily: 'var(--font-mono, monospace)',
                fontSize: '0.82rem',
                lineHeight: 1.65,
                color: '#e2e8f0',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}>
                {content.preview}
              </pre>
              {content.truncated && (
                <div style={{
                  marginTop: '1.25rem',
                  padding: '8px 12px',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  fontSize: '0.75rem',
                  color: '#8E8E93'
                }}>
                  Showing excerpt ({content.total_chars.toLocaleString()} characters total). Download document to view full original file.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
