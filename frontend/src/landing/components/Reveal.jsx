import React from 'react';
import { useReveal } from '../hooks/useReveal';

/**
 * Wrapper de animacao: fade + slide ao rolar.
 * direction: 'up' | 'down' | 'left' | 'right' | 'zoom'
 */
export default function Reveal({
  children,
  direction = 'up',
  delay = 0,
  className = '',
  as: Tag = 'div',
  ...rest
}) {
  const [ref, visible] = useReveal();
  return (
    <Tag
      ref={ref}
      className={`reveal reveal--${direction} ${visible ? 'is-visible' : ''} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
      {...rest}
    >
      {children}
    </Tag>
  );
}
