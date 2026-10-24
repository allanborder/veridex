import React, { useState } from 'react';
import Navigation from './components/Navigation';
import AskView from './components/AskView';
import KnowledgeView from './components/KnowledgeView';
import HistoryView from './components/HistoryView';
import AmbientBackground from './components/AmbientBackground';
import BootScreen from './components/BootScreen';

export default function App() {
  const [isBooting, setIsBooting] = useState(true);
  const [activeTab, setActiveTab] = useState('ask');
  const [history, setHistory] = useState([]);

  const handleSaveHistory = (entry) => {
    setHistory(prev => [entry, ...prev.filter(h => h.question !== entry.question)].slice(0, 30));
  };

  const handleClearHistory = () => {
    setHistory([]);
  };

  return (
    <div style={{ minHeight: '100vh', color: '#ffffff', display: 'flex', flexDirection: 'column', position: 'relative' }}>

      {/* ── Initial Boot Experience (runs only once on startup) ── */}
      {isBooting && (
        <BootScreen onComplete={() => setIsBooting(false)} />
      )}

      {/* ── Ambient spatial atmosphere (fixed, behind everything) ── */}
      <AmbientBackground />

      {/* ── Application layer (above background) ── */}
      <div
        className={!isBooting ? "animate-materialize" : ""}
        style={{
          position: 'relative',
          zIndex: 1,
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          opacity: isBooting ? 0 : 1,
          transition: 'opacity 300ms cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >

        {/* Floating Spatial Navigation */}
        <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Main content */}
        <main style={{ flex: 1, padding: '1rem 1.5rem 3.5rem 1.5rem' }}>
          {activeTab === 'ask' && <AskView onSaveHistory={handleSaveHistory} />}
          {activeTab === 'knowledge' && <KnowledgeView />}
          {activeTab === 'history' && <HistoryView history={history} onClearHistory={handleClearHistory} />}
        </main>

        {/* Apple-like minimal footer */}
        <footer style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.04)',
          padding: '1.25rem',
          textAlign: 'center',
          color: '#636366',
          fontSize: '0.74rem',
          letterSpacing: '0.02em'
        }}>
          VERIDEX &bull; Authorized Knowledge Verification
        </footer>
      </div>
    </div>
  );
}
