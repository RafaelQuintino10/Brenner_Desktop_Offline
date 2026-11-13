import React from 'react';

export default function SectionTitle({ title, sub, align = 'center', as: Tag = 'h2' }) {
  return (
    <div className={`section-head section-head--${align}`}>
      <Tag className="section-title">
        <span className="rule" />
        <span>{title}</span>
        <span className="rule" />
      </Tag>
      {sub && <p className="section-sub">{sub}</p>}
    </div>
  );
}
