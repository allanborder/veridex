import React, { useState } from 'react';
import { Clock, CheckCircle2, HelpCircle, AlertTriangle, MinusCircle, ArrowRight, Trash2 } from 'lucide-react';
import VerificationAnswer from './VerificationAnswer';

export default function HistoryView({ history = [], onClearHistory }) {
  const [selectedItem, setSelectedItem] = useState(null);

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    if (s.includes('CONTRADICT')) {
      return { label: 'Contradicted', color: '#FF453A', icon: AlertTriangle };
    }
    if (s.includes('ABSTAIN')) {
      return { label: 'Abstained', color: '#98989D', icon: MinusCircle };
    }
    if (s.includes('PARTIAL') || s.includes('UNCERTAIN')) {
      return { label: 'Uncertain', color: '#FF9F0A', icon: HelpCircle };
    }
    return { label: 'Supported', color: '#30D158', icon: CheckCircle2 };
  };

  return (
    <div style={{ maxWidth: '780px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem', paddingTop: '0.5rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0 0 0.25rem 0', color: '#fff', letterSpacing: '-0.02em' }}>
            History
          </h2>
          <p style={{ color: '#8E8E93', margin: 0, fontSize: '0.86rem' }}>
            Recent queries and their verification results.
          </p>
        </div>

        {history.length > 0 && onClearHistory && (
          <button
            onClick={onClearHistory}
            className="apple-btn"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '10px',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              color: '#8E8E93',
              fontSize: '0.78rem',
              cursor: 'pointer'
            }}
          >
            <Trash2 size={13} />
            Clear
          </button>
        )}
      </div>

      {/* Detail Modal / Panel if selected */}
      {selectedItem && (
        <div
          className="apple-glass animate-materialize"
          style={{
            borderRadius: '20px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.76rem', color: '#8E8E93', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Query Inspection
            </span>
            <button
              onClick={() => setSelectedItem(null)}
              className="apple-btn"
              style={{
                background: 'none',
                border: 'none',
                color: '#0A84FF',
                fontSize: '0.82rem',
                cursor: 'pointer'
              }}
            >
              Close inspection &times;
            </button>
          </div>

          <div style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff' }}>
            "{selectedItem.question}"
          </div>

          <VerificationAnswer response={selectedItem.response} />
        </div>
      )}

      {/* History Items List (Apple Grouped Table) */}
      <div
        className="apple-glass"
        style={{
          borderRadius: '20px',
          overflow: 'hidden'
        }}
      >
        {history.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#8E8E93', fontSize: '0.88rem' }}>
            No recent questions. Ask a question to see verification history here.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {history.map((item, idx) => {
              const badge = getStatusBadge(item.status);
              const BadgeIcon = badge.icon;
              const timeStr = item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

              return (
                <div
                  key={idx}
                  onClick={() => setSelectedItem(item)}
                  style={{
                    padding: '14px 18px',
                    borderBottom: idx < history.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    transition: 'background-color 0.15s ease'
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.025)')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <BadgeIcon size={16} color={badge.color} />
                    <div>
                      <div style={{ color: '#ffffff', fontSize: '0.9rem', fontWeight: 500 }}>
                        {item.question}
                      </div>
                      {timeStr && (
                        <div style={{ fontSize: '0.72rem', color: '#8E8E93', marginTop: '2px' }}>
                          {timeStr}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      fontSize: '0.74rem',
                      color: badge.color,
                      fontWeight: 600
                    }}>
                      {badge.label}
                    </span>
                    <ArrowRight size={14} color="#636366" />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
