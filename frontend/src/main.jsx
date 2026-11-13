import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import { LayoutDashboard, CalendarDays, Package, Users, Scissors, Wallet, Menu, X, Plus, Search, Trash2, Pencil, Check, TrendingUp, Download, ShoppingBag, Save, CalendarCheck, AlertCircle, Undo2, LogOut, LoaderCircle } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';
// import { api, login, logout, me, token, setToken, dateLocal, fromApi, toApi, downloadExcel } from './api';
import {
  api,
  login,
  logout,
  me,
  token,
  setToken,
  dateLocal,
  fromApi,
  toApi,
  downloadExcel,
  PANEL_MODE,
  request as apiRequest
} from './api';
import './style.css';


// const money = n => Number(n || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });'
const isBalconista = PANEL_MODE === 'balconista';
const isDesktop = import.meta.env.VITE_DESKTOP_MODE === 'true';
const CONFIG_MENSALIDADE = {
  valor: 200,
  primeiroVencimento: '2026-12-10',
  diaVencimento: 10,
  diasAntecedencia: 3,
};

const money = n => Number(n || 0).toLocaleString(
  'pt-BR',
  { style: 'currency', currency: 'BRL' }
);
const today = dateLocal;
const month = () => today().slice(0,7);
const initialData = {barbers:[], products:[], services:[], clients:[], appointments:[], sales:[], receipts:[], expenses:[], timeoffs:[], transactions:[]};
// const nav = [
//   ['dashboard','Dashboard',LayoutDashboard],
//   ['appointments','Agendamentos',CalendarDays],
//   ['products','Produtos',Package],
//   ['sales','Vendas',ShoppingBag],
//   ['barbers','Barbeiros',Scissors],
//   ['services','Serviços',ShoppingBag],
//   ['clients','Clientes',Users],
//   ['finance','Financeiro',Wallet],
// ];
const nav = [
  ['dashboard', 'Dashboard', LayoutDashboard],
  ['appointments', 'Agendamentos', CalendarDays],
  ['products', 'Produtos', Package],
  ['sales', 'Vendas', ShoppingBag],
  ['barbers', 'Barbeiros', Scissors],
  ['services', 'Serviços', ShoppingBag],
  ['clients', 'Clientes', Users],
  ['finance', 'Financeiro', Wallet],
  ...(isDesktop ? [['sync', 'Sincronização', CalendarCheck]] : []),
];

const menuVisible = isBalconista
  ? nav.filter(([key]) =>
      ['appointments', 'sales', ...(isDesktop ? ['sync'] : [])].includes(key)
    )
  : nav;

function useToast() {
  const [toast, setToast] = useState('');
  const notify = useCallback(message => setToast(message), []);
  useEffect(() => {
    if (!toast) return;
    const timeout = setTimeout(() => setToast(''), 5000);
    return () => clearTimeout(timeout);
  }, [toast]);
  return [toast, notify];
}

function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [working, setWorking] = useState(false);
  const [error, setError] = useState('');
  const handleSubmit = async e => {
    e.preventDefault();
    setWorking(true); setError('');
    try { const user = await login(email, password); onLogin(user); }
    catch (err) { setError(err.message); }
    finally { setWorking(false); }
  };
  return <div className="brenner-login"><form className="loginbox" onSubmit={handleSubmit}>
    <div className="brand"><span className="crown">♛</span><small>BARBEARIA</small><strong>BRENNER</strong><em>ESTILO TEM NOME</em></div>
    {/* <div className="eyebrow">ACESSO RESTRITO</div>
    <h1>Painel administrativo</h1>
    <p>Entre com o e-mail cadastrado no seu usuário administrador do Django.</p> */}
    <div className="eyebrow">ACESSO RESTRITO</div>

      <h1>
        {isBalconista ? 'Painel do balcão' : 'Painel administrativo'}
      </h1>

      <p>
        {isBalconista
          ? 'Entre com seu usuário de balconista.'
          : 'Entre com o e-mail cadastrado no seu usuário administrador do sistema.'}
      </p>
    <label className="field"><span>E-mail</span><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="admin@exemplo.com" autoComplete="email" required/></label>
    <label className="field"><span>Senha</span><input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" required/></label>
    {error&&<p className="loginerror">{error}</p>}
    <button disabled={working} className="primary loginbutton" type="submit">{working?'Entrando...':'Acessar painel'}</button>
    {/* <p className="loginnote">Somente usuários staff ativos. O e-mail é diferente do username do Django.</p> */}
    <p className="loginnote">
  {isBalconista
    ? 'Acesso exclusivo aos agendamentos e vendas.'
    : 'Somente usuários staff ativos. O e-mail é diferente do username do sistema.'}
</p>
  </form></div>;
}

function Root() {
  const [admin, setAdmin] = useState(null);
  const [authBusy, setAuthBusy] = useState(!!token());
  useEffect(() => {
    let active=true;
    if (!token()) { setAuthBusy(false); return; }
    // me().then(user=>{ if(active) setAdmin(user); }).catch(()=>{ setToken(null); if(active) setAdmin(null); }).finally(()=>{ if(active) setAuthBusy(false); });
    me()
  .then(user => {
    const allowed = isBalconista
      ? user.role === 'balconista' && !user.is_staff
      : user.is_staff;

    if (!allowed) {
      throw new Error('Perfil de acesso incorreto.');
    }

    if (active) setAdmin(user);
  })
  .catch(() => {
    setToken(null);
    if (active) setAdmin(null);
  })
  .finally(() => {
    if (active) setAuthBusy(false);
  });
    return ()=>{ active=false; };
  }, []);
  useEffect(() => {
    const handle = () => { setToken(null); setAdmin(null); };
    window.addEventListener('brenner:unauthorized', handle);
    return () => window.removeEventListener('brenner:unauthorized', handle);
  }, []);
  const handleLogout = async () => { try { await logout(); } catch { setToken(null); } setAdmin(null); };
  if (authBusy) return <div className="brenner-login"><LoaderCircle className="spin"/> Validando acesso...</div>;
  return admin ? <App admin={admin} onLogout={handleLogout}/> : <Login onLogin={setAdmin}/>;
}


// A mesma interface React ganha apenas mais uma aba no executável.
// Todas as demais cores, tabelas e modais são reaproveitados sem alteração.
function SincronizacaoDesktop({ onUpdated }) {
  const [status, setStatus] = useState(null);
  const [fila, setFila] = useState([]);
  const [working, setWorking] = useState(false);
  const [erro, setErro] = useState('');

  const carregar = useCallback(async () => {
    try {
      const [progresso, acoes] = await Promise.all([
        apiRequest('/offline/status/'),
        apiRequest('/offline/queue/')
      ]);
      setStatus(progresso);
      setFila(acoes);
      setErro('');
    } catch(e) {
      setErro(e.message);
    }
  }, []);

  useEffect(() => {
    carregar();
    const timer = setInterval(carregar, 15000);
    return () => clearInterval(timer);
  }, [carregar]);

  const sincronizar = async () => {
    setWorking(true);
    try {
      await apiRequest('/offline/sync/', {method:'POST'});
      await carregar();
      if (onUpdated) await onUpdated();
    } catch(e) {
      setErro(e.message);
    } finally {
      setWorking(false);
    }
  };

  const reenviar = async id => {
    const op = fila.find(x => x.id === id);
    if (op?.erro?.includes('Resultado incerto') &&
        !window.confirm('Confira antes no painel online: esta ação pode já ter sido gravada no servidor. Tem certeza de que deseja tentar reenviar?')) {
      return;
    }
    setWorking(true);
    try {
      await apiRequest(`/offline/queue/${id}/retry/`, {method:'POST'});
      await carregar();
    } catch(e) { setErro(e.message); }
    finally { setWorking(false); }
  };

  const formatarData = iso => iso
    ? new Date(iso).toLocaleString('pt-BR')
    : 'Ainda não realizada';

  return <>
    <div className="sync-overview">
      <div className="stat"><div><small>Conexão com o servidor</small><strong>{status?.online ? 'Online' : 'Offline'}</strong><span className="subtle">O aplicativo funciona com dados locais</span></div></div>
      <div className="stat"><div><small>Ações pendentes</small><strong>{status?.pendentes ?? '—'}</strong><span className="subtle">Aguardando envio ao Django</span></div></div>
      <div className="stat"><div><small>Conflitos</small><strong>{status?.conflitos ?? '—'}</strong><span className="subtle">Precisam de conferência</span></div></div>
    </div>
    <section className="panel space sync-panel">
      <div className="panelhead"><h3><CalendarCheck size={18}/> Sincronização com o servidor</h3>
        <button className="primary" disabled={working || !status?.online} onClick={sincronizar}>
          {working ? <LoaderCircle className="spin" size={17}/> : <CalendarCheck size={17}/>}
          Sincronizar agora
        </button>
      </div>
      <p><b>Última sincronização:</b> {formatarData(status?.ultima_sincronizacao)}</p>
      <p className="hint">Operações feitas sem internet ficam no SQLite deste computador. Quando a conexão retorna, o aplicativo tenta enviá-las na ordem de criação.</p>
      {status?.ultimo_erro && <p className="sync-error">Último aviso: {status.ultimo_erro}</p>}
      {erro && <p className="sync-error">{erro}</p>}
      <p className="hint">Cadastro e vendas offline são provisórios. O PostgreSQL confirma as regras de estoque, agenda e financeiro ao receber a sincronização. Conflitos não são sobrescritos automaticamente.</p>
    </section>
    <section className="panel space sync-panel">
      <div className="panelhead"><h3>Fila de operações</h3><span className="tag">{fila.length} item(ns) recente(s)</span></div>
      {fila.length ? <div className="tablewrap"><table>
        <thead><tr><th>Criada em</th><th>Operação</th><th>Rota</th><th>Situação</th><th>Ação</th></tr></thead>
        <tbody>{fila.map(op=><tr key={op.id}>
          <td>{formatarData(op.criada_em)}</td><td>{op.metodo}</td><td>{op.rota}</td>
          <td>{op.status==='conflict' ? <span className="sync-error" title={op.erro}>Conflito: {op.erro}</span> : 'Pendente'}</td>
          <td>{op.status==='conflict' ? <button className="secondary" disabled={working} onClick={()=>reenviar(op.id)}>Tentar novamente</button> : '—'}</td>
        </tr>)}</tbody>
      </table></div> : <p className="hint">Nenhuma operação pendente ou em conflito.</p>}
    </section>
  </>;
}

function LembreteMensalidade() {
  const [dataAtual, setDataAtual] = useState(today);

  const [mesOcultado, setMesOcultado] = useState(
    () => localStorage.getItem(
      'brenner_mensalidade_ocultada'
    ) || ''
  );

  useEffect(() => {
    const intervalo = setInterval(() => {
      setDataAtual(today());
    }, 60000);

    return () => clearInterval(intervalo);
  }, []);

  const config = CONFIG_MENSALIDADE;

  const mesAtual = dataAtual.slice(0, 7);
  const diaAtual = Number(dataAtual.slice(8, 10));

  // Primeira mensalidade:
  // fica sempre visível até o vencimento, inclusive.
  const primeiraMensalidade =
    dataAtual <= config.primeiroVencimento;

  // Mensalidades seguintes:
  // exibir apenas na janela de aviso.
  const inicioAviso = Math.max(
    1,
    config.diaVencimento - config.diasAntecedencia
  );

  const avisoRegular =
    !primeiraMensalidade &&
    diaAtual >= inicioAviso;

  // No primeiro período, não permite ocultar.
  if (!primeiraMensalidade && !avisoRegular) {
    return null;
  }

  if (!primeiraMensalidade && mesOcultado === mesAtual) {
    return null;
  }

  const vencimentoISO = primeiraMensalidade
    ? config.primeiroVencimento
    : `${mesAtual}-${String(config.diaVencimento).padStart(2, '0')}`;

  const calcularDias = (inicio, fim) => {
    const paraUTC = valor => {
      const [ano, mes, dia] = valor.split('-').map(Number);
      return Date.UTC(ano, mes - 1, dia);
    };

    return Math.round(
      (paraUTC(fim) - paraUTC(inicio)) / 86400000
    );
  };

  const diasRestantes = calcularDias(
    dataAtual,
    vencimentoISO
  );

  const [ano, mes, dia] = vencimentoISO.split('-');

  const dataFormatada = `${dia}/${mes}/${ano}`;

  let mensagem;

  if (primeiraMensalidade) {
    mensagem = diasRestantes === 0
      ? 'A primeira mensalidade vence hoje!'
      : `Primeira mensalidade em ${dataFormatada}. Faltam ${diasRestantes} dias.`;
  } else if (diasRestantes > 0) {
    mensagem = `A mensalidade vence em ${diasRestantes} dia(s).`;
  } else if (diasRestantes === 0) {
    mensagem = 'A mensalidade vence hoje!';
  } else {
    mensagem = `O vencimento deste mês foi em ${dataFormatada}.`;
  }

  const ocultar = () => {
    localStorage.setItem(
      'brenner_mensalidade_ocultada',
      mesAtual
    );

    setMesOcultado(mesAtual);
  };

  return (
    <div className="mensalidade-aviso">
      <div className="mensalidade-conteudo">
        <CalendarDays size={24}/>

        <div>
          <strong>
            Mensalidade do sistema — {money(config.valor)}
          </strong>

          <p>{mensagem}</p>

          <small>
            Vencimento mensal: todo dia {config.diaVencimento}.
          </small>
        </div>
      </div>

      {!primeiraMensalidade && (
        <button
          type="button"
          onClick={ocultar}
        >
          Ocultar neste mês
        </button>
      )}
    </div>
  );
}


function App({ admin, onLogout }) {
  const [data, setData] = useState(initialData);
  const [finance, setFinance] = useState(null);
  // const [page, setPage] = useState('dashboard');
  const [page, setPage] = useState(
  isBalconista ? 'appointments' : 'dashboard'
);
  const [sidebar, setSidebar] = useState(false);
  const [modal, setModal] = useState(null);
  const [edit, setEdit] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedDate, setSelectedDate] = useState(today());
  const [selectedMonth, setSelectedMonth] = useState(month());
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [toast, notify] = useToast();

  const refresh = useCallback(async () => {
    setLoading(true);setError('');
    try {
      // const kinds = ['barbers','products','services','clients','appointments','sales','receipts','expenses','timeoffs'];
      const kinds = isBalconista
      ? [
          'barbers',
          'products',
          'services',
          'clients',
          'appointments',
          'sales'
        ]
      : [
          'barbers',
          'products',
          'services',
          'clients',
          'appointments',
          'sales',
          'receipts',
          'expenses',
          'timeoffs'
        ];
      const values = await Promise.all(kinds.map(k=>api.list(k)));
      const mapped=Object.fromEntries(kinds.map((k,i)=>[k,values[i].map(fromApi[k])]));
      const appointmentsById=Object.fromEntries(mapped.appointments.map(a=>[a.id,a]));
      // const transactions=[
      //   ...mapped.sales.filter(s=>!s.reversed).map(s=>({id:`v${s.id}`, refId:s.id, date:s.date, kind:'Produto', description:`${s.productName} (${s.quantity}x)`, barberId:s.barberId, amount:s.amount, expense:s.cost, commission:s.commission})),
      //   ...mapped.receipts.map(s=>({id:`r${s.id}`, refId:s.id, date:s.date, kind:'Serviço',
      //   description:`${appointmentsById[s.appointmentId]?.client||'Atendimento'} ·
      //   ${appointmentsById[s.appointmentId]?.id||s.appointmentId}`, barberId:s.barberId, amount:s.amount, expense:0, commission:s.commission})),
      //   ...mapped.expenses.map(e=>({id:`d${e.id}`, refId:e.id, date:e.date, kind:'Despesa', description:e.description, barberId:null, amount:0, expense:e.expense, commission:0})),
      // ];
      // setData({...mapped,transactions});
      const transactions = isBalconista ? [] : [
  ...mapped.sales.filter(s => !s.reversed).map(s => ({
    id: `v${s.id}`,
    refId: s.id,
    date: s.date,
    kind: 'Produto',
    description: `${s.productName} (${s.quantity}x)`,
    barberId: s.barberId,
    amount: s.amount,
    expense: s.cost,
    commission: s.commission
  })),

  ...mapped.receipts.map(s => ({
    id: `r${s.id}`,
    refId: s.id,
    date: s.date,
    kind: 'Serviço',
    description: `${appointmentsById[s.appointmentId]?.client || 'Atendimento'} · ${appointmentsById[s.appointmentId]?.id || s.appointmentId}`,
    barberId: s.barberId,
    amount: s.amount,
    expense: 0,
    commission: s.commission
  })),

  ...mapped.expenses.map(e => ({
    id: `d${e.id}`,
    refId: e.id,
    date: e.date,
    kind: 'Despesa',
    description: e.description,
    barberId: null,
    amount: 0,
    expense: e.expense,
    commission: 0
  }))
];

setData({ ...initialData, ...mapped, transactions });
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(()=>{ refresh(); },[refresh]);
  // useEffect(()=>{ let active=true; api.finance(selectedMonth).then(v=>{if(active)setFinance(v)}).catch(e=>{if(active){setFinance(null);setError(e.message)}});return ()=>{active=false}},[selectedMonth,data.transactions]);
  useEffect(() => {
  let active = true;

  const consulta = isBalconista
    ? api.periodStatus(selectedMonth)
    : api.finance(selectedMonth);

  consulta
    .then(v => {
      if (active) setFinance(v);
    })
    .catch(e => {
      if (active) {
        setFinance(null);
        setError(e.message);
      }
    });

  return () => {
    active = false;
  };
}, [selectedMonth, data.transactions]);
  const reloadAfter = async message => {
    setModal(null);setEdit(null);await refresh();notify(message);
  };
  const runAction = async (fn,message) => {
    setBusy(true);
    try { await fn(); await reloadAfter(message); }
    catch(e) { notify('Erro: '+e.message); }
    finally { setBusy(false); }
  };
  const open=(kind,obj=null)=>{setEdit(obj);setModal(kind)};
  const submitModal=async (kind,v,editing) => {
    // if(kind==='sale') {
    //   return runAction(()=>api.registerSale({produto:Number(v.productId),barbeiro:Number(v.barberId),quantidade:Number(v.quantity),data:v.date}), 'Venda e comissão registradas no PostgreSQL');
    // }
    if (kind === 'sale') {
  const payload = {
    produto: Number(v.productId),
    quantidade: Number(v.quantity),
    data: v.date
  };

  // Apenas o administrador envia o barbeiro vendedor.
  // Vendas anteriores do balcão continuam sendo
  // atribuídas à Administração após uma edição.
  // if (
  //   !isBalconista &&
  //   !(editing && editing.barberId == null)
  // ) {
  //   payload.barbeiro = Number(v.barberId);
  // }
  if (isBalconista) {
  // O balcão pode escolher um barbeiro.
  // Barbearia (valor vazio) = Administração.
  payload.barbeiro = v.barberId
    ? Number(v.barberId)
    : null;

} else if (!(editing && editing.barberId == null)) {
  // Preserva o funcionamento atual do administrador.
  payload.barbeiro = Number(v.barberId);
}

  return runAction(
    () => editing
      ? api.update('sales', editing.id, payload)
      : api.registerSale(payload),

    editing
      ? 'Venda atualizada com sucesso'
      : 'Venda registrada com sucesso'
  );
}
    if(kind==='expense') {
      return runAction(()=>api.create('expenses',{descricao:v.description,data:v.date,valor:Number(v.expense)}),'Despesa registrada');
    }
    if(kind==='timeoffs') {
      const payload={barbeiro:Number(v.barberId),data:v.date,motivo:v.reason||''};
      return runAction(()=>editing?api.update('timeoffs',editing.id,payload):api.create('timeoffs',payload), 'Folga registrada');
    }
    const body=toApi(kind,v,!!editing,editing);
    if(kind==='appointments' && !editing && body.status==='concluido') {
      return notify('Crie como confirmado e depois conclua o atendimento.');
    }
    // await runAction(()=>editing?api.update(kind,editing.id,body):api.create(kind,body), editing?'Registro atualizado':'Registro cadastrado');
  await runAction(async () => {
  const registro = editing
    ? await api.update(kind, editing.id, body)
    : await api.create(kind, body);

  const id = editing ? editing.id : registro.id;

  if (kind === 'products' && v.imageFile) {
    await api.uploadImage('products', id, v.imageFile);
  }

  if (kind === 'barbers' && v.photoFile) {
    await api.uploadImage('barbers', id, v.photoFile);
  }

}, editing ? 'Registro atualizado' : 'Registro cadastrado');
  };
  const remove=async(kind,id)=>{
    if(!window.confirm('Excluir este registro? Registros financeiros contabilizados não podem ser apagados.'))return;
    await runAction(()=>api.remove(kind,id),'Registro excluído');
  };
  const complete=async appointment=>{
    if(!window.confirm(`Concluir e registrar pagamento do atendimento de ${appointment.client}?`))return;
    await runAction(()=>api.update('appointments',appointment.id,{status:'concluido',pago:true}), 'Atendimento concluído e comissão lançada no mês do recebimento');
  };
  const reverseSale=async sale=>{
    if(!sale || !window.confirm(`Estornar venda de ${sale.productName}? O estoque será devolvido e a comissão retirada do balanço.`))return;
    await runAction(()=>api.reverseSale(sale.id),'Venda estornada e estoque devolvido');
  };
  const closeFinancialMonth=async()=>{
    if(!window.confirm(`Fechar DEFINITIVAMENTE ${selectedMonth}? Não será possível lançar vendas ou despesas nesse mês.`))return;
    setBusy(true);
    try { const result=await api.closeMonth(selectedMonth); setFinance(result);notify('Mês fechado com sucesso'); }
    catch(e){notify('Erro: '+e.message)}
    finally{setBusy(false)}
  };
  const barber=id=>data.barbers.find(b=>String(b.id)===String(id));
  const product = id => data.products.find(
  p => String(p.id) === String(id)
);
  const service=id=>data.services.find(s=>String(s.id)===String(id));
  const filtered=kind=>data[kind].filter(x=>Object.values(x).some(v=>String(v??'').toLowerCase().includes(search.toLowerCase())));
  const monthTx=data.transactions.filter(t=>t.date?.startsWith(selectedMonth));
  const revenue=Number(finance?.receita_bruta||0);
  const costs=Number(finance?.custo_produtos||0)+Number(finance?.despesas||0);
  const commissions=Number(finance?.comissoes||0);
  const owner=Number(finance?.saldo_proprietario||0);
  const stats=[
    {label:'Agendamentos hoje',value:data.appointments.filter(a=>a.date===today()&&a.status!=='Cancelado').length,icon:CalendarDays},
    {label:'Clientes cadastrados',value:data.clients.length,icon:Users},
    {label:'Receita do mês',value:money(data.transactions.filter(t=>t.date?.startsWith(month())).reduce((sum,t)=>sum+Number(t.amount||0),0)),icon:Wallet},
    {label:'Produtos no estoque',value:data.products.reduce((sum,p)=>sum+Number(p.stock),0),icon:Package},
  ];
  const chart=Array.from({length:7},(_,i)=>{
    const d=new Date();d.setDate(d.getDate()-6+i);
    const date=new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10);
    return {name:d.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'}),valor:data.transactions.filter(t=>t.date===date).reduce((sum,t)=>sum+Number(t.amount||0),0)};
  });
  // const exportCSV=()=>{
  //   const rows=[['Data','Tipo','Descrição','Barbeiro','Receita','Custo/Despesa','Comissão'],...monthTx.map(t=>[t.date,t.kind,t.description,barber(t.barberId)?.name||'',t.amount,t.expense,t.commission])];
  //   const safe = v => { const text = String(v ?? ''); return /^[=+@\-\t\r]/.test(text.trimStart()) ? '\'' + text : text; };
  //   const csv='\ufeff'+rows.map(row=>row.map(v=>'"'+safe(v).replaceAll('"','""')+'"').join(';')).join('\r\n');
  //   const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  //   const a=document.createElement('a');a.href=url;a.download=`financeiro-${selectedMonth}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
  // };

const exportExcel = async () => {
  setBusy(true);

  try {
    const blob = await downloadExcel(selectedMonth);

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = `Brenner_Relatorio_${selectedMonth}.xlsx`;

    document.body.appendChild(a);
    a.click();
    a.remove();

    setTimeout(() => URL.revokeObjectURL(url), 2000);

    notify('Relatório Excel exportado com sucesso');
  } catch (e) {
    notify('Erro na exportação: ' + e.message);
  } finally {
    setBusy(false);
  }
};

return <div className="app">
  <aside className={'sidebar '+(sidebar?'show':'')}>
    <div className="brand">
      <span className="crown">♛</span>
      <small>BARBEARIA</small>
      <strong>BRENNER</strong>
      <em>ESTILO TEM NOME</em>
      </div>
      {/* <nav>
        {nav.map(([key,label,Icon])=>
        <button key={key}
          className={'nav '+(page===key?'active':'')}
          onClick={()=>{setPage(key);setSearch('');setSidebar(false)}}>
          <Icon size={19}/>
          {label}
        </button>)}
      </nav> */}
      <nav>
  {menuVisible.map(([key, label, Icon]) => (
    <button
      key={key}
      className={'nav ' + (page === key ? 'active' : '')}
      onClick={() => {
        setPage(key);
        setSearch('');
        setSidebar(false);
      }}
    >
      <Icon size={19}/>
      {label}
    </button>
  ))}
</nav>
          <div className="sidebottom">
            <div className="sidephoto">
              </div>
              <span>MAIS QUE CORTES,<br/> CONFIANÇA.</span>
              <small>GESTÃO INTELIGENTE</small>
              </div>
              </aside>{sidebar&&<div className="overlay" onClick={()=>setSidebar(false)}/>}
                <main>
                  <header>
                    <button className="iconbtn menu" onClick={()=>setSidebar(!sidebar)}>
                      <Menu/>
                    </button>
                    <div className="topsearch">
                    <Search size={17}/>
                    <input placeholder="Buscar nesta página..." value={search} onChange={e=>setSearch(e.target.value)}/>
                    </div>
                    <span className="topright">
                      <span className="online"/> {loading ? 'Carregando...' : (isDesktop ? 'Dados locais disponíveis' : 'Banco de dados conectado')}
                      <span className="avatar">MB</span>
                      {/* <b>{admin?.email || 'Administrador'}</b> */}
                      <b>
  {admin?.email || (isBalconista ? 'Balconista' : 'Administrador')}
</b>
<button className="iconbtn" onClick={onLogout} title="Sair do painel">
  <LogOut size={17}/>
</button>
</span>
</header>
<div className="content">
    {/* {!isBalconista && <LembreteMensalidade />} */}
    {!isBalconista && page === 'dashboard' && (
  <LembreteMensalidade />
)}

  {error&&
  <div className="apierror">
    <AlertCircle size={16}/>
    <span>{error}</span>
    <button onClick={refresh} className="secondary">
      Tentar novamente
      </button>
      </div>}<div className="hero"><div><div className="eyebrow">BARBEARIA BRENNER · PAINEL DE GESTÃO</div><h1>{({dashboard:'Visão geral',appointments:'Agendamentos',products:'Produtos & Estoque',barbers:'Barbeiros',services:'Serviços',clients:'Clientes',sales:'Vendas',finance:'Financeiro & Comissões',sync:'Sincronização'})[page]}</h1><p>{({dashboard:'Bem-vindo! Aqui está o resumo do seu negócio.',appointments:'Organize a agenda, horários e atendimentos.',products:'Gerencie produtos, preços, custos e vendas.',barbers:'Equipe, especialidades e percentuais de comissão.',services:'Catálogo de cortes, serviços e preços.',clients:'Sua base de clientes sempre organizada.',sales:'Registre vendas, acompanhe comissões e realize estornos.',finance:'Fechamento mensal, repasses e resultado do proprietário.',sync:'Acompanhe a fila local e o envio seguro de alterações.'})[page]}</p></div><div className="heroquote">DISCIPLINA<br/> TAMBÉM É ESTILO.<div className="goldline"/></div></div>
{isDesktop && page==='sync' && <SincronizacaoDesktop onUpdated={refresh}/>}
{page==='dashboard'&&<><div className="statgrid">{stats.map((s,i)=><div className="stat" key={i}><span className="stat-icon"><s.icon size={21}/></span><div><small>{s.label}</small><strong>{s.value}</strong><span className="subtle">Visão atualizada</span></div></div>)}</div><div className="two"><section className="panel"><div className="panelhead"><h3><TrendingUp size={18}/> Faturamento nos últimos 7 dias</h3><span className="tag">Receitas</span></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#d9a74d" stopOpacity={.36}/><stop offset="95%" stopColor="#d9a74d" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#282829" vertical={false}/><XAxis dataKey="name" stroke="#777" fontSize={11}/><YAxis stroke="#777" fontSize={11}/><Tooltip formatter={money} contentStyle={{background:'#191919',border:'1px solid #393027'}}/><Area type="monotone" dataKey="valor" stroke="#e4b45c" fill="url(#fill)" strokeWidth={3}/></AreaChart></ResponsiveContainer></div></section><section className="panel"><div className="panelhead"><h3><CalendarCheck size={18}/> Próximos agendamentos</h3><button className="link" onClick={()=>setPage('appointments')}>Ver todos →</button></div><div className="stack">{data.appointments.filter(a=>a.status!=='Cancelado').sort((a,b)=>`${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`)).slice(0,5).map(a=><div className="appointmentrow" key={a.id}><span className="time">{a.time}</span><span><b>{a.client}</b><small>{service(a.serviceId)?.name} · {barber(a.barberId)?.name}</small></span><span className={'status '+a.status.toLowerCase()}>{a.status}</span></div>)}</div></section></div><div className="quick"><div><h3>Controle total da sua barbearia</h3><p>Gerencie serviços, vendas e comissões em um só lugar.</p></div><button className="primary" onClick={()=>open('appointments')}><Plus size={17}/> Novo agendamento</button></div></>}
{page==='appointments'&&<>
  <div className="toolbar">
    <div className="tabs">
      <button className="selected">
        Agenda
      </button>
      <button onClick={()=>setSelectedDate(today())}>
        Hoje
      </button>
    </div>
    <div className="toolbar-right">
      <input className="dateinput" type="date" value={selectedDate} onChange={e=>setSelectedDate(e.target.value)}/>
      <button className="primary" onClick={()=>open('appointments')}>
        <Plus size={17}/>
        Novo agendamento
      </button>
      </div>
      </div>
      <div className="panel">
      <div className="panelhead">
        <h3>
          <CalendarDays size={19}/>
          Agenda de {new Date(selectedDate+'T12:00').toLocaleDateString('pt-BR',{dateStyle:'full'})}
        </h3>
        <span className="tag">{data.appointments.filter(x=>x.date===selectedDate).length}
          agendamentos
        </span>
        </div>
        <div className="appointmentsgrid">
          {data.barbers.map(b=><div className="barbercolumn" key={b.id}>
            <div className="barberheading">
              <span className="miniavatar">
                {b.name.split(' ').map(x=>x[0]).slice(0,2).join('')}
              </span>
              <div>
              <b>{b.name}</b>
              <small>{b.specialty}</small>
              </div>
              </div>{data.appointments.filter(a=>a.date===selectedDate&&String(a.barberId)===String(b.id)).sort((a,b)=>a.time.localeCompare(b.time)).map(a=><div className="slot" key={a.id}><div className="slot-top"><strong>{a.time}</strong><span className={'status '+a.status.toLowerCase()}>{a.status}</span></div><b>{a.client}</b><small>{service(a.serviceId)?.name}</small><div className="actions"><button onClick={()=>open('appointments',a)}><Pencil size={14}/></button>{a.status!=='Concluído'&&<button title="Concluir atendimento" onClick={()=>complete(a)}><Check size={14}/></button>}<button onClick={()=>remove('appointments',a.id)}><Trash2 size={14}/></button></div></div>)}<button className="addslot" onClick={()=>open('appointments',{barberId:b.id,date:selectedDate})}><Plus size={16}/> Adicionar horário</button></div>)}</div></div><div className="panel space"><div className="panelhead"><h3>Todos os agendamentos</h3></div><Table heads={['Data / Hora','Cliente','Serviço','Barbeiro','Status','Ações']} rows={filtered('appointments').map(a=>[`${a.date} · ${a.time}`,a.client,service(a.serviceId)?.name,barber(a.barberId)?.name,<span className={'status '+a.status.toLowerCase()}>{a.status}</span>,
              // <Actions edit={()=>open('appointments',a)} remove={()=>remove('appointments',a.id)}/>])}/>
              <Actions
  edit={() => open('appointments', a)}

  complete={
    !a.paid &&
    ['Aguardando', 'Confirmado'].includes(a.status)
      ? () => complete(a)
      : undefined
  }

  remove={() => remove('appointments', a.id)}
/>])}/>
              </div>
              </>}
{page==='products'&&<><div className="toolbar"><div className="tabs"><span className="tag">{data.products.length} produtos</span><span className="tag">{data.products.filter(p=>Number(p.stock)<=Number(p.minStock)).length} com estoque baixo</span></div><div className="toolbar-right"><button className="secondary" onClick={()=>open('sale')}><ShoppingBag size={17}/> Registrar venda</button><button className="primary" onClick={()=>open('products')}><Plus size={17}/> Novo produto</button></div></div><div className="productgrid">{filtered('products').map(p=><article className="product" key={p.id}><div className="productimage"><img src={p.image||'https://images.unsplash.com/photo-1594035910387-fea47794261f?w=400&q=80'} onError={e=>e.currentTarget.style.display='none'}/><span className="category">{p.category}</span></div><div className="productbody"><h3>{p.name}</h3><p>Preço de venda <strong>{money(p.price)}</strong></p><p>Custo <span>{money(p.cost)}</span></p><p>Margem bruta <span>{money(Number(p.price)-Number(p.cost))}</span></p><div className="productbottom"><span className={'status '+(Number(p.stock)<=Number(p.minStock)?'cancelado':'concluído')}>{p.stock} unidades</span><div className="actions"><button title="Editar" onClick={()=>open('products',p)}><Pencil size={16}/></button><button title="Excluir" onClick={()=>remove('products',p.id)}><Trash2 size={16}/></button></div></div></div></article>)}</div></>}
{page==='sales'&&<>
<div className="toolbar"><div className="tabs"><span className="tag">{data.sales.filter(s=>!s.reversed).length} vendas ativas</span><input className="dateinput" type="month" value={selectedMonth} onChange={e=>setSelectedMonth(e.target.value)}/></div><button className="primary" onClick={()=>open('sale')}><Plus size={17}/> Nova venda</button></div>
<div className="statgrid">{[
{label:'Vendas de produtos',value:data.sales.filter(s=>s.date.startsWith(selectedMonth)&&!s.reversed).length},
{label:'Faturamento com produtos',value:money(data.sales.filter(s=>s.date.startsWith(selectedMonth)&&!s.reversed).reduce((sum,s)=>sum+s.amount,0))},
// {label:'Comissões de produtos',
//   value:money(
//     data.sales
//     .filter(s=>s.date.startsWith(selectedMonth)&&!s.reversed)
//     .reduce((sum,s)=>sum+s.commission,0))},
// {label:'Produtos em estoque',value:data.products.reduce((sum,p)=>sum+Number(p.stock),0)}
...(!isBalconista ? [{
  label: 'Comissões de produtos',
  value: money(
    data.sales
      .filter(s => s.date.startsWith(selectedMonth) && !s.reversed)
      .reduce((sum, s) => sum + s.commission, 0)
  )
}] : []),
].map((s,i)=><div className="stat" key={i}><span className="stat-icon"><ShoppingBag size={21}/></span><div><small>{s.label}</small><strong>{s.value}</strong><span className="subtle">{selectedMonth}</span></div></div>)}</div>
<div className="panel">
  <div className="panelhead">
    <h3>
      <ShoppingBag size={18}/>
      Histórico de vendas
      </h3>
      <span className="tag">
        Estorno devolve unidades ao estoque
        </span>
        </div>
        {/* <Table heads={['Data','Produto','Vendedor','Quantidade','Valor','Comissão','Status','Ações']}  */}
        <Table
  heads={
    isBalconista
      ? [
          'Data',
          'Produto',
          'Vendedor',
          'Quantidade',
          'Valor',
          'Status',
          'Ações'
        ]
      : [
          'Data',
          'Produto',
          'Vendedor',
          'Quantidade',
          'Valor',
          'Comissão',
          'Status',
          'Ações'
        ]
  }
// rows={data.sales.filter(s=>s.date.startsWith(selectedMonth) && [s.productName,s.barberName].some(v=>String(v||'').toLowerCase().includes(search.toLowerCase()))).map(s=>[s.date,s.productName,s.barberName,s.quantity,money(s.amount),money(s.commission),<span className={'status '+(s.reversed?'cancelado':'concluído')}>{s.reversed?'Estornada':'Confirmada'}</span>,!s.reversed?<button className="secondary" disabled={busy||finance?.fechado} onClick={()=>reverseSale(s)}><Undo2 size={15}/> Estornar</button>:<span>—</span>])}/>
rows={data.sales
  .filter(s =>
    s.date.startsWith(selectedMonth) &&
    [s.productName, s.barberName].some(v =>
      String(v || '').toLowerCase().includes(search.toLowerCase())
    )
  )
  // .map(s => [
  //   s.date,
  //   s.productName,
  //   s.barberName,
  //   s.quantity,
  //   money(s.amount),
  .map(s => [
  s.date,

  <span className="sale-product-cell">
    {product(s.productId)?.image && (
      <img
        className="sale-product-thumb"
        src={product(s.productId).image}
        alt={s.productName}
      />
    )}

    {s.productName}
  </span>,

  s.barberName,
  s.quantity,
  money(s.amount),

    ...(!isBalconista ? [money(s.commission)] : []),

    <span className={'status ' + (s.reversed ? 'cancelado' : 'concluído')}>
      {s.reversed ? 'Estornada' : 'Confirmada'}
    </span>,

    // !s.reversed
    //   ? <button
    //       className="secondary"
    //       disabled={busy || finance?.fechado}
    //       onClick={() => reverseSale(s)}
    //     >
    //       <Undo2 size={15}/> Estornar
    //     </button>
    //   : <span>—</span>
    <div className="actions">

  {/* Só o administrador pode editar */}
  {!isBalconista &&
    !s.reversed &&
    !finance?.fechado && (
      <button
        title="Editar venda"
        disabled={busy}
        onClick={() => open('sale', s)}
      >
        <Pencil size={16}/>
      </button>
    )
  }

  {/* Mantém o estorno existente */}
  {!s.reversed ? (
    <button
      className="secondary"
      disabled={busy || finance?.fechado}
      onClick={() => reverseSale(s)}
    >
      <Undo2 size={15}/> Estornar
    </button>
  ) : (
    <span>—</span>
  )}

</div>
  ])}/>
</div>
{/* <p className="hint">Valor, estoque e percentual da comissão são calculados pelo Django no registro da venda. Não é permitido apagar uma venda; use estorno.</p> */}
<p className="hint">
  {isBalconista
    ? 'O valor da venda e a baixa no estoque são calculados automaticamente. Para cancelar uma venda, utilize o estorno.'
    : 'Valor, estoque e percentual da comissão são calculados pelo banco de dados no registro da venda. Não é permitido apagar uma venda; use estorno.'}
</p>
</>}
{page==='barbers'&&<><div className="toolbar"><span className="tag">{data.barbers.length} profissionais</span><button className="primary" onClick={()=>open('barbers')}><Plus size={17}/> Novo barbeiro</button></div><div className="panel"><Table heads={['Profissional','Contato','Especialidade','Comissão serviços','Comissão produtos','Status','Ações']} rows={filtered('barbers').map(b=>[<span className="person"><span className="miniavatar">
  {b.photoUrl ? (
    <img
      src={b.photoUrl}
      alt={b.name}
      style={{
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        borderRadius: '50%'
      }}
    />
  ) : (
    b.name.slice(0,2).toUpperCase()
  )}
</span><b>{b.name}</b></span>,b.phone,b.specialty,<b className="gold">{b.commission}%</b>,<b className="gold">{b.productCommission}%</b>,<span className="status concluído">{b.status}</span>,<Actions edit={()=>open('barbers',b)} remove={()=>remove('barbers',b.id)}/>])}/></div><p className="hint">As comissões são congeladas em cada lançamento. Os horários de cada barbeiro são editáveis no cadastro. As folgas são registradas abaixo.</p></>}
{page==='barbers'&&<div className="panel space"><div className="panelhead"><h3><CalendarDays size={18}/> Folgas e bloqueios de agenda</h3><button className="secondary" onClick={()=>open('timeoffs')}><Plus size={16}/> Registrar folga</button></div><Table heads={['Data','Barbeiro','Motivo','Ações']} rows={data.timeoffs.filter(f=>[f.barberName,f.reason,f.date].some(v=>String(v||'').toLowerCase().includes(search.toLowerCase()))).map(f=>[f.date,f.barberName,f.reason,<Actions edit={()=>open('timeoffs',f)} remove={()=>remove('timeoffs',f.id)}/>])}/></div>}
{page==='services'&&<><div className="toolbar"><span className="tag">{data.services.length} serviços</span><button className="primary" onClick={()=>open('services')}><Plus size={17}/> Novo serviço</button></div><div className="panel"><Table heads={['Serviço','Preço','Duração','Ações']} rows={filtered('services').map(s=>[<b>{s.name}</b>,<b className="gold">{money(s.price)}</b>,`${s.duration} minutos`,<Actions edit={()=>open('services',s)} remove={()=>remove('services',s.id)}/>])}/></div></>}
{page==='clients'&&<><div className="toolbar"><span className="tag">{data.clients.length} clientes</span><button className="primary" onClick={()=>open('clients')}><Plus size={17}/> Novo cliente</button></div><div className="panel"><Table heads={['Nome','Telefone','Agendamentos','Ações']} rows={filtered('clients').map(c=>[<b>{c.name}</b>,c.phone,data.appointments.filter(a=>a.client===c.name).length,<Actions edit={()=>open('clients',c)} remove={()=>remove('clients',c.id)}/>])}/></div></>}
{page==='finance'&&<>
<div className="toolbar"><div className="tabs"><span className="tag">{finance?.fechado?'Mês fechado':'Fechamento mensal'}</span><input className="dateinput" type="month" value={selectedMonth} onChange={e=>setSelectedMonth(e.target.value)}/></div><div className="toolbar-right"><button
  className="secondary"
  onClick={exportExcel}
  disabled={busy}
>
  <Download size={17}/>
  Exportar Excel
</button><button className="secondary" disabled={busy||finance?.fechado||selectedMonth>=month()} title="Somente meses anteriores podem ser fechados" onClick={closeFinancialMonth}><Check size={16}/> Fechar mês</button><button className="primary" disabled={busy||finance?.fechado} onClick={()=>open('expense')}><Plus size={17}/> Registrar despesa</button></div></div>
<div className="statgrid financegrid">{[{label:'Receita bruta',value:revenue},{label:'Custos e despesas',value:costs},{label:'Comissões dos barbeiros',value:commissions},{label:'Resultado do proprietário',value:owner}].map((s,i)=><div className="stat" key={i}><span className="stat-icon"><Wallet size={20}/></span><div><small>{s.label}</small><strong>{money(s.value)}</strong><span className="subtle">{selectedMonth}</span></div></div>)}</div>
<div className="two"><div className="panel"><div className="panelhead"><h3><Users size={18}/> Repasse por barbeiro</h3></div><Table heads={['Barbeiro','Serviços','Produtos','Total a receber']} rows={(finance?.repasses||[]).map(r=>[r.barbeiro,money(r.servicos),money(r.produtos),<b className="gold">{money(r.total)}</b>])}/></div><div className="panel"><div className="panelhead"><h3><TrendingUp size={18}/> Distribuição da receita</h3></div><div className="piearea"><ResponsiveContainer width="100%" height={240}><PieChart><Pie data={[{name:'Proprietário',value:Math.max(0,owner)},{name:'Comissões',value:commissions},{name:'Custos',value:costs}].filter(r=>r.value>0)} dataKey="value" innerRadius={66} outerRadius={95} paddingAngle={3}>{['#e3b760','#ad8244','#555052'].map((c,i)=><Cell key={i} fill={c}/>)}</Pie><Tooltip formatter={money}/></PieChart></ResponsiveContainer><div className="legend"><span>● Proprietário: {money(owner)}</span><span>● Comissões: {money(commissions)}</span><span>● Custos: {money(costs)}</span></div></div></div></div>
<div className="panel space"><div className="panelhead"><h3>Movimentações do mês</h3><button className="secondary" disabled={busy||finance?.fechado} onClick={()=>open('sale')}><Plus size={15}/> Registrar venda</button></div>
{/* <Table
heads={
  isBalconista
    ? [
        'Data',
        'Produto',
        'Vendedor',
        'Quantidade',
        'Valor',
        'Status',
        'Ações'
      ]
    : [
        'Data',
        'Produto',
        'Vendedor',
        'Quantidade',
        'Valor',
        'Comissão',
        'Status',
        'Ações'
      ]
}
rows={monthTx.map(t=>[t.date,t.description,t.kind,
// barber(t.barberId)?.name||'—',
barber(t.barberId)?.name ||
  (t.kind === 'Produto' ? 'Administração' : '—'),
money(t.amount)
,money(t.expense),
money(t.commission),
t.kind==='Despesa'&&!finance?.fechado?
<button className="iconbtn" title="Excluir despesa" onClick={()=>remove('expenses',t.refId)}>
  <Trash2 size={15}/>
</button>
  :t.kind==='Produto'&&!t.reversed&&!finance?.fechado?
<button className="secondary" onClick={()=>reverseSale(data.sales.find(s=>s.id===t.refId))}>
  Estornar
</button>:'—'])}
/> */}
<Table
  heads={[
    'Data',
    'Descrição',
    'Tipo',
    'Responsável',
    'Receita',
    'Custo / Despesa',
    'Comissão',
    'Ações'
  ]}

  rows={monthTx.map(t => [
    t.date,

    t.description,

    t.kind,

    barber(t.barberId)?.name ||
      (t.kind === 'Produto' ? 'Administração' : '—'),

    money(t.amount),

    money(t.expense),

    money(t.commission),

    t.kind === 'Despesa' && !finance?.fechado
      ? (
          <button
            className="iconbtn"
            title="Excluir despesa"
            onClick={() => remove('expenses', t.refId)}
          >
            <Trash2 size={15}/>
          </button>
        )
      : t.kind === 'Produto' && !t.reversed && !finance?.fechado
        ? (
            <button
              className="secondary"
              onClick={() => reverseSale(
                data.sales.find(s => s.id === t.refId)
              )}
            >
              Estornar
            </button>
          )
        : '—'
  ])}
/>
</div>
<p className="hint">Resultado do proprietário = receitas de serviços e produtos − custo dos produtos − despesas − comissões. Cálculos e fechamentos vêm do banco de dados; valores consolidados não são recalculados no navegador.</p>
</>}
</div></main>{modal&&<Modal key={`${modal}-${edit?.id||'new'}`} kind={modal} initial={edit} data={data} close={()=>{setModal(null);setEdit(null)}} submit={submitModal} busy={busy}/>} {loading&&<div className="loadingstate"><LoaderCircle className="spin"/> Atualizando dados...</div>}{toast&&<div className="toast"><Check size={16}/>{toast}</div>}</div>}

// function Actions({edit,remove}) {
//   return <div className="actions">
//   <button title="Editar" onClick={edit}>
//     <Pencil size={16}/>
//   </button>
//   <button title="Excluir" onClick={remove}>
//     <Trash2 size={16}/>
//   </button>
//   </div>;
//   }
function Actions({ edit, remove, complete: completeAction }) {
  return (
    <div className="actions">

      {completeAction && (
        <button
          title="Marcar atendimento como concluído"
          onClick={completeAction}
        >
          <Check size={16}/>
        </button>
      )}
      <button title="Editar" onClick={edit}>
        <Pencil size={16}/>
      </button>


      <button title="Excluir" onClick={remove}>
        <Trash2 size={16}/>
      </button>

    </div>
  );
}
function Table({heads,rows}) { return <div className="tablewrap"><table><thead><tr>{heads.map((h,i)=><th key={i}>{h}</th>)}</tr></thead><tbody>{rows.length?rows.map((r,i)=><tr key={i}>{r.map((c,j)=><td key={j}>{c??'—'}</td>)}</tr>):<tr><td colSpan={heads.length} className="empty">Nenhum registro encontrado.</td></tr>}</tbody></table></div>; }

const DEFAULT_HOURS=()=>Array.from({length:6},(_,day)=>[
  {dia_semana:day,inicio:'08:00',fim:'11:40'},
  {dia_semana:day,inicio:'14:00',fim:'19:40'},
]).flat();
const week=['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo'];

function ImagePicker({ label, current, file, onFile }) {
  const [preview, setPreview] = useState(current || '');

  useEffect(() => {
    if (!file) {
      setPreview(current || '');
      return;
    }

    const url = URL.createObjectURL(file);
    setPreview(url);

    return () => URL.revokeObjectURL(url);
  }, [file, current]);

  const selectFile = selected => {
    if (!selected) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(selected.type)) {
      alert('Escolha uma imagem JPG, PNG ou WEBP.');
      return;
    }

    if (selected.size > 5 * 1024 * 1024) {
      alert('A imagem deve ter no máximo 5 MB.');
      return;
    }

    onFile(selected);
  };

  return (
    <div className="field full">
      <span>{label}</span>

      <label
        className="upload-zone"
        onDragOver={e => e.preventDefault()}
        onDrop={e => {
          e.preventDefault();
          selectFile(e.dataTransfer.files?.[0]);
        }}
      >
        <input
          type="file"
          className="upload-native"
          accept="image/jpeg,image/png,image/webp"
          onChange={e => selectFile(e.target.files?.[0])}
        />

        {preview ? (
          <img
            src={preview}
            alt="Prévia da imagem selecionada"
            className="upload-preview"
          />
        ) : (
          <span className="upload-placeholder">
            <Package size={32} />
            Nenhuma imagem selecionada
          </span>
        )}

        <strong>Arraste uma imagem ou clique para selecionar</strong>
        <small>JPG, PNG ou WEBP — máximo 5 MB</small>
      </label>
    </div>
  );
}

function Modal({kind,initial,data,close,submit,busy}) {
  const defaultValues={
    appointments:{client:'',clientId:'',clientPhone:'',barberId:data.barbers.find(b=>b.status==='Ativo')?.id||'',serviceId:data.services[0]?.id||'',date:today(),time:'09:00',status:'Confirmado',notes:''},
    products:{name:'',category:'Pomadas',price:0,cost:0,stock:0,minStock:5,image:'',description:'',active:true},
    barbers:{name:'',phone:'',specialty:'Corte masculino',commission:40,productCommission:10,status:'Ativo',photoUrl:'',horarios:DEFAULT_HOURS()},
    services:{name:'',description:'',price:0,duration:40,image:'',active:true},
    clients:{name:'',phone:''},
    // sale:{
    //   productId:data.products.find(p=>p.stock>0)?.id||'',
    //   barberId:data.barbers.find(b=>b.status==='Ativo')?.id||'',
    //   quantity:1,
    //   date:today()
    // },
    sale: {
  productId: data.products.find(p => p.stock > 0)?.id || '',

  barberId: isBalconista
    ? ''
    : data.barbers.find(b => b.status === 'Ativo')?.id || '',

  quantity: 1,
  date: today()
},
    expense:{description:'',expense:0,date:today()},
    timeoffs:{barberId:data.barbers[0]?.id||'',date:today(),reason:''},
  };
  const [v,setV]=useState(()=>({...defaultValues[kind],...initial}));
  const selectedSaleProduct = data.products.find(
  p => String(p.id) === String(v.productId)
);
  const field=(key,value)=>setV(p=>({...p,[key]:value}));
  const f=(label,key,type='text',opts,required=false)=> <label className="field"><span>{label}</span>{opts?<select value={v[key]??''} onChange={e=>field(key,e.target.value)} required={required}>{opts.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>:<input type={type} min={type==='number'?'0':undefined} max={key==='commission'||key==='productCommission'?100:undefined} step={type==='number'?['stock','minStock','quantity','duration'].includes(key)?1:'.01':undefined} value={v[key]??''} onChange={e=>field(key,type==='number'?Number(e.target.value):e.target.value)} required={required}/>}</label>;
  const options=(arr,label)=>arr.map(x=>({value:x.id,label:x[label]}));
  const title={appointments:'Agendamento',products:'Produto',barbers:'Barbeiro',services:'Serviço',clients:'Cliente',sale:'Venda',expense:'Despesa',timeoffs:'Folga'}[kind];
  const setHours=(day,shift,key,value)=>setV(p=>{
    const horarios=(p.horarios||[]).filter(x=>x.dia_semana!==day).concat(
      (p.horarios||[]).filter(x=>x.dia_semana===day).map((x,i)=>i===shift?{...x,[key]:value}:x)
    );
    return {...p,horarios};
  });
  const toggleDay=day=>setV(p=>({
    ...p,horarios:(p.horarios||[]).some(x=>x.dia_semana===day)
      ?(p.horarios||[]).filter(x=>x.dia_semana!==day)
      :[...(p.horarios||[]),{dia_semana:day,inicio:'08:00',fim:'11:40'},{dia_semana:day,inicio:'14:00',fim:'19:40'}],
  }));
  const handleSubmit=e=>{
    e.preventDefault();
    if(kind==='appointments'&&!initial && !v.clientId && !v.clientPhone) return alert('Informe o telefone do novo cliente.');
    if(kind==='barbers'&&(Number(v.commission)>100||Number(v.productCommission)>100))return alert('Comissões não podem superar 100%.');
    return submit(kind,v,initial?.id?initial:null);
  };
  return <div className="modalshade" onMouseDown={e=>{if(e.target===e.currentTarget&&!busy)close()}}><div className="modal" role="dialog" aria-modal="true" aria-label={`${initial?.id?'Editar':'Novo'} ${title}`}>
    <div className="modalhead"><div><span className="eyebrow">BARBEARIA BRENNER</span><h2>{initial?.id?'Editar':'Novo'} {title}</h2></div><button className="iconbtn" disabled={busy} onClick={close} aria-label="Fechar"><X/></button></div>
    <form onSubmit={handleSubmit}><div className="formgrid">
      {kind==='appointments'&&<>
        {f('Barbeiro','barberId','text',options(data.barbers.filter(b=>b.status==='Ativo'||b.id===initial?.barberId),'name'),true)}
        {f('Serviço','serviceId','text',data.services.map(s=>({value:s.id,label:`${s.name} · ${money(s.price)}`})),true)}
        {initial?.id?<div className="full"><p className="hint">Cliente: <b>{initial.client}</b>. Para alterar nome/telefone, use a aba Clientes.</p></div>:<>
          {f('Selecionar cliente já cadastrado (opcional)','clientId','text',[{value:'',label:'Cadastrar novo cliente...'},...options(data.clients,'name')])}
          {!v.clientId&&<>{f('Nome do novo cliente','client','text',null,true)}{f('Telefone com DDD','clientPhone','tel',null,true)}</>}
        </>}
        {f('Data','date','date',null,true)}{f('Horário','time','time',null,true)}
        {f('Status','status','text',(initial?.id?['Aguardando','Confirmado','Concluído','Cancelado']:['Aguardando','Confirmado']).map(x=>({value:x,label:x})),true)}
        <div className="full">{f('Observações','notes')}</div>
        <p className="full hint">Horários são validados no banco de dados; ao concluir, o valor e a comissão são lançados no financeiro.</p>
      </>}
      {kind==='products'&&<>{f('Nome do produto','name','text',null,true)}{f('Categoria','category','text',['Pomadas','Barba','Shampoos','Acessórios','Outros'].map(x=>({value:x,label:x})))}{f('Preço (R$)','price','number',null,true)}{f('Custo (R$)','cost','number',null,true)}{f('Estoque','stock','number',null,true)}{f('Estoque mínimo','minStock','number')}<div className="full">
  <ImagePicker
    label="Foto do produto"
    current={v.image}
    file={v.imageFile}
    onFile={file => field('imageFile', file)}
  />

  {f('Descrição', 'description')}
</div></>}
      {kind==='barbers'&&<>{f('Nome','name','text',null,true)}{f('Telefone','phone','tel')}{f('Especialidade','specialty')}{f('Status','status','text',['Ativo','Inativo'].map(x=>({value:x,label:x})))}{f('Comissão por corte (%)','commission','number',null,true)}{f('Comissão por venda (%)','productCommission','number',null,true)}<div className="full">{f('URL da foto','photoUrl','url')}</div>
        <div className="full"><p className="eyebrow">HORÁRIOS SEMANAIS</p><p className="hint">Ative os dias e ajuste o expediente. O backend usa esses horários para validar agendamentos.</p><div className="schedulegrid">{week.map((label,day)=>{
          const hours=(v.horarios||[]).filter(h=>h.dia_semana===day).sort((a,b)=>a.inicio.localeCompare(b.inicio));
          return <div className="schedule-day" key={day}><label><input type="checkbox" checked={hours.length>0} onChange={()=>toggleDay(day)}/>{label}</label>{hours.length>0&&<div className="schedule-times">{hours.map((h,index)=><div key={index}><input aria-label="Início" type="time" required value={h.inicio.slice(0,5)} onChange={e=>setHours(day,index,'inicio',e.target.value)}/><span>até</span><input aria-label="Fim" type="time" required value={h.fim.slice(0,5)} onChange={e=>setHours(day,index,'fim',e.target.value)}/></div>)}</div>}</div>;
        })}</div></div>
      </>}
      {kind==='services'&&<>{f('Nome do serviço','name','text',null,true)}{f('Preço (R$)','price','number',null,true)}{f('Duração (minutos)','duration','number',null,true)}<div className="full">
  <ImagePicker
    label="Foto do barbeiro"
    current={v.photoUrl}
    file={v.photoFile}
    onFile={file => field('photoFile', file)}
  />
</div></>}
      {kind==='clients'&&<>{f('Nome completo','name','text',null,true)}{f('Telefone com DDD','phone','tel',null,true)}</>}
      {/* {kind==='sale'&&<>
      {f(
        'Produto',
        'productId',
        'text',
        data.products.filter(p=>p.stock>0).map(p=>({
          value:p.id,
          label:`${p.name} · ${money(p.price)} · estoque ${p.stock}`
          })),
          true
          )}{
            f(
              'Barbeiro vendedor',
              'barberId',
              'text',
              options(data.barbers.filter(b=>b.status==='Ativo'),'name'),
              true
              )}
              {f(
                'Quantidade','quantity','number',null,true)}
                {f('Data da venda','date','date',null,true)}
                <p className="hint full">
                  O preço e a comissão serão calculados pelo Django. A baixa de estoque é automática.
                </p>
              </>} */}
      {kind === 'sale' && <>

  {f(
    'Produto',
    'productId',
    'text',
    data.products
      .filter(p =>
        p.stock > 0 ||
        String(p.id) === String(v.productId)
      )
      .map(p => ({
        value: p.id,
        label: `${p.name} · ${money(p.price)} · estoque ${p.stock}`
      })),
    true
  )}

  {/* Foto completa do produto selecionado */}
  {selectedSaleProduct?.image && (
    <div className="sale-product-preview full">
      <img
        src={selectedSaleProduct.image}
        alt={selectedSaleProduct.name}
      />
      <span>{selectedSaleProduct.name}</span>
    </div>
  )}

  {/* Seleção de barbeiro somente no administrativo.
      Vendas do balcão mantêm sua atribuição original. */}
  {/* {!isBalconista &&
    !(initial?.id && initial.barberId == null) &&
    f(
      'Barbeiro vendedor',
      'barberId',
      'text',
      options(
        data.barbers.filter(
          b => b.status === 'Ativo' ||
               b.id === initial?.barberId
        ),
        'name'
      ),
      true
    )
  }

  {(isBalconista ||
    (initial?.id && initial.barberId == null)) && (
    <p className="hint full">
      Venda destinada à Administração, sem comissão de barbeiro.
    </p>
  )} */}
  {/* BALCÃO: Barbearia como opção padrão */}
{isBalconista && (
  f(
    'Destinar venda para',
    'barberId',
    'text',
    [
      {
        value: '',
        label: 'Barbearia'
      },
      ...options(
        data.barbers.filter(
          b => b.status === 'Ativo'
        ),
        'name'
      )
    ],
    false
  )
)}

{/* ADMIN: mantém o formulário existente */}
{!isBalconista &&
  !(initial?.id && initial.barberId == null) &&
  f(
    'Barbeiro vendedor',
    'barberId',
    'text',
    options(
      data.barbers.filter(
        b => b.status === 'Ativo' ||
             b.id === initial?.barberId
      ),
      'name'
    ),
    true
  )
}

{/* Mensagem informativa para o balcão */}
{isBalconista && (
  <p className="hint full">
    {v.barberId
      ? 'A venda será atribuída ao barbeiro selecionado.'
      : 'Venda destinada à Barbearia.'}
  </p>
)}

{/* Preserva a edição de vendas da Administração */}
{!isBalconista &&
  initial?.id &&
  initial.barberId == null && (
    <p className="hint full">
      Venda destinada à Administração, sem comissão de barbeiro.
    </p>
)}

  {f('Quantidade', 'quantity', 'number', null, true)}

  {f('Data da venda', 'date', 'date', null, true)}

  <p className="hint full">
    O Banco de dados calcula os valores e atualiza o estoque automaticamente.
  </p>

</>}
      {kind==='expense'&&<>{f('Descrição','description','text',null,true)}{f('Valor (R$)','expense','number',null,true)}{f('Data','date','date',null,true)}</>}
      {kind==='timeoffs'&&<>{f('Barbeiro','barberId','text',options(data.barbers,'name'),true)}{f('Data','date','date',null,true)}<div className="full">{f('Motivo','reason')}</div></>}
    </div><div className="modalfoot"><button type="button" className="secondary" disabled={busy} onClick={close}>Cancelar</button><button type="submit" disabled={busy} className="primary"><Save size={16}/>{busy?'Salvando...':'Salvar '+title.toLowerCase()}</button></div></form>
  </div></div>;
}
createRoot(document.getElementById('root')).render(<Root/>);
