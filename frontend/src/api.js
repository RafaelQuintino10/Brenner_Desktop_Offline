/** API Django REST (backend do projeto), única fonte de verdade. Sem localStorage de registros. */
// export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
// const KEY = 'brenner_admin_token';
// export const token = () => sessionStorage.getItem(KEY);
// export const setToken = value => value ? sessionStorage.setItem(KEY, value) : sessionStorage.removeItem(KEY);

export const API_URL = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
).replace(/\/$/, '');

export const PANEL_MODE =
  /^\/barbearia(?:\/|$)/.test(window.location.pathname)
    ? 'balconista'
    : 'admin';

const KEY = PANEL_MODE === 'balconista'
  ? 'brenner_balconista_token'
  : 'brenner_admin_token';

export const token = () => sessionStorage.getItem(KEY);

export const setToken = value =>
  value
    ? sessionStorage.setItem(KEY, value)
    : sessionStorage.removeItem(KEY);

export function dateLocal() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function errorMessage(payload, code) {
  if (typeof payload === 'string') return payload;
  if (!payload || typeof payload !== 'object') return `Erro HTTP ${code}`;
  const entries = Object.entries(payload).map(([k, v]) => {
    const value = Array.isArray(v) ? v.join(', ') : typeof v === 'object' ? JSON.stringify(v) : String(v);
    return k === 'detail' || k === 'non_field_errors' ? value : `${k}: ${value}`;
  });
  return entries.join(' | ') || `Erro HTTP ${code}`;
}

export async function request(path, { method = 'GET', body, signal } = {}) {
  const url = path.startsWith('http') ? path : `${API_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const t = token();
  let response;
  const isFormData = body instanceof FormData;
  try {
    response = await fetch(url, {
      method, signal,
      headers: {
        Accept: 'application/json',
        ...(body !== undefined && !isFormData
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...(t ? { Authorization: `Token ${t}` } : {}),
      },
      ...(body !== undefined
        ? { body: isFormData ? body : JSON.stringify(body) }
        : {}),
    });
  } catch (e) {
    throw new Error('Não foi possível acessar o Django. Confira se o servidor está rodando em ' + API_URL);
  }
  let data = null;
  if (response.status !== 204) {
    const text = await response.text();
    try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  }
  if (!response.ok) {
    if (response.status === 401 && t) window.dispatchEvent(new Event('brenner:unauthorized'));
    throw new Error(errorMessage(data, response.status));
  }
  return data;
}

// export async function login(email, password) {
//   const result = await request('/auth/login/', { method: 'POST', body: { email: email.trim(), password } });
//   setToken(result.token);
//   return result;
// }
export async function login(email, password) {
  const path = PANEL_MODE === 'balconista'
    ? '/auth/login-balconista/'
    : '/auth/login/';

  const result = await request(path, {
    method: 'POST',
    body: {
      email: email.trim(),
      password
    }
  });

  setToken(result.token);
  return result;
}
export async function logout() {
  try { await request('/auth/logout/', { method: 'POST' }); } finally { setToken(null); }
}
export const me = () => request('/auth/me/');

// A DRF paginada (PAGE_SIZE=50) é percorrida inteira. Ignora valores mockados.
export async function listAll(route) {
  let page = 1, records = [];
  while (page <= 100) {
    const sep = route.includes('?') ? '&' : '?';
    const response = await request(`${route}${sep}page=${page}`);
    if (Array.isArray(response)) return response;
    records = records.concat(response?.results || []);
    if (!response?.next) return records;
    page += 1;
  }
  throw new Error('Lista muito extensa para carregar integralmente. Refine a consulta.');
}

const routes = {
  barbers: '/barbeiros/', products: '/produtos/', services: '/servicos/',
  clients: '/clientes/', appointments: '/agendamentos/', sales: '/vendas/',
  expenses: '/despesas/', receipts: '/recebimentos-servicos/', timeoffs: '/folgas/',
};
export const api = {
  list: type => listAll(routes[type]),
  create: (type, value) => request(routes[type], { method: 'POST', body: value }),
  update: (type, id, value) => request(`${routes[type]}${id}/`, { method: 'PATCH', body: value }),
  remove: (type, id) => request(`${routes[type]}${id}/`, { method: 'DELETE' }),
  registerSale: value => request('/vendas/', { method: 'POST', body: value }),
  reverseSale: id => request(`/vendas/${id}/estornar/`, { method: 'POST' }),
  // finance: month => request(`/financeiro/resumo/?mes=${encodeURIComponent(month)}`),
  // closeMonth: month => request('/financeiro/fechamentos/', { method: 'POST', body: { mes: month } }),
  finance: month =>
  request(`/financeiro/resumo/?mes=${encodeURIComponent(month)}`),

  periodStatus: month =>
    request(`/financeiro/status-periodo/?mes=${encodeURIComponent(month)}`),

  closeMonth: month =>
    request('/financeiro/fechamentos/', {
      method: 'POST',
      body: { mes: month }
    }),
  closures: () => request('/financeiro/fechamentos/'),
  availableSlots: (barber, service, date) => request(`/public/disponibilidade/?barbeiro=${barber}&servico=${service}&data=${date}`),
  uploadImage: (type, id, file) => {
  const form = new FormData();
  form.append('arquivo', file);

  const path = type === 'barbers'
    ? `/barbeiros/${id}/foto/`
    : `/produtos/${id}/imagem/`;

  return request(path, {
    method: 'POST',
    body: form
  });
},
};

const statusDisplay = { pendente: 'Aguardando', confirmado: 'Confirmado', concluido: 'Concluído', cancelado: 'Cancelado' };
export const backendStatus = status => ({ Aguardando: 'pendente', Confirmado: 'confirmado', 'Concluído': 'concluido', Cancelado: 'cancelado' }[status] || status || 'pendente');

export const fromApi = {
  barbers: a => ({ id: a.id, name: a.nome, phone: a.telefone, specialty: a.especialidade, commission: Number(a.comissao_servico), productCommission: Number(a.comissao_produto), status: a.ativo ? 'Ativo' : 'Inativo', photoUrl: a.foto_exibicao || a.foto_url, horarios: a.horarios || [] }),
  products: a => ({ id: a.id, name: a.nome, category: a.categoria, description: a.descricao, price: Number(a.preco), cost: Number(a.custo), stock: a.estoque, minStock: a.estoque_minimo, image: a.imagem_exibicao || a.imagem_url, active: a.ativo }),
  services: a => ({ id: a.id, name: a.nome, description: a.descricao, price: Number(a.preco), duration: a.duracao_minutos, image: a.imagem_url, active: a.ativo }),
  clients: a => ({ id: a.id, name: a.nome, phone: a.telefone }),
  appointments: a => ({ id: a.id, client: a.nome_cliente || '', clientId: a.cliente, clientPhone: a.telefone_cliente || '', barberId: a.barbeiro, serviceId: a.servico, date: a.data, time: String(a.hora).slice(0, 5), status: statusDisplay[a.status] || a.status, paid: a.pago, charged: Number(a.valor_cobrado), notes: a.observacao || '' }),
  sales: a => ({ id: a.id, productId: a.produto, productName: a.produto_nome, barberId: a.barbeiro, barberName: a.barbeiro_nome, date: a.data, quantity: a.quantidade, amount: Number(a.valor_total), cost: Number(a.custo_total), commission: Number(a.comissao), reversed: a.estornada }),
  receipts: a => ({ id: a.id, appointmentId: a.agendamento, barberId: a.barbeiro, date: a.data, amount: Number(a.valor), commission: Number(a.comissao) }),
  expenses: a => ({ id: a.id, description: a.descricao, date: a.data, expense: Number(a.valor) }),
  timeoffs: a => ({ id: a.id, barberId: a.barbeiro, barberName: a.barbeiro_nome, date: a.data, reason: a.motivo }),
};

// O backend calcula preços, custos e comissões. O frontend só mostra os valores retornados.
export function toApi(type, v, editing = false, initial = null) {
  switch (type) {
    case 'barbers': return {
      nome: v.name?.trim(), telefone: v.phone || '', especialidade: v.specialty || '',
      ativo: v.status === 'Ativo', comissao_servico: v.commission,
      comissao_produto: v.productCommission,
      ...(v.horarios !== undefined ? { horarios: v.horarios } : {}),
    };
    case 'products': return {
      nome: v.name?.trim(), categoria: v.category, descricao: v.description || '',
      preco: v.price, custo: v.cost, estoque: v.stock, estoque_minimo: v.minStock,
       ativo: v.active !== false,
    };
    case 'services': return {
      nome: v.name?.trim(), descricao: v.description || '', preco: v.price,
      duracao_minutos: v.duration, imagem_url: v.image || '', ativo: v.active !== false,
    };
    case 'clients': return { nome: v.name?.trim(), telefone: v.phone };
    case 'appointments': {
      const status = backendStatus(v.status);
      const candidate = {
        barbeiro: Number(v.barberId), servico: Number(v.serviceId), data: v.date,
        hora: v.time, status, observacao: v.notes || '',
      };
      // PATCH em status não deve revalidar um horário antigo como se fosse remarcação.
      // O serializer Django verifica conflitos quando data/hora/serviço/barbeiro realmente mudam.
      const payload = editing && initial
        ? Object.fromEntries(Object.entries(candidate).filter(([key, value]) => {
            const prev = {
              barbeiro: Number(initial.barberId), servico: Number(initial.serviceId),
              data: initial.date, hora: initial.time, status: backendStatus(initial.status),
              observacao: initial.notes || '',
            }[key];
            return String(prev) !== String(value);
          }))
        : candidate;
      if (!editing) {
        if (v.clientId) payload.cliente = Number(v.clientId);
        else { payload.cliente_nome = v.client?.trim(); payload.cliente_telefone = v.clientPhone?.trim(); }
      }
      if (status === 'concluido') payload.pago = true;
      return payload;
    }
    default: return v;
  }
}


export async function downloadExcel(month) {
  const t = token();

  const response = await fetch(
    `${API_URL}/financeiro/excel/?mes=${encodeURIComponent(month)}`,
    {
      headers: {
          Accept: '*/*',
        ...(t ? { Authorization: `Token ${t}` } : {}),
      },
    },
  );

  if (!response.ok) {
    const payload = await response.json().catch(() => null);

    if (response.status === 401) {
      window.dispatchEvent(
        new Event('brenner:unauthorized')
      );
    }

    throw new Error(errorMessage(payload, response.status));
  }

  return response.blob();
}
