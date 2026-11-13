"""API local compatível com as rotas consumidas pelo React da Barbearia Brenner.

A API Django continua sendo autoridade: este adaptador NÃO tenta sobrescrever
conflitos e não confirma lançamentos no servidor antes de receber HTTP 2xx.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .store import Store, now_iso

RESOURCES = {
    'barbeiros': 'barbeiros', 'produtos': 'produtos', 'servicos': 'servicos',
    'clientes': 'clientes', 'agendamentos': 'agendamentos', 'vendas': 'vendas',
    'recebimentos-servicos': 'recebimentos-servicos', 'despesas': 'despesas',
    'folgas': 'folgas',
}
ADMIN_ONLY = {'despesas', 'folgas', 'recebimentos-servicos'}
READ_ONLY_BALCAO = {'barbeiros', 'produtos', 'servicos', 'clientes'}
FOREIGN = {'produto': 'produtos', 'barbeiro': 'barbeiros', 'cliente': 'clientes',
           'servico': 'servicos', 'agendamento': 'agendamentos'}


class ApiError(Exception):
    def __init__(self,code,message):
        super().__init__(str(message))
        self.code = code


class OfflineConnection(Exception):
    pass


class RemoteRejected(Exception):
    def __init__(self,code,message):
        super().__init__(str(message))
        self.code = code


def quant(v):
    return Decimal(str(v or 0)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def as_float(v):
    return float(quant(v))


class Engine:
    def __init__(self, remote_base:str, store:Store|None=None, *, timeout:float=3.0,
                 offline_login_valid_days:int=30):
        self.store=store or Store()
        self.store.recover_inflight()
        self.remote_base=remote_base.rstrip('/')
        if not self.remote_base.startswith(('https://','http://')):
            raise ValueError('A URL da API deve começar com https:// (ou http:// em desenvolvimento).')
        self.timeout=timeout
        self.offline_login_valid_days=offline_login_valid_days
        self.sessions={}
        self.last_connection_ok=False
        self.last_check=0.0
        self.net_lock=threading.RLock()
        self.sync_lock=threading.Lock()
        self.stop_event=threading.Event()

    def remote(self,path,method='GET',payload=None,token='',file_path=None,accept='application/json'):
        url=self.remote_base + (path if path.startswith('/') else '/'+path)
        data=None
        headers={'Accept':accept,'User-Agent':'BrennerDesktop/0.1'}
        if token:
            headers['Authorization']='Token '+token
        if file_path:
            filename=os.path.basename(file_path)
            ext=Path(filename).suffix.lower()
            content_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            boundary='----brenner'+secrets.token_hex(12)
            body=Path(file_path).read_bytes()
            data=(f'--{boundary}\r\nContent-Disposition: form-data; name="arquivo"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode()+body+f'\r\n--{boundary}--\r\n'.encode())
            headers['Content-Type']='multipart/form-data; boundary='+boundary
        elif payload is not None:
            data=json.dumps(payload,ensure_ascii=False).encode()
            headers['Content-Type']='application/json'
        request=urllib.request.Request(url,data=data,headers=headers,method=method)
        try:
            with urllib.request.urlopen(request,timeout=self.timeout) as response:
                raw=response.read()
                mime=response.headers.get('Content-Type','')
                if 'json' in mime or not raw:
                    try:return json.loads(raw) if raw else None
                    except (ValueError,UnicodeDecodeError):return raw
                return raw
        except urllib.error.HTTPError as e:
            content=e.read()[:2000]
            try:
                decoded=json.loads(content)
                reason=decoded.get('detail',decoded) if isinstance(decoded,dict) else decoded
            except Exception:
                reason=content.decode(errors='replace')
            raise RemoteRejected(e.code,reason) from e
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            raise OfflineConnection(str(e)) from e

    def is_online(self,force=False):
        now=time.monotonic()
        if not force and now-self.last_check<6:
            return self.last_connection_ok
        with self.net_lock:
            try:
                self.remote('/health/')
                self.last_connection_ok=True
            except (OfflineConnection,RemoteRejected):
                self.last_connection_ok=False
            self.last_check=now
        return self.last_connection_ok

    def identity(self,headers):
        auth=headers.get('Authorization','')
        token=auth.removeprefix('Token ').strip() if auth.startswith('Token ') else ''
        scope=self.sessions.get(token)
        if not scope:
            raise ApiError(401,'Faça login para acessar o armazenamento local.')
        return scope,self.store.single('SELECT email,username,role FROM users WHERE email=?',(scope,))

    def login(self,path,payload):
        email=str(payload.get('email') or '').strip().lower()
        password=str(payload.get('password') or '')
        role='balconista' if path.endswith('login-balconista/') else 'admin'
        if not email or not password:
            raise ApiError(400,'Informe e-mail e senha.')
        try:
            response=self.remote(path,'POST',{'email':email,'password':password})
            returned_role=response.get('role','admin' if response.get('is_staff') else 'balconista')
            if returned_role != role:
                raise ApiError(403,'Perfil incompatível com este painel.')
            self.store.save_user(email,password,response.get('username',email),role,response['token'])
            online=True
        except OfflineConnection:
            cached=self.store.verify_user(email,password,role)
            if not cached:
                raise ApiError(401,'Sem internet: é necessário um primeiro login online neste computador com essas credenciais.')
            elapsed=datetime.now(timezone.utc)-datetime.fromisoformat(cached['last_online_login'])
            if elapsed>timedelta(days=self.offline_login_valid_days):
                raise ApiError(401,f'Login offline expirou após {self.offline_login_valid_days} dias. Conecte-se para validar sua conta no Django.')
            response={'username':cached['username'],'email':email,'role':role,'is_staff':role=='admin'}
            online=False
        except RemoteRejected as e:
            # Não aceitar credenciais antigas se o servidor estiver acessível e as rejeitar.
            raise ApiError(e.code,'Credenciais ou perfil inválidos no servidor.')
        local_token=secrets.token_urlsafe(40)
        self.sessions[local_token]=email
        if online:
            threading.Thread(target=self.refresh_scope,args=(email,),daemon=True).start()
        return {'token':local_token,'email':email,'username':response['username'],
                'role':role,'is_staff':role=='admin','modo':'online' if online else 'offline'}

    def status(self,scope):
        return {'online':self.is_online(),'pendentes':self.store.queue_count(scope,'pending'),
                'conflitos':self.store.queue_count(scope,'conflict'),
                'ultima_sincronizacao':self.store.meta(scope,'last_sync'),
                'ultimo_erro':self.store.meta(scope,'last_error',''),
                'banco_local':str(self.store.db_file)}

    def enforce(self,role,type_,method,action=''):
        if type_ in ADMIN_ONLY and role!='admin':
            raise ApiError(403,'Acesso administrativo necessário.')
        if method=='GET':return
        if role=='balconista':
            if type_ in READ_ONLY_BALCAO:
                raise ApiError(403,'O balcão só pode consultar este cadastro.')
            if type_ not in ('agendamentos','vendas'):
                raise ApiError(403,'Operação não autorizada para o balcão.')
            if type_=='vendas' and method in ('PATCH','PUT','DELETE'):
                raise ApiError(403,'Somente o administrador pode editar vendas.')

    def route(self,path,method='GET',payload=None,headers=None,uploaded=None):
        headers=headers or {}
        if path in ('/auth/login/','/auth/login-balconista/') and method=='POST':
            return self.login(path,payload or {})
        scope,user=self.identity(headers)
        role=user['role']
        if path=='/auth/me/' and method=='GET':
            return {'username':user['username'],'email':scope,'role':role,'is_staff':role=='admin'}
        if path=='/auth/logout/' and method=='POST':
            auth=headers.get('Authorization','').removeprefix('Token ').strip()
            self.sessions.pop(auth,None)
            return None
        if path=='/offline/status/' and method=='GET':return self.status(scope)
        if path=='/offline/queue/' and method=='GET':
            return [{'id':r['id'],'metodo':r['method'],'rota':r['path'],'status':r['status'],
                     'erro':r['error'],'criada_em':r['created_at']} for r in self.store.queue(scope)]
        if path=='/offline/sync/' and method=='POST':
            self.synchronize(scope)
            self.refresh_scope(scope)
            return self.status(scope)
        m=re.fullmatch(r'/offline/queue/(\d+)/retry/',path)
        if m and method=='POST':
            self.store.retry(int(m.group(1)),scope)
            return self.status(scope)
        if path.startswith('/financeiro/'):
            if role!='admin' and not path.startswith('/financeiro/status-periodo/'):
                raise ApiError(403,'Somente administrador.')
            return self.finance(scope,path,method,payload)
        if path.startswith('/public/'):
            # Disponibilidade pública offline não pode ser garantida.
            return self.passthrough(scope,path,method,payload)
        # {type}/{id}/ or {type}/{id}/estornar/ or {type}/{id}/imagem/
        m=re.fullmatch(r'/([\w-]+)/(?:([-\d]+)/)?(?:(estornar|imagem|foto)/)?',path)
        if not m or m.group(1) not in RESOURCES:
            raise ApiError(404,'Rota local desconhecida: '+path)
        kind,id_,action=m.groups()
        self.enforce(role,kind,method,action)
        if action in ('imagem','foto') and method=='POST':
            return self.image_upload(scope,kind,id_,path,uploaded)
        if method=='GET' and not id_:
            return self.get_collection(scope,kind,path)
        if method=='GET' and id_:
            record=self.store.get_record(scope,kind,id_)
            if record is None:raise ApiError(404,'Registro não encontrado no cache.')
            return record
        if method not in ('POST','PATCH','PUT','DELETE'):
            raise ApiError(405,'Operação não suportada.')
        return self.write(scope,kind,id_,action,method,path,payload or {})

    def passthrough(self,scope,path,method,payload):
        token=self.store.remote_token(scope)
        try:return self.remote(path,method,payload,token)
        except OfflineConnection:raise ApiError(503,'Esta consulta exige internet e não possui dados locais.')
        except RemoteRejected as e:raise ApiError(e.code,str(e))

    def fetch_collection(self,scope,kind):
        token=self.store.remote_token(scope)
        if not token:raise OfflineConnection('Sem token remoto válido. Entre online novamente.')
        items=[]
        for page in range(1,101):
            result=self.remote(f'/{kind}/?page={page}',token=token)
            if isinstance(result,list):items.extend(result);break
            if not isinstance(result,dict):break
            items.extend(result.get('results',[]))
            if not result.get('next'):break
        else:raise ApiError(409,'Limite de páginas da API atingido.')
        return self.cache_images(items)

    def get_collection(self,scope,kind,path):
        # Não substituir dados locais enquanto houver qualquer ação não resolvida.
        queue_open=self.store.queue_count(scope,'pending') or self.store.queue_count(scope,'conflict')
        if not queue_open and self.is_online():
            try:
                self.store.set_records(scope,kind,self.fetch_collection(scope,kind))
            except (OfflineConnection,RemoteRejected,ApiError) as error:
                self.store.set_meta(scope,'last_error',str(error))
        return self.store.list_records(scope,kind)

    def cache_images(self,items):
        for row in items:
            for key in ('imagem_exibicao','imagem_url','foto_exibicao','foto_url'):
                url=row.get(key)
                if not url or not str(url).startswith(('http','/media/')):continue
                cached=self.store.single('SELECT file_path FROM media_cache WHERE url=?',(url,))
                if cached and Path(cached['file_path']).is_file():
                    row[key]='/offline-media/'+Path(cached['file_path']).name
                    continue
                # Evita requisições muito longas e não baixa assets externos não confiáveis.
                final=urllib.parse.urljoin(self.remote_base+'/',url)
                allowed_host=urllib.parse.urlparse(self.remote_base).netloc
                if urllib.parse.urlparse(final).netloc!=allowed_host:continue
                try:
                    with urllib.request.urlopen(final,timeout=1.5) as response:
                        if int(response.headers.get('Content-Length','0'))>5_000_000:continue
                        data=response.read(5_000_001)
                        if len(data)>5_000_000:continue
                        ext=Path(urllib.parse.urlparse(final).path).suffix.lower()
                        if ext not in ('.png','.jpg','.jpeg','.webp'):ext='.jpg'
                        filename=hashlib.sha256(final.encode()).hexdigest()+ext
                        local=self.store.media / filename
                        local.write_bytes(data)
                        self.store.execute('INSERT OR REPLACE INTO media_cache(url,file_path) VALUES(?,?)',(url,str(local)))
                        row[key]='/offline-media/'+filename
                except Exception:pass
        return items

    def local_finance_summary(self,scope,month):
        """Resumo PROVISÓRIO calculado dos registros SQLite.

        Não é um fechamento contábil: só o Django confirma a apuração.
        """
        sales=[s for s in self.store.list_records(scope,'vendas')
               if str(s.get('data','')).startswith(month) and not s.get('estornada')]
        receipts=[s for s in self.store.list_records(scope,'recebimentos-servicos')
                  if str(s.get('data','')).startswith(month)]
        expenses=[s for s in self.store.list_records(scope,'despesas')
                  if str(s.get('data','')).startswith(month)]
        prod=sum((quant(s.get('valor_total',0)) for s in sales),Decimal('0'))
        service=sum((quant(s.get('valor',0)) for s in receipts),Decimal('0'))
        costs=sum((quant(s.get('custo_total',0)) for s in sales),Decimal('0'))
        extra=sum((quant(s.get('valor',0)) for s in expenses),Decimal('0'))
        comm_products=sum((quant(s.get('comissao',0)) for s in sales),Decimal('0'))
        comm_services=sum((quant(s.get('comissao',0)) for s in receipts),Decimal('0'))
        old=self.store.get_snapshot(scope,'/financeiro/resumo/?mes='+month)
        fechado=(old[0].get('fechado',False) if old else False)
        repasses=[]
        for barber in self.store.list_records(scope,'barbeiros'):
            b=barber['id']
            sp=sum((quant(r.get('comissao',0)) for r in receipts if r.get('barbeiro')==b),Decimal('0'))
            pp=sum((quant(r.get('comissao',0)) for r in sales if r.get('barbeiro')==b),Decimal('0'))
            if sp or pp:
                repasses.append({'barbeiro_id':b,'barbeiro':barber.get('nome',''),
                                 'servicos':str(sp),'produtos':str(pp),'total':str(sp+pp)})
        return {'mes':month,'total_servicos':str(service),'total_produtos':str(prod),
                'receita_bruta':str(service+prod),'custo_produtos':str(costs),
                'despesas':str(extra),'comissoes_servicos':str(comm_services),
                'comissoes_produtos':str(comm_products),
                'comissoes':str(comm_products+comm_services),
                'saldo_proprietario':str(service+prod-costs-extra-comm_products-comm_services),
                'repasses':repasses,'fechado':fechado,'provisorio':True}

    def finance(self,scope,path,method,payload):
        u=urllib.parse.urlsplit(path)
        month=urllib.parse.parse_qs(u.query).get('mes',[date.today().strftime('%Y-%m')])[0]
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',month):
            raise ApiError(400,'Mês inválido.')
        key=u.path+('?mes='+month if ('resumo' in u.path or 'status-periodo' in u.path or 'excel' in u.path) else '')
        if method!='GET':
            # Fechamentos só online: operação com risco financeiro irreversível.
            if not self.is_online():raise ApiError(409,'Fechamento financeiro exige conexão com o servidor.')
            try:
                result=self.remote(path,method,payload,self.store.remote_token(scope))
                self.store.snapshot(scope,key,result)
                return result
            except OfflineConnection:raise ApiError(503,'Sem conexão com servidor.')
            except RemoteRejected as e:raise ApiError(e.code,str(e))
        # Mostrar lançamentos locais imediatamente durante modo offline,
        # sem confundir estimativa com o valor consolidado pelo PostgreSQL.
        if u.path.endswith('/resumo/') and (
            not self.is_online() or self.store.queue_count(scope,'pending')
            or self.store.queue_count(scope,'conflict')
        ):
            return self.local_finance_summary(scope,month)
        if self.is_online():
            try:
                result=self.remote(path,token=self.store.remote_token(scope),accept='*/*' if 'excel' in u.path else 'application/json')
                if isinstance(result,bytes):
                    filename='excel-'+month+'.xlsx'
                    target=self.store.folder/('relatorio-'+hashlib.sha256(scope.encode()).hexdigest()[:12]+'-'+filename)
                    target.write_bytes(result)
                    self.store.snapshot(scope,key,{'arquivo':str(target)})
                else:self.store.snapshot(scope,key,result)
                return result
            except (OfflineConnection,RemoteRejected):pass
        result=self.store.get_snapshot(scope,key)
        if not result and u.path.endswith('/status-periodo/'):
            backup=self.store.get_snapshot(scope,'/financeiro/resumo/?mes='+month)
            if backup:
                return {'mes':month,'fechado':backup[0].get('fechado',False),'provisorio':True}
        if result:
            if isinstance(result[0],dict) and 'arquivo' in result[0]:
                p=Path(result[0]['arquivo'])
                if p.is_file():return p.read_bytes()
            return result[0]
        raise ApiError(503,'Sem cópia local deste relatório. Consulte online ao menos uma vez.')

    def record_optimistic(self,scope,kind,id_,payload,method,action):
        # Não tenta simular 100% das regras financeiras/conflitos do Django.
        before=self.store.get_record(scope,kind,id_) if id_ else None
        if method=='DELETE':
            if not before:raise ApiError(404,'Registro não encontrado.')
            self.store.del_record(scope,kind,id_)
            return None
        row=dict(before or {})
        if not id_:
            raise ValueError('Local ID requerido para simulação de criação.')
        row['id']=int(id_) if str(id_).lstrip('-').isdigit() else id_
        row.update(payload)
        if kind=='produtos':
            if float(row.get('preco',0))<0 or int(row.get('estoque',0))<0:
                raise ApiError(400,'Preço ou estoque inválido.')
            row.setdefault('imagem_exibicao', row.get('imagem_url',''))
        elif kind=='barbeiros':
            row.setdefault('horarios',[])
            row.setdefault('foto_exibicao',row.get('foto_url',''))
        elif kind=='agendamentos':
            if not row.get('data') or not row.get('hora'):
                raise ApiError(400,'Informe data e hora.')
            if row.get('cliente_nome'):
                row['nome_cliente']=row['cliente_nome']
                row['telefone_cliente']=row.get('cliente_telefone','')
            elif row.get('cliente'):
                cliente=self.store.get_record(scope,'clientes',row['cliente'])
                row['nome_cliente']=(cliente or {}).get('nome','Cliente')
            if row.get('pago') and row.get('status')!='concluido':
                raise ApiError(400,'Pagamento só em atendimento concluído.')
            row.setdefault('pago',False)
            servico=self.store.get_record(scope,'servicos',row.get('servico'))
            row.setdefault('valor_cobrado',str(quant((servico or {}).get('preco',0))))
            row.setdefault('observacao','')
            # Corte concluído offline: espelhar um recebimento PROVISÓRIO;
            # o Django criará o lançamento oficial quando aceitar o PATCH.
            if row.get('status')=='concluido' and row.get('pago') and not (before or {}).get('pago'):
                valor=quant(row.get('valor_cobrado',0))
                barbeiro=self.store.get_record(scope,'barbeiros',row.get('barbeiro'))
                percentual=quant((barbeiro or {}).get('comissao_servico',0))
                recebimento={
                    'id':-int(time.time()*1000000),
                    'agendamento':row['id'],'barbeiro':row.get('barbeiro'),
                    'data':date.today().isoformat(),'valor':str(valor),
                    'comissao':str(quant(valor*percentual/100)),
                    'provisorio':True,
                }
                self.store.put_record(scope,'recebimentos-servicos',recebimento)
        elif kind=='vendas':
            if action=='estornar':
                if not before or before.get('estornada'):
                    raise ApiError(409,'Venda não encontrada ou já estornada.')
                row['estornada']=True
                produto=self.store.get_record(scope,'produtos',row['produto'])
                if produto:
                    produto['estoque']=int(produto.get('estoque',0))+int(row['quantidade'])
                    self.store.put_record(scope,'produtos',produto)
            else:
                product=self.store.get_record(scope,'produtos',row.get('produto'))
                if not product:raise ApiError(400,'Produto indisponível no cache local.')
                qty=int(row.get('quantidade',0))
                if qty<1:raise ApiError(400,'Quantidade deve ser maior que zero.')
                old_qty=int(before.get('quantidade',0)) if before and before.get('produto')==row.get('produto') else 0
                if int(product.get('estoque',0))+old_qty<qty:
                    raise ApiError(409,'Estoque local insuficiente.')
                if before and before.get('produto')!=row.get('produto'):
                    previous=self.store.get_record(scope,'produtos',before.get('produto'))
                    if previous:
                        previous['estoque']=int(previous.get('estoque',0))+int(before.get('quantidade',0))
                        self.store.put_record(scope,'produtos',previous)
                product['estoque']=int(product.get('estoque',0))+old_qty-qty
                self.store.put_record(scope,'produtos',product)
                # Totais locais são estimativas; servidor recalcula ao sincronizar.
                price=quant(product.get('preco',0))
                row['produto_nome']=product.get('nome','')
                row['valor_total']=str(price*qty)
                row['custo_total']=str(quant(product.get('custo',0))*qty)
                barber=self.store.get_record(scope,'barbeiros',row.get('barbeiro')) if row.get('barbeiro') else None
                row['barbeiro_nome']=(barber or {}).get('nome','Administração')
                commission=quant((price*qty)*Decimal(str((barber or {}).get('comissao_produto',0)))/100)
                row['comissao']=str(commission)
                row.setdefault('estornada',False)
        self.store.put_record(scope,kind,row)
        return row

    def write(self,scope,kind,id_,action,method,path,payload):
        role=self.store.single('SELECT role FROM users WHERE email=?',(scope,))['role']
        if kind=='vendas' and action=='estornar' and method!='POST':
            raise ApiError(405,'Estorno exige POST.')
        if kind=='vendas' and action!='estornar' and method=='DELETE':
            raise ApiError(405,'Não se apagam vendas; use o estorno.')
        if kind=='vendas' and method=='POST' and 'quantidade' not in payload:
            raise ApiError(400,'Quantidade obrigatória.')
        if method=='POST' and id_ is None:
            local_id=None
        elif not id_:
            raise ApiError(400,'ID requerido.')
        else:local_id=id_
        # Primeiro, operar no Django quando houver conexão (não criar fila desnecessária).
        remote_token=self.store.remote_token(scope)
        if self.is_online() and remote_token and not self.store.queue_count(scope,'pending') and not self.store.queue_count(scope,'conflict'):
            try:
                result=self.remote(path,method,payload,remote_token)
                if method=='DELETE':self.store.del_record(scope,kind,id_)
                elif action=='estornar':
                    current=self.store.get_record(scope,kind,id_)
                    if current:
                        current['estornada']=True
                        self.store.put_record(scope,kind,current)
                    # Produto precisa ser recarregado do Django.
                elif isinstance(result,dict) and 'id' in result:
                    self.store.put_record(scope,kind,self.cache_images([result])[0])
                # Atualizar lista ao receber mudanças do backend.
                threading.Thread(target=self.refresh_scope,args=(scope,),daemon=True).start()
                return result
            except RemoteRejected as e:raise ApiError(e.code,str(e))
            except OfflineConnection:
                # A chamada pode ter chegado ao Django e a resposta se perdido.
                # Não reenviar automaticamente: poderia duplicar uma venda.
                raise ApiError(409,
                    'Conexão caiu durante a operação. Confira no servidor se foi salva antes de repetir.')
        # Não aceitar operações em períodos que o último status confirmou fechados.
        if kind in ('vendas','agendamentos','despesas'):
            record_before=self.store.get_record(scope,kind,id_) if id_ else None
            data_lancamento=payload.get('data') or (record_before or {}).get('data')
            if data_lancamento:
                mes=str(data_lancamento)[:7]
                old=self.store.get_snapshot(scope,f'/financeiro/status-periodo/?mes={mes}')
                if not old:
                    old=self.store.get_snapshot(scope,f'/financeiro/resumo/?mes={mes}')
                if old and old[0].get('fechado'):
                    raise ApiError(409,'O período está fechado segundo o último estado conhecido.')
        # Offline, ou já existem operações aguardando envio.
        if method=='POST' and id_ is None:
            queue_id=self.store.enqueue(scope,method,path,payload)
            local_id='-'+str(queue_id)
        else:
            if not self.store.get_record(scope,kind,id_):
                raise ApiError(404,'Registro não existe no cache local.')
            queue_id=self.store.enqueue(scope,method,path,payload)
        try:
            result=self.record_optimistic(scope,kind,local_id,payload,method,action)
        except Exception:
            self.store.execute('DELETE FROM outbox WHERE id=?',(queue_id,))
            raise
        if result is None:return None
        return result

    def image_upload(self,scope,kind,id_,path,uploaded):
        if kind not in ('barbeiros','produtos') or not uploaded:
            raise ApiError(400,'Envio inválido.')
        data,filename=uploaded
        if len(data)>5_000_000:raise ApiError(413,'Imagem acima de 5 MB.')
        ext=Path(filename).suffix.lower()
        if ext not in ('.jpg','.jpeg','.png','.webp'):
            raise ApiError(400,'Somente JPG, PNG e WEBP.')
        record=self.store.get_record(scope,kind,id_)
        if not record:raise ApiError(404,'Registro não encontrado.')
        name=secrets.token_hex(12)+ext
        local=self.store.media/name
        local.write_bytes(data)
        field='imagem_exibicao' if kind=='produtos' else 'foto_exibicao'
        record[field]='/offline-media/'+name
        self.store.put_record(scope,kind,record)
        self.store.enqueue(scope,'POST',path,{},str(local))
        return record

    def replace_ids(self,scope,kind,path,payload):
        m=re.match(r'^/([\w-]+)/(-\d+)/(.*)$',path)
        if m:
            mapped=self.store.get_map(scope,m.group(1),m.group(2))
            if not mapped:
                raise OfflineConnection(f'Aguardando ID remoto para {path}')
            path=f'/{m.group(1)}/{mapped}/{m.group(3)}'
        data=dict(payload or {})
        for field,type_ in FOREIGN.items():
            if field in data and isinstance(data[field],int) and data[field]<0:
                mapped=self.store.get_map(scope,type_,data[field])
                if not mapped:raise OfflineConnection(f'Aguardando ID remoto para {field}={data[field]}')
                data[field]=int(mapped)
        return path,data

    def synchronize(self,only_scope=None):
        if not self.sync_lock.acquire(blocking=False):return
        try:
            if not self.is_online(force=True):return
            rows=self.store.pending(only_scope)
            touched=set()
            blocked=set()
            for op in rows:
                scope=op['scope']
                if scope in blocked or self.store.queue_count(scope,'conflict'):
                    # Enquanto existir conflito, preservar a ordem original do usuário.
                    blocked.add(scope)
                    continue
                token=self.store.remote_token(scope)
                if not token:
                    self.store.set_meta(scope,'last_error','Entre online novamente para renovar o token de sincronização.')
                    continue
                payload=json.loads(op['payload']) if op['payload'] else None
                started=False
                try:
                    path,data=self.replace_ids(scope,None,op['path'],payload)
                    self.store.mark_sending(op['id'])
                    started=True
                    result=self.remote(path,op['method'],data,token,file_path=op['file_path'])
                    kind=path.split('/')[1]
                    if op['method']=='POST' and not op['file_path'] and re.fullmatch(r'/[\w-]+/',op['path']) and isinstance(result,dict) and 'id' in result:
                        self.store.set_map(scope,kind,'-'+str(op['id']),result['id'])
                        self.store.del_record(scope,kind,'-'+str(op['id']))
                        self.store.put_record(scope,kind,result)
                    self.store.finish(op['id'])
                    self.store.set_meta(scope,'last_error','')
                    touched.add(scope)
                except RemoteRejected as e:
                    if e.code==401:
                        self.store.mark_pending(op['id'])
                        self.store.set_meta(scope,'last_error','Token remoto expirado. Faça login novamente online.')
                        blocked.add(scope)
                        continue
                    self.store.conflict(op['id'],f'HTTP {e.code}: {e}')
                    self.store.set_meta(scope,'last_error',f'Conflito na ação #{op["id"]}: {e}')
                    # Não enviar operações seguintes deste usuário fora de ordem.
                    blocked.add(scope)
                    continue
                except OfflineConnection as e:
                    if started:
                        self.store.conflict(op['id'],
                            'Resultado incerto: a operação pode ter chegado ao servidor. '
                            'Confirme no painel online antes de tentar novamente.')
                    self.store.set_meta(scope,'last_error',str(e))
                    blocked.add(scope)
                    continue
            for scope in touched:
                self.store.set_meta(scope,'last_sync',now_iso())
        finally:
            self.sync_lock.release()

    def refresh_scope(self,scope):
        if not self.is_online():return
        # Ações pendentes/conflituosas nunca podem ser sobrescritas com refresh remoto.
        if self.store.queue_count(scope,'pending') or self.store.queue_count(scope,'conflict'):return
        user=self.store.single('SELECT role FROM users WHERE email=?',(scope,))
        if not user:return
        token=self.store.remote_token(scope)
        if not token:return
        try:
            remote_user=self.remote('/auth/me/',token=token)
            expected_staff=user['role']=='admin'
            if bool(remote_user.get('is_staff')) != expected_staff:
                self.store.set_meta(scope,'last_error','Perfil no servidor mudou. Faça login online novamente.')
                return
        except (OfflineConnection,RemoteRejected) as e:
            self.store.set_meta(scope,'last_error','Não foi possível revalidar a sessão no Django: '+str(e))
            return
        kinds=['barbeiros','produtos','servicos','clientes','agendamentos','vendas']
        if user['role']=='admin':
            kinds.extend(['despesas','recebimentos-servicos','folgas'])
        for kind in kinds:
            try:self.store.set_records(scope,kind,self.fetch_collection(scope,kind))
            except (OfflineConnection,RemoteRejected,ApiError) as e:
                self.store.set_meta(scope,'last_error',str(e))
                return
        # Pré-carregar fechamento do mês vigente e anterior, para ambos os perfis.
        today=date.today()
        prev_year=today.year if today.month>1 else today.year-1
        prev_month=today.month-1 or 12
        for month in (today.strftime('%Y-%m'),f'{prev_year:04d}-{prev_month:02d}'):
            route='/financeiro/resumo/' if user['role']=='admin' else '/financeiro/status-periodo/'
            key=route+'?mes='+month
            try:self.store.snapshot(scope,key,self.remote(key,token=self.store.remote_token(scope)))
            except (OfflineConnection,RemoteRejected):pass
        self.store.set_meta(scope,'last_sync',now_iso())

    def background(self,interval=30):
        while not self.stop_event.wait(interval):
            self.synchronize()
            for u in self.store.query('SELECT email FROM users'):
                self.refresh_scope(u['email'])
