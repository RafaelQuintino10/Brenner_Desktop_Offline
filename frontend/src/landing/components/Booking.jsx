
import React, { useEffect, useState } from 'react';
import { CalendarDays, MessageCircle } from 'lucide-react';

import SectionTitle from './SectionTitle';
import Reveal from './Reveal';

import { publicApi } from '../api';
import { WHATSAPP_NUMBER } from '../config';

function hojeLocal() {
  const d = new Date();

  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, '0'),
    String(d.getDate()).padStart(2, '0'),
  ].join('-');
}

export default function Booking({
  barbers = [],
  services = [],
}) {
  const [form, setForm] = useState({
    nome: '',
    telefone: '',
    barbeiro: '',
    servico: '',
    data: '',
    hora: '',
    observacao: '',
  });

  const [horarios, setHorarios] = useState([]);
  const [buscando, setBuscando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState(null);

  const alterar = (campo, valor) => {
    setForm(prev => ({
      ...prev,
      [campo]: valor,
      ...(campo === 'barbeiro' ||
         campo === 'servico' ||
         campo === 'data'
        ? { hora: '' }
        : {}),
    }));

    setErro('');
  };

  useEffect(() => {
    let ativo = true;

    if (!form.barbeiro || !form.servico || !form.data) {
      setHorarios([]);
      setBuscando(false);
      return;
    }

    setBuscando(true);
    setHorarios([]);

    publicApi.disponibilidade({
      barbeiro: form.barbeiro,
      servico: form.servico,
      data: form.data,
    })
      .then(response => {
        if (ativo) {
          setHorarios(response.horarios || []);
        }
      })
      .catch(error => {
        if (ativo) {
          setErro(error.message);
          setHorarios([]);
        }
      })
      .finally(() => {
        if (ativo) setBuscando(false);
      });

    return () => {
      ativo = false;
    };
  }, [form.barbeiro, form.servico, form.data]);

  async function agendar(event) {
    event.preventDefault();

    if (salvando || sucesso) return;

    const telefone = form.telefone.replace(/\D/g, '');

    if (telefone.length < 10 || telefone.length > 13) {
      setErro('Informe um telefone com DDD válido.');
      return;
    }

    if (!horarios.includes(form.hora)) {
      setErro('Escolha um horário disponível.');
      return;
    }

    setSalvando(true);
    setErro('');

    try {
      const reserva = await publicApi.agendar({
        cliente_nome: form.nome.trim(),
        cliente_telefone: telefone,
        barbeiro: Number(form.barbeiro),
        servico: Number(form.servico),
        data: form.data,
        hora: form.hora,
        observacao: form.observacao,
      });

      const barbeiro = barbers.find(
        b => String(b.id) === form.barbeiro
      );

      const servico = services.find(
        s => String(s.id) === form.servico
      );

      const mensagem = [
        'Olá! Fiz um agendamento pelo site da Barbearia Brenner.',
        '',
        `Reserva: #${reserva.id}`,
        `Nome: ${form.nome}`,
        `Telefone: ${telefone}`,
        `Serviço: ${servico?.nome || ''}`,
        `Barbeiro: ${barbeiro?.nome || ''}`,
        `Data: ${form.data.split('-').reverse().join('/')}`,
        `Horário: ${form.hora}`,
        form.observacao
          ? `Observações: ${form.observacao}`
          : '',
        '',
        'Gostaria de confirmar meu agendamento.',
      ].filter(Boolean).join('\n');

      const whatsapp =
        `https://wa.me/${WHATSAPP_NUMBER}?text=${
          encodeURIComponent(mensagem)
        }`;

      setSucesso({
        id: reserva.id,
        whatsapp,
      });

      // Somente abre o WhatsApp depois que
      // o Django confirmar o cadastro (HTTP 201).
      window.location.assign(whatsapp);

    } catch (error) {
      setErro(error.message);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <section
      id="agendar"
      className="section booking-section"
    >
      <div className="container">
        <Reveal direction="up">
          <SectionTitle
            title="Agende seu horário"
            sub="Escolha seu serviço, profissional e horário disponível."
          />
        </Reveal>

        <div className="booking-wrapper gold-card">
          <div className="booking-heading">
            <CalendarDays size={26} />

            <div>
              <h3>Reserve seu atendimento</h3>
              <p>
                Seu pedido será registrado e enviado
                à barbearia para confirmação.
              </p>
            </div>
          </div>

          {sucesso ? (
            <div className="booking-success" role="status">
              <h3>Reserva #{sucesso.id} registrada!</h3>
              <p>
                Seu agendamento está pendente de confirmação.
              </p>

              <a
                className="btn btn-whats"
                href={sucesso.whatsapp}
              >
                <MessageCircle size={18} />
                Abrir WhatsApp
              </a>
            </div>
          ) : (
            <form onSubmit={agendar} className="booking-form">
              <label>
                Nome completo
                <input
                  type="text"
                  required
                  maxLength={120}
                  value={form.nome}
                  onChange={e =>
                    alterar('nome', e.target.value)
                  }
                  placeholder="Seu nome"
                />
              </label>

              <label>
                WhatsApp com DDD
                <input
                  type="tel"
                  required
                  value={form.telefone}
                  onChange={e =>
                    alterar('telefone', e.target.value)
                  }
                  placeholder="(88) 99999-9999"
                />
              </label>

              <label>
                Serviço
                <select
                  required
                  value={form.servico}
                  onChange={e =>
                    alterar('servico', e.target.value)
                  }
                >
                  <option value="">Selecione o serviço</option>

                  {services.map(servico => (
                    <option key={servico.id} value={servico.id}>
                      {servico.nome} — R$ {servico.preco}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Barbeiro
                <select
                  required
                  value={form.barbeiro}
                  onChange={e =>
                    alterar('barbeiro', e.target.value)
                  }
                >
                  <option value="">Selecione o barbeiro</option>

                  {barbers.map(barbeiro => (
                    <option
                      key={barbeiro.id}
                      value={barbeiro.id}
                    >
                      {barbeiro.nome}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Data do agendamento
                <input
                  type="date"
                  required
                  min={hojeLocal()}
                  value={form.data}
                  onChange={e =>
                    alterar('data', e.target.value)
                  }
                />
              </label>

              <label>
                Horário disponível
                <select
                  required
                  value={form.hora}
                  disabled={
                    buscando ||
                    !form.data ||
                    !form.barbeiro ||
                    !form.servico
                  }
                  onChange={e =>
                    alterar('hora', e.target.value)
                  }
                >
                  <option value="">
                    {buscando
                      ? 'Buscando horários...'
                      : 'Selecione um horário'}
                  </option>

                  {horarios.map(hora => (
                    <option key={hora} value={hora}>
                      {hora}
                    </option>
                  ))}
                </select>
              </label>

              {!buscando &&
                form.data &&
                form.barbeiro &&
                form.servico &&
                horarios.length === 0 && (
                  <p className="booking-notice">
                    Não há horários livres para esta seleção.
                  </p>
                )}

              <label className="booking-full">
                Observações (opcional)
                <textarea
                  maxLength={250}
                  rows={3}
                  value={form.observacao}
                  onChange={e =>
                    alterar('observacao', e.target.value)
                  }
                  placeholder="Alguma preferência ou observação?"
                />
              </label>

              {erro && (
                <p
                  className="booking-error booking-full"
                  role="alert"
                >
                  {erro}
                </p>
              )}

              <div className="booking-full booking-submit">
                <button
                  type="submit"
                  className="btn btn-gold"
                  disabled={
                    salvando ||
                    buscando ||
                    !form.hora
                  }
                >
                  <MessageCircle size={19} />

                  {salvando
                    ? 'Registrando agendamento...'
                    : 'Agendar e abrir WhatsApp'}
                </button>

                <small>
                  A reserva será registrada como pendente.
                  A barbearia confirmará o atendimento.
                </small>
              </div>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}
