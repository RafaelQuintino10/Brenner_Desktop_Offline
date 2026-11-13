import React from 'react';

/**
 * Navalha (straight razor) em SVG - icone ornamental dourado
 */
export default function RazorIcon({ size = 64, className = '', flip = false, ...rest }) {
  return (
    <svg
      width={size}
      height={size * 0.42}
      viewBox="0 0 200 84"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={flip ? { transform: 'scaleX(-1)' } : undefined}
      aria-hidden="true"
      {...rest}
    >
      <defs>
        <linearGradient id="razorBlade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#f7f7f7" />
          <stop offset="0.45" stopColor="#bfc3c9" />
          <stop offset="0.55" stopColor="#e9ebee" />
          <stop offset="1" stopColor="#8d9298" />
        </linearGradient>
        <linearGradient id="razorHandle" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#6b4a2b" />
          <stop offset="0.5" stopColor="#3b2715" />
          <stop offset="1" stopColor="#241709" />
        </linearGradient>
        <linearGradient id="razorGold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f3dc9a" />
          <stop offset="0.5" stopColor="#c9a24a" />
          <stop offset="1" stopColor="#8a6a2a" />
        </linearGradient>
      </defs>
      {/* Lamina */}
      <path
        d="M18 52 C 40 30, 90 22, 150 26 L 150 44 C 100 46, 60 50, 30 60 Z"
        fill="url(#razorBlade)"
        stroke="#6c7076"
        strokeWidth="1.5"
      />
      <path d="M28 56 C 60 46, 100 40, 148 40" stroke="#ffffff" strokeOpacity="0.6" strokeWidth="1.2" />
      {/* Pino / articulacao */}
      <circle cx="152" cy="35" r="6" fill="url(#razorGold)" stroke="#5c4518" strokeWidth="1" />
      {/* Cabo */}
      <path
        d="M150 28 L 190 40 C 196 42, 196 52, 190 54 L 150 62 C 146 62, 144 58, 146 54 L 148 46 C 149 40, 148 32, 150 28 Z"
        fill="url(#razorHandle)"
        stroke="#1a1008"
        strokeWidth="1.2"
      />
      <path d="M156 36 L 186 45" stroke="#9c7a4e" strokeOpacity="0.5" strokeWidth="1.3" />
      <circle cx="184" cy="47" r="2.2" fill="url(#razorGold)" />
    </svg>
  );
}
