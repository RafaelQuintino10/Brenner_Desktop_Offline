
import React from 'react';
import { MessageCircle } from 'lucide-react';

import Reveal from './Reveal';
import SectionTitle from './SectionTitle';
import { mediaUrl } from '../api';
import { WHATSAPP_NUMBER } from '../config';

const money = value =>
  Number(value || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });

export default function Products({
  products = [],
  loading = false,
  error = '',
}) {
  return (
    <section id="produtos" className="section products-section">
      <div className="container">
        <Reveal direction="up">
          <SectionTitle
            title="Nossos produtos"
            sub="Produtos selecionados para cuidar do seu estilo."
          />
        </Reveal>

        {loading && (
          <p className="catalog-message">
            Carregando produtos...
          </p>
        )}

        {!loading && error && (
          <p className="catalog-message" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && products.length === 0 && (
          <p className="catalog-message">
            Nenhum produto disponível no momento.
          </p>
        )}

        <div className="products-grid">
          {products.map((p, i) => {
            const mensagem =
              `Olá! Tenho interesse no produto ${p.nome}, ` +
              `anunciado por ${money(p.preco)}. Está disponível?`;

            const url = p.whatsapp_url ||
              `https://wa.me/${WHATSAPP_NUMBER}?text=${
                encodeURIComponent(mensagem)
              }`;

            return (
              <Reveal
                key={p.id}
                direction="up"
                delay={Math.min(100 + i * 80, 480)}
              >
                <article className="product-landing-card">
                  <div className="product-landing-image">
                    {p.imagem_exibicao || p.imagem_url ? (
                      <img
                        src={mediaUrl(
                          p.imagem_exibicao || p.imagem_url
                        )}
                        alt={p.nome}
                        loading="lazy"
                      />
                    ) : (
                      <span>Barbearia Brenner</span>
                    )}
                  </div>

                  <div className="product-landing-body">
                    <span className="product-category">
                      {p.categoria}
                    </span>

                    <h3>{p.nome}</h3>

                    <p className="product-description">
                      {p.descricao}
                    </p>

                    <strong className="catalog-price">
                      {money(p.preco)}
                    </strong>

                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-gold product-whatsapp"
                    >
                      <MessageCircle size={18} />
                      Consultar no WhatsApp
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
