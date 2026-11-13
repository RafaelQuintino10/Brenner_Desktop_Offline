"""Teste do servidor HTTP local e da resolução de /admin e /barbearia."""
import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from desktop.app import start_server
from tests.test_offline import MockDjango
from http.server import ThreadingHTTPServer
from threading import Thread


class HttpTests(unittest.TestCase):
    def test_routes_auth_and_local_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            for label in ('admin','barbearia'):
                folder=base/'dist'/label
                folder.mkdir(parents=True)
                (folder/'index.html').write_text(f'<title>{label}</title>')
            (base/'dist'/'index.html').write_text('<title>Landing</title>')
            django=ThreadingHTTPServer(('127.0.0.1',0),MockDjango)
            django.product={'id':1,'nome':'Pomada','preco':'50.00','estoque':10,'custo':'20.00'}
            django.sales=[]
            worker=Thread(target=django.serve_forever,daemon=True)
            worker.start()
            app,engine,thread=start_server(f'http://127.0.0.1:{django.server_port}/api',folder=base/'data',dist=base/'dist')
            url=f'http://127.0.0.1:{app.server_port}'
            try:
                for name in ('admin','barbearia'):
                    with urllib.request.urlopen(url+'/'+name) as response:
                        self.assertIn(name,response.read().decode())
                request=urllib.request.Request(url+'/api/offline/status/')
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(request)
                self.assertEqual(ctx.exception.code,401)
                data=json.dumps({'email':'balcao@teste.com','password':'SenhaForte#2026'}).encode()
                login=urllib.request.Request(url+'/api/auth/login-balconista/',data=data,
                    headers={'Content-Type':'application/json'},method='POST')
                with urllib.request.urlopen(login) as response:
                    token=json.load(response)['token']
                req=urllib.request.Request(url+'/api/produtos/',headers={'Authorization':'Token '+token})
                with urllib.request.urlopen(req) as response:
                    self.assertEqual(json.load(response)[0]['nome'],'Pomada')
            finally:
                app.shutdown();app.server_close();django.shutdown();django.server_close()
                engine.store.db.close()


if __name__=='__main__':unittest.main()
