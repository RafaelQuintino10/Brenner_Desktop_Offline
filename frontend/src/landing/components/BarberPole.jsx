import React from 'react';

/**
 * Poste de barbeiro animado (CSS puro).
 * As listras giram continuamente via background-position.
 */
export default function BarberPole({ className = '', height = 320, speed = 2.6, style }) {
  return (
    <div
      className={`pole ${className}`}
      style={{ '--pole-h': `${height}px`, '--pole-speed': `${speed}s`, ...style }}
      aria-hidden="true"
    >
      <div className="pole__glow" />
      <div className="pole__ball pole__ball--top" />
      <div className="pole__cap pole__cap--top" />
      <div className="pole__body">
        <div className="pole__stripes" />
        <div className="pole__shade" />
        <div className="pole__gloss" />
      </div>
      <div className="pole__cap pole__cap--bottom" />
      <div className="pole__ball pole__ball--bottom" />
    </div>
  );
}
