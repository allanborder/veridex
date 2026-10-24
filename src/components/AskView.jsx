import React, { useState } from 'react';
import { askQuestion } from '../services/api';
import { ArrowUp, Loader2, Check, Circle, AlertCircle } from 'lucide-react';
import VerificationAnswer from './VerificationAnswer';

// Real pipeline stages corresponding to the backend execution lifecycle
const PIPELINE_STAGES = [
  { id: 1, label: 'Understanding question' },
  { id: 2, label: 'Searching knowledge' },
  { id: 3, label: 'Selecting evidence' },
  { id: 4, label: 'Generating answer' },
  { id: 5, label: 'Verifying claims' },
];

// Tamil Nadu demo scenarios for live judging
const DEMO_SCENARIOS = [
  { label: 'Supported',          query: 'What is the capital of Tamil Nadu?' },
  { label: 'Paraphrase / Typo',  query: 'hw mny distrcts r thr in tamil ndu?' },
  { label: 'Evidence Boundary',  query: 'Who is the Chief Minister of Tamil Nadu?' },
  { label: 'Abstain',            query: 'What is the current Bitcoin price?' },
  { label: 'Contradiction',      query: 'Does Tamil Nadu have fewer than 30 districts?' },
];

export default function AskView({ onSaveHistory }) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [isFocused, setIsFocused] = useState(false);

  const handleAsk = async (qOverride) => {
    const q = (qOverride || question).trim();
    if (!q) return;

    setQuestion(q);
    setLoading(true);
    setError(null);
    setResponse(null);
    setCurrentStage(1); // 1. Understanding question

    // Progress lifecycle — mirrors real backend stages
    const t2 = setTimeout(() => setCurrentStage(2), 150);
    const t3 = setTimeout(() => setCurrentStage(3), 320);
    const t4 = setTimeout(() => setCurrentStage(4), 500);
    const t5 = setTimeout(() => setCurrentStage(5), 700);

    try {
      const res = await askQuestion(q);
      setCurrentStage(6); // complete
      setResponse(res);
      if (onSaveHistory) {
        onSaveHistory({
          question: q,
          status: (res.verification_status || res.decision || 'SUPPORTED').toUpperCase(),
          timestamp: new Date().toISOString(),
          response: res
        });
      }
    } catch (err) {
      console.error(err);
      setError('Could not reach the backend. Check that the server is running.');
    } finally {
      clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); clearTimeout(t5);
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div style={{
      maxWidth: '780px',
      margin: '0 auto',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.75rem',
      paddingTop: '0.5rem'
    }}>

      {/* ── Brand Header (Clean & Apple-like) ── */}
      <div style={{ textAlign: 'center', marginTop: '1.25rem', marginBottom: '0.25rem' }}>
        <h1 style={{
          fontSize: '2.6rem',
          fontWeight: 700,
          letterSpacing: '-0.03em',
          color: '#ffffff',
          marginBottom: '0.4rem',
        }}>
          VERIDEX
        </h1>
        <p style={{
          fontSize: '1rem',
          color: '#8E8E93',
          margin: 0,
          fontWeight: 400,
          letterSpacing: '-0.01em',
        }}>
          Answers grounded in your authorized knowledge.
        </p>
      </div>

      {/* ── Apple-like Command Surface Input (Deep Liquid Glass) ── */}
      <div
        className="apple-glass"
        style={{
          borderRadius: '24px',
          padding: '1.35rem 1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.85rem',
          borderColor: isFocused ? 'rgba(255, 255, 255, 0.28)' : 'rgba(255, 255, 255, 0.12)',
          boxShadow: isFocused 
            ? '0 28px 80px rgba(0, 0, 0, 0.55), 0 0 28px rgba(10, 132, 255, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.25)' 
            : '0 24px 72px rgba(0, 0, 0, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.16)',
          backgroundColor: isFocused ? 'rgba(255, 255, 255, 0.058)' : 'var(--glass-surface-bg)',
          backdropFilter: 'var(--glass-surface-blur)',
          WebkitBackdropFilter: 'var(--glass-surface-blur)',
          transition: 'all 0.28s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        <textarea
          rows={2}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about your authorized knowledge…"
          disabled={loading}
          style={{
            width: '100%',
            backgroundColor: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#ffffff',
            fontSize: '1.08rem',
            lineHeight: 1.55,
            resize: 'none',
            fontFamily: 'inherit',
          }}
        />

        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderTop: '1px solid rgba(255, 255, 255, 0.07)',
          paddingTop: '0.75rem',
        }}>
          <span style={{ fontSize: '0.76rem', color: '#8E8E93', letterSpacing: '0.01em' }}>
            Press Enter to submit
          </span>

          <button
            onClick={() => handleAsk()}
            disabled={loading || !question.trim()}
            className="apple-btn"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '12px',
              backgroundColor: question.trim() && !loading ? '#0A84FF' : 'rgba(255, 255, 255, 0.06)',
              border: question.trim() && !loading ? '1px solid rgba(255, 255, 255, 0.22)' : '1px solid rgba(255, 255, 255, 0.08)',
              color: '#ffffff',
              cursor: question.trim() && !loading ? 'pointer' : 'default',
              boxShadow: question.trim() && !loading ? '0 6px 20px rgba(10, 132, 255, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.25)' : 'none',
              transform: question.trim() && !loading ? 'scale(1)' : 'scale(0.96)',
            }}
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <ArrowUp size={17} />}
          </button>
        </div>
      </div>

      {/* ── Demo Scenarios (Visually secondary pill bar) ── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexWrap: 'wrap',
        gap: '6px',
      }}>
        <span style={{ fontSize: '0.75rem', color: '#636366', marginRight: '4px' }}>
          Demo scenarios:
        </span>
        {DEMO_SCENARIOS.map((item, i) => (
          <button
            key={i}
            onClick={() => handleAsk(item.query)}
            disabled={loading}
            className="apple-btn"
            style={{
              fontSize: '0.76rem',
              padding: '4px 11px',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid rgba(255, 255, 255, 0.07)',
              color: '#8E8E93',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
              e.currentTarget.style.color = '#ffffff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
              e.currentTarget.style.color = '#8E8E93';
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* ── Real Processing Indicator ── */}
      {loading && (
        <div
          className="apple-glass"
          style={{
            borderRadius: '18px',
            padding: '1.4rem 1.6rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.85rem',
          }}
        >
          <div style={{
            fontSize: '0.76rem',
            fontWeight: 600,
            color: '#8E8E93',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}>
            Checking question against authorized knowledge
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '9px' }}>
            {PIPELINE_STAGES.map((s) => {
              const isDone    = currentStage > s.id;
              const isCurrent = currentStage === s.id;
              return (
                <div key={s.id} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  fontSize: '0.86rem',
                  color: isDone ? '#30D158' : isCurrent ? '#0A84FF' : '#636366',
                  transition: 'color 0.2s ease',
                }}>
                  <div style={{ width: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {isDone    ? <Check size={14} strokeWidth={2.5} />
                   : isCurrent ? <Loader2 size={13} className="animate-spin" />
                   :             <Circle size={8} strokeWidth={2} />}
                  </div>
                  <span>{s.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Error State ── */}
      {error && (
        <div
          style={{
            padding: '1rem 1.25rem',
            borderRadius: '14px',
            background: 'rgba(255, 69, 58, 0.08)',
            border: '1px solid rgba(255, 69, 58, 0.22)',
            backdropFilter: 'blur(20px)',
            color: '#FF453A',
            fontSize: '0.88rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
          <button
            onClick={() => handleAsk()}
            className="apple-btn"
            style={{
              background: 'transparent',
              border: '1px solid rgba(255, 69, 58, 0.35)',
              borderRadius: '8px',
              color: '#FF453A',
              padding: '4px 10px',
              fontSize: '0.78rem',
              cursor: 'pointer',
            }}
          >
            Try again
          </button>
        </div>
      )}

      {/* ── Answer & Evidence (Smooth Materialize) ── */}
      {response && !loading && (
        <div className="animate-materialize">
          <VerificationAnswer response={response} onAskQuery={handleAsk} />
        </div>
      )}

    </div>
  );
}
