import React, { useEffect, useState } from 'react';
import { Clock, CalendarDays, MapPin, Navigation, Flame, MessageCircle, Info } from 'lucide-react';
import Reveal from './Reveal';
import RazorIcon from './RazorIcon';
import BarberPole from './BarberPole';
import SectionTitle from './SectionTitle';
import { content } from '../data/content';
import { whatsappLink } from '../config';

function toMinutes(hhmm) {
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
}

function useOpenStatus(slots) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const check = () => {
      const now = new Date();
      const mins = now.getHours() * 60 + now.getMinutes();
      const isSunday = now.getDay() === 0;
      const inside = slots.some((s) => mins >= toMinutes(s.open) && mins <= toMinutes(s.close));
      setOpen(!isSunday && inside);
    };
    check();
    const id = setInterval(check, 60 * 1000);
    return () => clearInterval(id);
  }, [slots]);
  return open;
}

/* ---------------- Horários + Endereço ---------------- */
export function HoursAddress() {
  const { hours, address } = content;
  const isOpen = useOpenStatus(hours.slots);
  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address.mapsQuery)}`;
  const embedUrl = `https://maps.google.com/maps?q=${encodeURIComponent(address.mapsQuery)}&t=&z=16&ie=UTF8&iwloc=&output=embed`;

  return (
    <section id="horarios" className="section info" data-testid="hours-section">
      <div className="container info__grid">
        {/* Horários */}
        <Reveal direction="left" className="info__col">
          <div className="gold-card info__card hours" data-testid="hours-card">
            <SectionTitle title={hours.title} align="left" as="h2" />
            <div className="hours__meta">
              <span className="hours__days">
                <CalendarDays size={16} /> {hours.days}
              </span>
              <span className={`hours__status ${isOpen ? 'is-open' : ''}`} data-testid="hours-status">
                <span className="hours__dot" />
                {isOpen ? 'Aberto agora' : 'Fechado no momento'}
              </span>
            </div>

            <div className="hours__slots">
              {hours.slots.map((slot, i) => (
                <div className="hours__slot" key={slot.open} data-testid={`hours-row-${i}`}>
                  <span className="hours__clock">
                    <Clock size={30} strokeWidth={1.6} />
                  </span>
                  <div className="hours__time">
                    <small>{slot.label}</small>
                    <div>
                      <strong>{slot.open}</strong>
                      <em>às</em>
                      <strong>{slot.close}</strong>
                    </div>
                  </div>
                  <RazorIcon size={86} className="hours__razor" />
                </div>
              ))}
            </div>

            <p className="hours__note">
              <Info size={18} />
              <span>
                <strong>Atendimento com hora marcada.</strong> Garanta seu horário pelo WhatsApp e evite esperas.
                Fechamos aos domingos.
              </span>
            </p>
          </div>
        </Reveal>

        {/* Endereço */}
        <Reveal direction="right" delay={120} className="info__col" id="localizacao">
          <div className="gold-card info__card address" data-testid="address-section">
            <div className="address__head">
              <span className="address__pin">
                <MapPin size={28} strokeWidth={1.7} />
              </span>
              <div>
                <h2 className="address__title">{address.title}</h2>
                <p className="address__line" data-testid="address-line">
                  {address.line1}
                  <br />
                  {address.line2}
                </p>
              </div>
            </div>

            <a href={mapsUrl} target="_blank" rel="noreferrer" className="address__map" aria-label="Abrir no Google Maps">
              <iframe
                title="Mapa - Barbearia Brenner"
                src={embedUrl}
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                tabIndex={-1}
              />
              <span className="address__map-tag">
                <Navigation size={14} /> Barbearia Brenner
              </span>
            </a>

            <div className="address__actions">
              <a href="#agendar" className="btn btn-gold" data-testid="address-whatsapp-btn">
                <MessageCircle size={18} />
                {address.button}
              </a>
              <a href={mapsUrl} target="_blank" rel="noreferrer" className="btn btn-outline" data-testid="address-maps-btn">
                <Navigation size={18} />
                Como chegar
              </a>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ---------------- CTA final ---------------- */
export function FinalCta() {
  const { finalCta } = content;
  return (
    <section className="section final" data-testid="final-cta-section">
      <BarberPole className="final__pole final__pole--l" height={240} speed={3} />
      <BarberPole className="final__pole final__pole--r" height={240} speed={3.3} />
      <div className="container final__inner">
        <Reveal direction="up">
          <div className="final__flame">
            <Flame size={32} />
          </div>
          <h2 className="final__headline" data-testid="final-headline">
            {finalCta.headline} <br />
            <span className="gold-text display final__brand">{finalCta.brand}</span>
          </h2>
          <p className="final__sub">{finalCta.sub}</p>
        </Reveal>
        <Reveal direction="up" delay={180}>
          <p className="final__closing">{finalCta.closing}</p>
          <a href="#agendar" className="btn btn-gold final__btn" data-testid="final-whatsapp-btn">
            <MessageCircle size={20} />
            {finalCta.button}
          </a>
        </Reveal>
      </div>
    </section>
  );
}
