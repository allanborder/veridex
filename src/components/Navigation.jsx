import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Database, Clock } from 'lucide-react';
import { checkBackendHealth } from '../services/api';

const NAV_ITEMS = [
  { id: 'ask', label: 'Ask', icon: MessageSquare },
  { id: 'knowledge', label: 'Knowledge', icon: Database },
  { id: 'history', label: 'History', icon: Clock },
];

export default function Navigation({ activeTab, setActiveTab }) {
  const [online, setOnline] = useState(true);
  const [pillStyle, setPillStyle] = useState({ left: 0, width: 0, opacity: 0 });
  const navContainerRef = useRef(null);
  const buttonRefs = useRef({});

  useEffect(() => {
    let active = true;
    checkBackendHealth()
      .then(res => {
        if (active) setOnline(res && res.status === 'ok');
      })
      .catch(() => {
        if (active) setOnline(false);
      });
    return () => { active = false; };
  }, []);

  // Update physical sliding glass pill position whenever activeTab changes
  useEffect(() => {
    const activeBtn = buttonRefs.current[activeTab];
    const container = navContainerRef.current;
    if (activeBtn && container) {
      const btnRect = activeBtn.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      setPillStyle({
        left: btnRect.left - containerRect.left,
        width: btnRect.width,
        opacity: 1,
      });
    }
  }, [activeTab]);

  return (
    <div style={{
      position: 'sticky',
      top: '1.15rem',
      zIndex: 100,
      width: '100%',
      display: 'flex',
      justifyContent: 'center',
      padding: '0 1rem',
      pointerEvents: 'none',
    }}>
      <header
        style={{
          pointerEvents: 'auto',
          display: 'flex',
          alignItems: 'center',
          gap: '1.25rem',
          padding: '6px 14px',
          background: 'var(--glass-nav-bg)',
          backdropFilter: 'var(--glass-nav-blur)',
          WebkitBackdropFilter: 'var(--glass-nav-blur)',
          border: '1px solid var(--glass-nav-border)',
          borderRadius: '20px',
          boxShadow: 'var(--glass-nav-shadow)',
          transition: 'all 0.24s cubic-bezier(0.16, 1, 0.3, 1)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Top edge physical specular highlight */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: '10%',
            right: '10%',
            height: '1px',
            background: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.28) 50%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Brand */}
        <div 
          onClick={() => setActiveTab('ask')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            paddingRight: '6px',
            userSelect: 'none',
            zIndex: 2,
          }}
        >
          <img
            src="/logo.png"
            alt="VERIDEX Logo"
            style={{ width: '22px', height: '22px', objectFit: 'contain', borderRadius: '5px' }}
          />
          <span style={{
            fontWeight: 700,
            fontSize: '0.86rem',
            letterSpacing: '0.08em',
            color: '#ffffff',
          }}>
            VERIDEX
          </span>
        </div>

        {/* Separator */}
        <div style={{ width: '1px', height: '14px', backgroundColor: 'rgba(255, 255, 255, 0.12)', zIndex: 2 }} />

        {/* Primary Navigation with Single Sliding Glass Pill Indicator */}
        <nav
          ref={navContainerRef}
          style={{
            display: 'flex',
            gap: '2px',
            alignItems: 'center',
            position: 'relative',
          }}
        >
          {/* Physical Sliding Glass Pill */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${pillStyle.left}px`,
              width: `${pillStyle.width}px`,
              opacity: pillStyle.opacity,
              backgroundColor: 'rgba(255, 255, 255, 0.105)',
              border: '1px solid rgba(255, 255, 255, 0.16)',
              borderRadius: '13px',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.18)',
              transition: 'all 280ms cubic-bezier(0.16, 1, 0.3, 1)',
              pointerEvents: 'none',
              zIndex: 1,
            }}
          />

          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                ref={(el) => (buttonRefs.current[item.id] = el)}
                onClick={() => setActiveTab(item.id)}
                className="apple-btn"
                style={{
                  padding: '6px 14px',
                  borderRadius: '13px',
                  fontSize: '0.82rem',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? '#ffffff' : '#8E8E93',
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  position: 'relative',
                  zIndex: 2,
                  transition: 'color 180ms ease, transform 160ms cubic-bezier(0.16, 1, 0.3, 1)',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.color = '#ffffff';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.color = '#8E8E93';
                }}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Separator */}
        <div style={{ width: '1px', height: '14px', backgroundColor: 'rgba(255, 255, 255, 0.12)', zIndex: 2 }} />

        {/* Connection Indicator Dot */}
        <div
          title={online ? 'Local Backend Active & Connected' : 'Offline Mode'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            paddingLeft: '2px',
            zIndex: 2,
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: online ? '#30D158' : '#FF453A',
              boxShadow: online ? '0 0 10px rgba(48, 209, 88, 0.8)' : 'none',
              transition: 'background-color 0.2s ease',
            }}
          />
        </div>
      </header>
    </div>
  );
}
