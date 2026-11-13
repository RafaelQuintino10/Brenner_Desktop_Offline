import React from 'react';
import { Scissors, Clock, MapPin, MessageCircle } from 'lucide-react';
import { content } from '../data/content';
import { whatsappLink } from '../config';

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="footer" data-testid="footer">
      <div className="container footer__inner">
        <div className="footer__brand">
          <div className="footer__logo">
            <Scissors size={20} />
          </div>
          <div>
            <p className="footer__name">
              {content.brand.first} <em>{content.brand.second}</em>
            </p>
            <p className="footer__tag">{content.services.items.slice(0, 3).map((s) => s.title).join(' | ')}</p>
          </div>
        </div>

        <ul className="footer__info">
          <li>
            <Clock size={16} />
            {content.hours.slots.map((s) => `${s.open} - ${s.close}`).join('  |  ')}
          </li>
          <li>
            <MapPin size={16} />
            {content.address.line1} {content.address.line2}
          </li>
        </ul>

        <a
          href={whatsappLink()}
          target="_blank"
          rel="noreferrer"
          className="btn btn-whats footer__btn"
          data-testid="footer-whatsapp-btn"
        >
          <MessageCircle size={18} />
          WhatsApp
        </a>
      </div>
      <div className="footer__bottom">
        <div className="ornament">
          <span />
          <Scissors size={14} />
          <span />
        </div>
        <p>
          &copy; {year} {content.footer.rights}
        </p>
      </div>
    </footer>
  );
}
