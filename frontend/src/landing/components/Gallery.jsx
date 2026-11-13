import React, { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight, Maximize2 } from 'lucide-react';
import Reveal from './Reveal';
import SectionTitle from './SectionTitle';
import { content } from '../data/content';

export default function Gallery() {
  const { gallery } = content;
  const [active, setActive] = useState(null);

  const close = useCallback(() => setActive(null), []);
  const prev = useCallback(
    () => setActive((i) => (i === null ? null : (i - 1 + gallery.images.length) % gallery.images.length)),
    [gallery.images.length]
  );
  const next = useCallback(
    () => setActive((i) => (i === null ? null : (i + 1) % gallery.images.length)),
    [gallery.images.length]
  );

  useEffect(() => {
    if (active === null) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') prev();
      if (e.key === 'ArrowRight') next();
    };
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [active, close, prev, next]);

  return (
    <section id="galeria" className="section gallery" data-testid="gallery-section">
      <div className="container">
        <Reveal direction="up">
          <SectionTitle title={gallery.title} sub={gallery.sub} />
        </Reveal>

        <div className="gallery__grid">
          {gallery.images.map((img, i) => (
            <Reveal key={img.src} direction="zoom" delay={80 + i * 80} className={`gallery__item gallery__item--${i}`}>
              <button
                type="button"
                className="gallery__btn"
                onClick={() => setActive(i)}
                aria-label={`Ampliar foto: ${img.alt}`}
                data-testid={`gallery-item-${i}`}
              >
                <img src={img.src} alt={img.alt} loading="lazy" />
                <span className="gallery__hover">
                  <Maximize2 size={22} />
                  <span>{img.alt}</span>
                </span>
              </button>
            </Reveal>
          ))}
        </div>
      </div>

      {active !== null && (
        <div className="lightbox" role="dialog" aria-modal="true" data-testid="gallery-lightbox" onClick={close}>
          <button type="button" className="lightbox__close" onClick={close} aria-label="Fechar">
            <X size={26} />
          </button>
          <button
            type="button"
            className="lightbox__nav lightbox__nav--prev"
            onClick={(e) => { e.stopPropagation(); prev(); }}
            aria-label="Anterior"
          >
            <ChevronLeft size={30} />
          </button>
          <img
            src={gallery.images[active].src}
            alt={gallery.images[active].alt}
            className="lightbox__img"
            onClick={(e) => e.stopPropagation()}
          />
          <button
            type="button"
            className="lightbox__nav lightbox__nav--next"
            onClick={(e) => { e.stopPropagation(); next(); }}
            aria-label="Próxima"
          >
            <ChevronRight size={30} />
          </button>
          <p className="lightbox__caption">{gallery.images[active].alt}</p>
        </div>
      )}
    </section>
  );
}
