// import React from 'react';
// import { MessageCircle } from 'lucide-react';
// import Navbar from './components/Navbar';
// import Hero from './components/Hero';
// import Services from './components/Services';
// import Gallery from './components/Gallery';
// import { HoursAddress, FinalCta } from './components/Sections';
// import Footer from './components/Footer';
// import { whatsappLink } from './config';
// import './styles/components.css';

// export default function App() {
//   return (
//     <div className="bb-app">
//       <Navbar />
//       <main>
//         <Hero />
//         <Services />
//         <HoursAddress />
//         <Gallery />
//         <FinalCta />
//       </main>
//       <Footer />

//       <a
//         href={whatsappLink()}
//         target="_blank"
//         rel="noreferrer"
//         className="whats-float"
//         aria-label="Falar no WhatsApp"
//         data-testid="floating-whatsapp-btn"
//       >
//         <MessageCircle size={28} />
//       </a>
//     </div>
//   );
// }



import React, { useEffect, useState } from 'react';
import { MessageCircle } from 'lucide-react';

import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Services from './components/Services';
import Products from './components/Products';
import Booking from './components/Booking';
import Gallery from './components/Gallery';
import { HoursAddress, FinalCta } from './components/Sections';
import Footer from './components/Footer';

import { whatsappLink } from './config';
import { publicApi } from './api';

import './styles/components.css';
import './styles/commerce.css';

export default function App() {
  const [catalogo, setCatalogo] = useState({
    servicos: [],
    produtos: [],
    barbeiros: [],
  });

  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    let ativo = true;

    async function carregarCatalogo() {
      try {
        const dados = await publicApi.catalogo();

        if (ativo) {
          setCatalogo(dados);
          setErro('');
        }
      } catch (error) {
        if (ativo) {
          setErro(
            'Não foi possível carregar o catálogo da barbearia.'
          );
        }
      } finally {
        if (ativo) setLoading(false);
      }
    }

    carregarCatalogo();

    return () => {
      ativo = false;
    };
  }, []);

  return (
    <div className="bb-app">
      <Navbar />

      <main>
        <Hero />

        <Services
          services={catalogo.servicos}
          loading={loading}
          error={erro}
        />

        <Products
          products={catalogo.produtos}
          loading={loading}
          error={erro}
        />

        <Booking
          barbers={catalogo.barbeiros}
          services={catalogo.servicos}
        />

        <HoursAddress />
        <Gallery />
        <FinalCta />
      </main>

      <Footer />

      <a
        href={whatsappLink()}
        target="_blank"
        rel="noreferrer"
        className="whats-float"
        aria-label="Falar no WhatsApp"
      >
        <MessageCircle size={28} />
      </a>
    </div>
  );
}
