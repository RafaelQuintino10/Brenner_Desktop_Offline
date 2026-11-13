
const API_URL = (
  import.meta.env.VITE_API_URL ||
  'http://127.0.0.1:8000/api'
).replace(/\/+$/, '');

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.body
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      data.detail ||
      data.non_field_errors?.[0] ||
      data.message ||
      data.mensagem ||
      Object.values(data).flat().join(' ') ||
      `Erro HTTP ${response.status}`;

    throw new Error(message);
  }

  return data;
}

export const publicApi = {
  catalogo: () => request('/public/catalogo/'),

  disponibilidade: ({ barbeiro, servico, data }) => {
    const params = new URLSearchParams({
      barbeiro: String(barbeiro),
      servico: String(servico),
      data,
    });

    return request(`/public/disponibilidade/?${params}`);
  },

  agendar: (dados) =>
    request('/public/agendamentos/', {
      method: 'POST',
      body: JSON.stringify(dados),
    }),
};

export function mediaUrl(path) {
  if (!path) return '';

  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const origin = new URL(API_URL).origin;

  return new URL(path, origin).href;
}
