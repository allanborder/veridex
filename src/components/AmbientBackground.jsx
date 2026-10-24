import React, { useEffect, useState } from 'react';

/**
 * AmbientBackground
 * Deep Apple-inspired ambient lighting canvas.
 * Projects radiant, soft light fields (cyan-blue, frosty silver, deep slate)
 * that visibly pass through the floating Liquid Glass panels.
 * Respects prefers-reduced-motion.
 */
export default function AmbientBackground() {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mq.matches);
    const handler = (e) => setReducedMotion(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const base = {
    position: 'absolute',
    borderRadius: '50%',
    pointerEvents: 'none',
    willChange: 'transform',
  };

  const orbs = [
    {
      // Top Center: Radiant Apple Cyan-Blue Light Cone
      width: '60vw',
      height: '55vw',
      top: '-18vw',
      left: '20vw',
      background: 'radial-gradient(ellipse at center, rgba(10, 132, 255, 0.095) 0%, rgba(10, 132, 255, 0.035) 45%, transparent 70%)',
      filter: 'blur(90px)',
      animation: reducedMotion ? 'none' : 'ambientDrift1 18s ease-in-out infinite alternate',
    },
    {
      // Middle Right: Soft Frosty Silver/White Ambient Light
      width: '48vw',
      height: '48vw',
      top: '15vh',
      right: '-10vw',
      background: 'radial-gradient(ellipse at center, rgba(220, 232, 255, 0.055) 0%, rgba(160, 185, 220, 0.02) 50%, transparent 75%)',
      filter: 'blur(100px)',
      animation: reducedMotion ? 'none' : 'ambientDrift2 22s ease-in-out infinite alternate',
    },
    {
      // Bottom Left: Deep Indigo / Slate Spatial Glow
      width: '52vw',
      height: '50vw',
      bottom: '-12vw',
      left: '-10vw',
      background: 'radial-gradient(ellipse at center, rgba(60, 95, 180, 0.07) 0%, rgba(30, 50, 110, 0.02) 55%, transparent 80%)',
      filter: 'blur(95px)',
      animation: reducedMotion ? 'none' : 'ambientDrift3 16s ease-in-out infinite alternate',
    },
    {
      // Center Accent: Subtle Luminous Core
      width: '35vw',
      height: '35vw',
      top: '38vh',
      left: '32vw',
      background: 'radial-gradient(ellipse at center, rgba(255, 255, 255, 0.03) 0%, rgba(10, 132, 255, 0.015) 50%, transparent 75%)',
      filter: 'blur(80px)',
      animation: reducedMotion ? 'none' : 'ambientDrift1 26s ease-in-out infinite alternate-reverse',
    }
  ];

  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
        background: '#050507',
      }}
    >
      {/* Soft Vignette Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at 50% 35%, transparent 35%, rgba(5, 5, 7, 0.65) 100%)',
          pointerEvents: 'none',
        }}
      />
      {orbs.map((orb, i) => (
        <div key={i} style={{ ...base, ...orb }} />
      ))}
    </div>
  );
}
