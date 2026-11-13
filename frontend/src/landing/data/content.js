// Conteúdo estático (mock) da landing page
export const content = {
  brand: {
    first: 'Barbearia',
    second: 'Brenner',
  },
  nav: [
    { label: 'Início', href: '#inicio' },
    { label: 'Serviços', href: '#servicos' },
    { label: 'Horários', href: '#horarios' },
    { label: 'Galeria', href: '#galeria' },
    { label: 'Localização', href: '#localizacao' },
    { label: 'Produtos', href: '#produtos' },
    { label: 'Agendar', href: '#agendar' },
  ],
  hero: {
    kicker: ['Estilo', 'Qualidade', 'Confiança'],
    description:
      'Corte masculino, barba e acabamento com qualidade e ambiente familiar.',
    primaryCta: 'Agendar horário',
    secondaryCta: 'Ver serviços',
    features: [
      { icon: 'crown', label: 'Profissionais\nqualificados' },
      { icon: 'armchair', label: 'Ambiente\nfamiliar' },
      { icon: 'shield', label: 'Atendimento\ncom horário' },
      { icon: 'users', label: 'Estilo para\ntodas as idades' },
    ],
  },
  services: {
    title: 'Nossos serviços',
    sub: 'Tudo que você precisa para manter o estilo em dia.',
    items: [
      {
        id: 'corte',
        icon: 'scissors',
        title: 'Corte masculino',
        description: 'Estilo e qualidade no seu corte.',
        image:
          'https://images.unsplash.com/photo-1599351431202-1e0f0137899a?crop=entropy&cs=srgb&fm=jpg&q=80&w=800',
      },
      {
        id: 'barba',
        icon: 'razor',
        title: 'Barba',
        description: 'Aparagem e alinhamento com precisão.',
        image:
          'https://images.unsplash.com/photo-1503951914875-452162b0f3f1?crop=entropy&cs=srgb&fm=jpg&q=80&w=800',
      },
      {
        id: 'acabamento',
        icon: 'comb',
        title: 'Acabamento',
        description: 'Detalhes que fazem a diferença.',
        image:
          'https://images.unsplash.com/photo-1647140655214-e4a2d914971f?crop=entropy&cs=srgb&fm=jpg&q=80&w=800',
      },
      {
        id: 'cuidados',
        icon: 'sparkles',
        title: 'Cuidados especiais',
        description: 'Produtos de qualidade para seu visual.',
        image:
          'https://images.unsplash.com/photo-1621607505833-616916c46a25?crop=entropy&cs=srgb&fm=jpg&q=80&w=800',
      },
    ],
  },
  hours: {
    title: 'Horário de funcionamento',
    days: 'Segunda a Sábado',
    slots: [
      { open: '08:00', close: '11:40', label: 'Manhã' },
      { open: '14:00', close: '19:40', label: 'Tarde' },
    ],
  },
  address: {
    title: 'Endereço',
    line1: 'Rua do hospital,',
    line2: 'em frente à pracinha.',
    mapsQuery: 'Rua do Hospital, em frente à pracinha',
    button: 'Agendar pelo WhatsApp',
  },
  gallery: {
    title: 'Galeria',
    sub: 'Um pouco do nosso dia a dia na barbearia.',
    images: [
      {
        src: 'https://images.unsplash.com/photo-1592647420148-bfcc177e2117?crop=entropy&cs=srgb&fm=jpg&q=80&w=900',
        alt: 'Cadeira de barbeiro',
      },
      {
        src: 'https://images.unsplash.com/photo-1605497788044-5a32c7078486?crop=entropy&cs=srgb&fm=jpg&q=80&w=900',
        alt: 'Interior da barbearia',
      },
      {
        src: 'https://images.unsplash.com/photo-1621605815971-fbc98d665033?crop=entropy&cs=srgb&fm=jpg&q=80&w=900',
        alt: 'Barbeiro em ação',
      },
      {
        src: 'https://images.pexels.com/photos/16997937/pexels-photo-16997937.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940',
        alt: 'Corte masculino moderno',
      },
      {
        src: 'https://images.unsplash.com/photo-1585747860715-2ba37e788b70?crop=entropy&cs=srgb&fm=jpg&q=80&w=900',
        alt: 'Ambiente da barbearia',
      },
      {
        src: 'https://images.unsplash.com/photo-1599351431202-1e0f0137899a?crop=entropy&cs=srgb&fm=jpg&q=80&w=900',
        alt: 'Corte com máquina',
      },
    ],
  },
  finalCta: {
    headline: 'Venha dar um talento no visual na',
    brand: 'Barbearia Brenner!',
    sub: 'Atendimento de qualidade e ambiente familiar.',
    closing: 'Esperamos você!',
    button: 'Agendar agora',
  },
  footer: {
    rights: 'Barbearia Brenner. Todos os direitos reservados.',
  },
};
