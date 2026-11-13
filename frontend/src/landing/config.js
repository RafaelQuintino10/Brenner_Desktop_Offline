// ======================================================
// CONFIGURAÇÕES DA BARBEARIA BRENNER
// Altere aqui o número do WhatsApp (somente números, com DDI + DDD)
// Exemplo: 5551999999999  ->  +55 (51) 99999-9999
// ======================================================
export const WHATSAPP_NUMBER = '5597984387365';

export const WHATSAPP_MESSAGE =
  'Olá! Gostaria de agendar um horário na Barbearia Brenner.';

export const whatsappLink = () =>
  `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;

// Personagem (PNG com fundo transparente) - arquivo em /public
export const CHARACTER_IMAGE = '/brenner-barber.png';

// Arte/poster original (usada no emblema)
export const POSTER_IMAGE =
  'https://customer-assets-4nw71qhi.emergentagent.net/job_c604f85b-cb70-46d7-a75f-9481a3896509/artifacts/38e1c98c5cf8c5b5_IMG-20261006-WA0008.jpg';

// Foto de fundo da hero (interior da barbearia)
export const HERO_BG =
  'https://images.unsplash.com/photo-1585747860715-2ba37e788b70?crop=entropy&cs=srgb&fm=jpg&q=80&w=1920';
