"""Testes da API desktop com um servidor Django simulado, sem PostgreSQL."""
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from desktop.engine import Engine, ApiError
from desktop.store import Store

PRODUCT={'id':1,'nome':'Pomada','preco':'50.00','custo':'20.00','estoque':10,
         'categoria':'Pomadas','estoque_minimo':2,'descricao':'','ativo':True,
         'imagem_exibicao':''}
BARBER={'id':2,'nome':'João','especialidade':'Corte','telefone':'',
        'comissao_servico':'40.00','comissao_produto':'10.00','ativo':True,
        'horarios':[],'foto_exibicao':''}


class MockDjango(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path=='/api/health/':return self.json({'ok':True})
        if self.path=='/api/auth/me/':return self.json({'username':'balcao','email':'balcao@teste.com','is_staff':False,'role':'balconista'})
        p=self.path.split('?')[0]
        if p=='/api/produtos/':return self.json([self.server.product.copy()])
        if p=='/api/barbeiros/':return self.json([BARBER.copy()])
        if p=='/api/vendas/':return self.json(self.server.sales.copy())
        if p=='/api/financeiro/status-periodo/':return self.json({'mes':'2026-11','fechado':False})
        if p=='/api/financeiro/resumo/':return self.json({'mes':'2026-11','receita_bruta':'0.00','fechado':False})
        return self.json([])
    def do_POST(self):
        data=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
        if self.path in ('/api/auth/login/','/api/auth/login-balconista/'):
            if data.get('password')!='SenhaForte#2026':return self.json({'detail':'Inválido'},400)
            staff=self.path=='/api/auth/login/'
            return self.json({'token':'valid-remote-token','username':('admin' if staff else 'balcao'),
                              'is_staff':staff,'role':('admin' if staff else 'balconista'),'email':data['email']})
        if self.path=='/api/vendas/':
            qty=data['quantidade']
            if self.server.product['estoque']<qty:return self.json({'detail':'Estoque insuficiente'},400)
            self.server.product['estoque']-=qty
            row={'id':len(self.server.sales)+100,'produto':data['produto'],'produto_nome':'Pomada',
                 'barbeiro':data.get('barbeiro'),'barbeiro_nome':'João' if data.get('barbeiro') else 'Administração',
                 'quantidade':qty,'data':data['data'],'valor_total':str(50*qty)+'.00',
                 'custo_total':str(20*qty)+'.00','comissao':str(5*qty)+'.00' if data.get('barbeiro') else '0.00',
                 'estornada':False}
            self.server.sales.append(row)
            return self.json(row,201)
        return self.json({'detail':'Rota POST não simulada.'},404)


class TestOffline(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)
        self.srv=ThreadingHTTPServer(('127.0.0.1',0),MockDjango)
        self.srv.product=PRODUCT.copy()
        self.srv.sales=[]
        self.thread=threading.Thread(target=self.srv.serve_forever,daemon=True)
        self.thread.start()
        self.engine=Engine(f'http://127.0.0.1:{self.srv.server_port}/api',Store(self.path),timeout=.4)
        self.email='balcao@teste.com'
        self.login=self.engine.route('/auth/login-balconista/','POST',{'email':self.email,'password':'SenhaForte#2026'})
        self.headers={'Authorization':'Token '+self.login['token']}
        self.engine.refresh_scope(self.email)

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.temp.cleanup()

    def offline(self):
        self.srv.shutdown();self.srv.server_close()
        self.engine.last_check=0

    def online_again(self):
        self.srv=ThreadingHTTPServer(('127.0.0.1',self.srv.server_port),MockDjango)
        self.srv.product=PRODUCT.copy()
        self.srv.sales=[]
        self.thread=threading.Thread(target=self.srv.serve_forever,daemon=True)
        self.thread.start()
        self.engine.last_check=0

    def test_first_login_caches_and_password_not_stored(self):
        self.assertEqual(self.login['role'],'balconista')
        self.assertEqual(len(self.engine.route('/produtos/',headers=self.headers)),1)
        row=self.engine.store.single('SELECT * FROM users WHERE email=?',(self.email,))
        self.assertNotIn('SenhaForte#2026',str(row))
        self.assertEqual(self.engine.status(self.email)['pendentes'],0)
        self.offline()
        second=self.engine.route('/auth/login-balconista/','POST',{'email':self.email,'password':'SenhaForte#2026'})
        self.assertEqual(second['modo'],'offline')
        with self.assertRaises(ApiError):
            self.engine.route('/auth/login-balconista/','POST',{'email':self.email,'password':'errada'})

    def test_offline_sale_and_sync(self):
        self.offline()
        payload={'produto':1,'barbeiro':2,'quantidade':2,'data':'2026-11-12'}
        record=self.engine.route('/vendas/','POST',payload,self.headers)
        self.assertLess(record['id'],0)
        self.assertEqual(self.engine.status(self.email)['pendentes'],1)
        self.assertEqual(self.engine.store.get_record(self.email,'produtos',1)['estoque'],8)
        self.online_again()
        self.engine.synchronize(self.email)
        self.engine.refresh_scope(self.email)
        status=self.engine.status(self.email)
        self.assertEqual(status['pendentes'],0)
        self.assertEqual(status['conflitos'],0)
        self.assertEqual(len(self.srv.sales),1)
        self.assertEqual(self.srv.sales[0]['barbeiro'],2)
        self.assertEqual(self.srv.product['estoque'],8)

    def test_conflict_no_silent_overwrite(self):
        self.offline()
        self.engine.route('/vendas/','POST',{'produto':1,'barbeiro':None,'quantidade':3,'data':'2026-11-12'},self.headers)
        self.online_again()
        self.srv.product['estoque']=0
        self.engine.synchronize(self.email)
        st=self.engine.status(self.email)
        self.assertEqual(st['conflitos'],1)
        self.assertEqual(len(self.srv.sales),0)
        self.assertTrue(self.engine.store.get_record(self.email,'vendas',-1))

    def test_balconista_cannot_modify_products_offline(self):
        self.offline()
        with self.assertRaises(ApiError) as caught:
            self.engine.route('/produtos/','POST',{'nome':'Teste'},self.headers)
        self.assertEqual(caught.exception.code,403)

    def test_reopen_db_preserves_cache(self):
        self.offline()
        reopened=Engine(self.engine.remote_base,Store(self.path),timeout=.4)
        local=reopened.route('/auth/login-balconista/','POST',{'email':self.email,'password':'SenhaForte#2026'})
        data=reopened.route('/produtos/',headers={'Authorization':'Token '+local['token']})
        self.assertEqual(data[0]['nome'],'Pomada')


if __name__=='__main__':unittest.main()
