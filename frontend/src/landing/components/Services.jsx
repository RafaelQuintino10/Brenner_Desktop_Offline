// import React from 'react';
// import { Scissors, Sparkles, ArrowRight } from 'lucide-react';
// import Reveal from './Reveal';
// import SectionTitle from './SectionTitle';
// import { content } from '../data/content';
// import { whatsappLink } from '../config';

// function RazorMini({ size = 26 }) {
//   return (
//     <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
//       <path d="M3 15 L13 5 C 14 4, 16 4, 17 5 L 19 7 L 7 19 Z" />
//       <path d="M17 11 L 21 15" />
//       <path d="M19 13 L 15 17" />
//     </svg>
//   );
// }

// function CombMini({ size = 26 }) {
//   return (
//     <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
//       <rect x="3" y="6" width="18" height="5" rx="1.5" />
//       <path d="M5 11v6M8 11v6M11 11v5M14 11v6M17 11v5M20 11v4" />
//     </svg>
//   );
// }

// const icons = {
//   scissors: <Scissors size={26} />,
//   sparkles: <Sparkles size={26} />,
//   razor: <RazorMini />,
//   comb: <CombMini />,
// };

// export default function Services() {
//   const { services } = content;
//   return (
//     <section id="servicos" className="section services" data-testid="services-section">
//       <div className="container">
//         <Reveal direction="up">
//           <SectionTitle title={services.title} sub={services.sub} />
//         </Reveal>

//         <div className="services__grid">
//           {services.items.map((s, i) => (
//             <Reveal key={s.id} direction="up" delay={120 + i * 110}>
//               <article className="service-card" data-testid={`service-card-${s.id}`}>
//                 <div className="service-card__media">
//                   <div className="service-card__img">
//                     <img src={s.image} alt={s.title} loading="lazy" />
//                   </div>
//                   <div className="service-card__badge">{icons[s.icon]}</div>
//                 </div>
//                 <div className="service-card__body">
//                   <h3 className="service-card__title">{s.title}</h3>
//                   <p className="service-card__desc">{s.description}</p>
//                   <a href={whatsappLink()} target="_blank" rel="noreferrer" className="service-card__link">
//                     Agendar <ArrowRight size={15} />
//                   </a>
//                 </div>
//               </article>
//             </Reveal>
//           ))}
//         </div>
//       </div>
//     </section>
//   );
// }


import React from 'react';
import { Scissors, ArrowRight } from 'lucide-react';

import Reveal from './Reveal';
import SectionTitle from './SectionTitle';
import { content } from '../data/content';
import { mediaUrl } from '../api';

export default function Services({
  services = [],
  loading = false,
  error = '',
}) {
  return (
    <section
      id="servicos"
      className="section services"
      data-testid="services-section"
    >
      <div className="container">
        <Reveal direction="up">
          <SectionTitle
            title="Nossos serviços"
            sub="Escolha seu estilo e agende com nossos profissionais."
          />
        </Reveal>

        {loading && (
          <p className="catalog-message">
            Carregando serviços...
          </p>
        )}

        {!loading && error && (
          <p className="catalog-message" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && services.length === 0 && (
          <p className="catalog-message">
            Nenhum serviço disponível no momento.
          </p>
        )}

        <div className="services__grid">
          {services.map((s, i) => {
            const imagem = mediaUrl(s.imagem_exibicao || s.imagem_url)
              || content.services.items[
                i % content.services.items.length
              ].image;

            return (
              <Reveal
                key={s.id}
                direction="up"
                delay={Math.min(120 + i * 80, 480)}
              >
                <article className="service-card">
                  <div className="service-card__media">
                    <div className="service-card__img">
                      <img
                        src={imagem}
                        alt={s.nome}
                        loading="lazy"
                      />
                    </div>

                    <div className="service-card__badge">
                      <Scissors size={26} />
                    </div>
                  </div>

                  <div className="service-card__body">
                    <h3 className="service-card__title">
                      {s.nome}
                    </h3>

                    <p className="service-card__desc">
                      {s.descricao ||
                        'Atendimento especializado com qualidade.'}
                    </p>

                    <p className="catalog-price">
                      {Number(s.preco).toLocaleString('pt-BR', {
                        style: 'currency',
                        currency: 'BRL',
                      })}
                    </p>

                    <p className="catalog-duration">
                      Duração: {s.duracao_minutos} minutos
                    </p>

                    <a
                      href="#agendar"
                      className="service-card__link"
                    >
                      Agendar serviço
                      <ArrowRight size={15} />
                    </a>
                  </div>
                </article>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
