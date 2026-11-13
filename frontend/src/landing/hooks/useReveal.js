import { useEffect, useRef, useState } from 'react';

/**
 * Hook de "reveal on scroll" - adiciona a classe `is-visible`
 * quando o elemento entra na viewport (fade + slide).
 */
export function useReveal(options = {}) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;

    if (typeof IntersectionObserver === 'undefined') {
      setVisible(true);
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -60px 0px', ...options }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return [ref, visible];
}

/**
 * Parallax leve sem re-render: aplica transform direto no DOM via rAF.
 * targets: [{ ref, factor, base }] -> translateY(scrollY * factor) + base
 * Desativado em telas pequenas e com prefers-reduced-motion.
 */
export function useParallax(targets, { max = 160, disableBelow = 900 } = {}) {
  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return undefined;

    let frame = 0;
    let active = window.innerWidth >= disableBelow;

    const apply = () => {
      frame = 0;
      const y = Math.min(window.scrollY || 0, max);
      targets.forEach(({ ref, factor, base = '' }) => {
        if (!ref.current) return;
        ref.current.style.transform = active
          ? `translate3d(0, ${(y * factor).toFixed(1)}px, 0) ${base}`.trim()
          : base;
      });
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(apply);
    };
    const onResize = () => {
      active = window.innerWidth >= disableBelow;
      onScroll();
    };
    apply();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      cancelAnimationFrame(frame);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
}

/**
 * Hook que retorna o valor do scroll vertical (para parallax leve)
 */
export function useScrollY() {
  const [y, setY] = useState(0);
  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => setY(window.scrollY || 0));
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(frame);
    };
  }, []);
  return y;
}
