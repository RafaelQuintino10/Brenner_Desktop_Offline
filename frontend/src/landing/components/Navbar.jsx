import React, { useEffect, useState } from 'react';
import { Menu, X, MessageCircle } from 'lucide-react';
import { content } from '../data/content';
import { whatsappLink } from '../config';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  return (
    <>
    <header className={`nav ${scrolled || open ? 'nav--scrolled' : ''}`} data-testid="navbar">
      <div className="container nav__inner">
        <a href="#inicio" className="nav__brand" data-testid="nav-brand">
          <span className="nav__brand-mark">
            <span className="nav__brand-ball" />
            <span className="nav__brand-stripes" />
            <span className="nav__brand-ball nav__brand-ball--sm" />
          </span>
          <span className="nav__brand-text">
            <span>{content.brand.first}</span>
            <em>{content.brand.second}</em>
          </span>
        </a>

        <nav className="nav__links">
          {content.nav.map((item) => (
            <a key={item.href} href={item.href} className="nav__link" data-testid={`nav-link-${item.href.slice(1)}`}>
              {item.label}
            </a>
          ))}
        </nav>

        {/* <a
          href={whatsappLink()}
          target="_blank"
          rel="noreferrer"
          className="btn btn-gold nav__cta"
          data-testid="nav-whatsapp-btn"
        > */}
        <a
            href="#agendar"
            className="btn btn-gold nav__cta"
          >
          <MessageCircle size={18} />
          Agendar horário
        </a>

        <button
          type="button"
          className="nav__toggle"
          aria-label={open ? 'Fechar menu' : 'Abrir menu'}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          data-testid="nav-toggle"
        >
          {open ? <X size={26} /> : <Menu size={26} />}
        </button>
      </div>
    </header>

      <div className={`nav__mobile ${open ? 'is-open' : ''}`} data-testid="nav-mobile-menu">
        {content.nav.map((item, i) => (
          <a
            key={item.href}
            href={item.href}
            className="nav__mobile-link"
            style={{ transitionDelay: `${80 + i * 60}ms` }}
            onClick={() => setOpen(false)}
          >
            {item.label}
          </a>
        ))}
        <a
          href={whatsappLink()}
          target="_blank"
          rel="noreferrer"
          className="btn btn-whats"
          style={{ transitionDelay: '360ms' }}
          onClick={() => setOpen(false)}
        >
          <MessageCircle size={18} />
          Agendar pelo WhatsApp
        </a>
      </div>
    </>
  );
}
