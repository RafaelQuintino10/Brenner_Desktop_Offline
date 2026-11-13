import React, { useRef } from 'react';
import { MessageCircle, ChevronDown, Crown, Armchair, ShieldCheck, Users } from 'lucide-react';
import BarberPole from './BarberPole';
import RazorIcon from './RazorIcon';
import Reveal from './Reveal';
import { content } from '../data/content';
import { whatsappLink, CHARACTER_IMAGE, HERO_BG } from '../config';
import { useParallax } from '../hooks/useReveal';

const featureIcons = {
  crown: Crown,
  armchair: Armchair,
  shield: ShieldCheck,
  users: Users,
};

export default function Hero() {
  const bgRef = useRef(null);
  const charRef = useRef(null);
  const { hero, brand } = content;

  useParallax([
    { ref: bgRef, factor: 0.12, base: 'scale(1.08)' },
    { ref: charRef, factor: -0.08 },
  ]);

  return (
    <section id="inicio" className="hero" data-testid="hero-section">
      <div ref={bgRef} className="hero__bg" style={{ backgroundImage: `url(${HERO_BG})` }} />
      <div className="hero__overlay" />

      <BarberPole className="hero__pole hero__pole--left" height={300} speed={2.8} />
      <BarberPole className="hero__pole hero__pole--right" height={300} speed={3.1} />

      <div className="container hero__inner">
        <div className="hero__content">
          <Reveal direction="down">
            <p className="hero__kicker" data-testid="hero-kicker">
              {hero.kicker.map((k, i) => (
                <React.Fragment key={k}>
                  {i > 0 && <span className="hero__kicker-dot" />}
                  <span>{k}</span>
                </React.Fragment>
              ))}
            </p>
          </Reveal>

          <Reveal direction="left" delay={100}>
            <h1 className="hero__title" data-testid="hero-title">
              <span className="hero__title-line1 gold-text">{brand.first}</span>
              <span className="hero__title-line2">
                <RazorIcon size={96} className="hero__razor hero__razor--l" />
                <span className="gold-text display">{brand.second}</span>
                <RazorIcon size={96} flip className="hero__razor hero__razor--r" />
              </span>
            </h1>
            <div className="hero__underline" />
          </Reveal>

          <Reveal direction="left" delay={220}>
            <p className="hero__desc">{hero.description}</p>
          </Reveal>

          <Reveal direction="up" delay={320} className="hero__actions">
            {/* <a
              href={whatsappLink()}
              target="_blank"
              rel="noreferrer"
              className="btn btn-gold"
              data-testid="hero-whatsapp-btn"
            > */}
            <a
              href="#agendar"
              className="btn btn-gold"
            >
              <MessageCircle size={20} />
              {hero.primaryCta}
            </a>
            <a href="#servicos" className="btn btn-outline" data-testid="hero-services-btn">
              {hero.secondaryCta}
            </a>
          </Reveal>

          <Reveal direction="up" delay={420}>
            <ul className="hero__features" data-testid="hero-features">
              {hero.features.map((f) => {
                const Icon = featureIcons[f.icon];
                return (
                  <li key={f.icon} className="hero__feature">
                    <span className="hero__feature-icon">
                      <Icon size={26} strokeWidth={1.6} />
                    </span>
                    <span className="hero__feature-label">{f.label}</span>
                  </li>
                );
              })}
            </ul>
          </Reveal>
        </div>

        <Reveal direction="right" delay={200} className="hero__art-wrap">
          <div className="hero__art" data-testid="hero-art">
            <div className="hero__art-glow" />
            <div className="hero__art-ring" />
            <div ref={charRef} className="hero__character-wrap">
              <img
                src={CHARACTER_IMAGE}
                alt="Barbeiro da Barbearia Brenner segurando navalha"
                className="hero__character"
                fetchPriority="high"
                decoding="async"
              />
            </div>
          </div>
        </Reveal>
      </div>

      <a href="#servicos" className="hero__scroll" aria-label="Rolar para serviços">
        <ChevronDown size={22} />
      </a>
    </section>
  );
}
