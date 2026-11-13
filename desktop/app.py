"""Launcher Windows/Linux: WebView embutida + servidor local + SQLite.

Comandos:
  python -m desktop.app --panel admin
  python -m desktop.app --panel barbearia
  python -m desktop.app --panel both
  python -m desktop.app --serve --panel admin  # teste no navegador
"""
from __future__ import annotations

import argparse
import email.parser
from email import policy
import json
import mimetypes
import os
import re
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .engine import Engine, ApiError, OfflineConnection
from .store import Store, app_data_dir


def base_dir():
    # Quando empacotado, o PyInstaller extrai os arquivos em sys._MEIPASS.
    return Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))


def frontend_dist():
    return base_dir() / 'frontend' / 'dist'


def load_config():
    path=app_data_dir() / 'config.json'
    if not path.exists():
        bundled=base_dir()/'desktop'/'config.example.json'
        default=json.loads(bundled.read_text('utf-8'))
        path.write_text(json.dumps(default,indent=2,ensure_ascii=False),encoding='utf-8')
    config=json.loads(path.read_text('utf-8'))
    remote=config.get('api_url','').strip().rstrip('/')
    if not remote or 'SEU-DOMINIO' in remote.upper() or 'seu-dominio' in remote.lower():
        # Janela de configuração única. Não altera a interface React dos painéis.
        try:
            import tkinter as tk
            from tkinter import simpledialog
            root=tk.Tk()
            root.withdraw()
            entered=simpledialog.askstring('Brenner — configuração inicial',
                f'Informe a URL HTTPS da API Django (terminando em /api):\n\nConfiguração: {path}',
                initialvalue='https://', parent=root)
            root.destroy()
            if entered:
                remote=entered.strip().rstrip('/')
                path.write_text(json.dumps({'api_url':remote},ensure_ascii=False,indent=2),encoding='utf-8')
            else:
                raise RuntimeError(f'Preencha api_url no arquivo: {path}')
        except Exception as exc:
            # Em terminal sem ambiente gráfico, edite manualmente config.json.
            if isinstance(exc,RuntimeError): raise
            raise RuntimeError(f'Preencha api_url no arquivo: {path}') from exc
    if remote.startswith('http://') and not (
        '127.0.0.1' in remote or 'localhost' in remote or os.getenv('BRENNER_ALLOW_HTTP')=='1'
    ):
        raise RuntimeError('Em produção use HTTPS na api_url.')
    return remote


class Handler(BaseHTTPRequestHandler):
    server_version='BrennerDesktop/0.1'
    def log_message(self,fmt,*args):
        if os.getenv('BRENNER_HTTP_DEBUG')=='1':super().log_message(fmt,*args)

    def fail(self,status,message):
        self.send_json({'detail':str(message)},status)

    def send_bytes(self,data,content_type,status=200):
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store' if content_type.startswith('application/json') else 'public, max-age=300')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers()
        if self.command!='HEAD':self.wfile.write(data)

    def send_json(self,obj,status=200):
        if obj is None and status==200:status=204
        self.send_bytes(b'' if status==204 else json.dumps(obj,ensure_ascii=False,default=str).encode('utf-8'),'application/json; charset=utf-8',status)

    def cors_guard(self):
        host=self.headers.get('Host','')
        if host not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
            raise ApiError(403,'Host inválido.')
        origin=self.headers.get('Origin')
        if origin and origin not in (f'http://{host}',):
            raise ApiError(403,'Origem não autorizada.')

    def body(self):
        size=int(self.headers.get('Content-Length','0'))
        if size>7_000_000:raise ApiError(413,'Requisição muito grande.')
        raw=self.rfile.read(size)
        content_type=self.headers.get('Content-Type','')
        if content_type.startswith('multipart/form-data'):
            envelope=(f'Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n').encode()+raw
            message=email.parser.BytesParser(policy=policy.default).parsebytes(envelope)
            for part in message.iter_parts():
                if part.get_param('name',header='content-disposition')=='arquivo':
                    name=Path(part.get_filename() or 'foto.jpg').name
                    return None,(part.get_payload(decode=True) or b'',name)
            raise ApiError(400,'Arquivo não recebido.')
        if raw:
            try:return json.loads(raw),None
            except ValueError:raise ApiError(400,'JSON inválido.')
        return None,None

    def do_GET(self):self.dispatch()
    def do_POST(self):self.dispatch()
    def do_PATCH(self):self.dispatch()
    def do_PUT(self):self.dispatch()
    def do_DELETE(self):self.dispatch()
    def do_HEAD(self):self.dispatch()

    def dispatch(self):
        try:
            self.cors_guard()
            parsed=urllib.parse.urlsplit(self.path)
            path=urllib.parse.unquote(parsed.path)
            if path=='/desktop/health':
                return self.send_json({'status':'ok'})
            if path.startswith('/api/'):
                if self.command=='HEAD':raise ApiError(405,'Método não suportado.')
                data,uploaded=self.body() if self.command!='GET' else (None,None)
                full=path[4:]+('?'+parsed.query if parsed.query and path.startswith('/api/financeiro/') else '')
                result=self.server.engine.route(full,self.command,data,self.headers,uploaded)
                if isinstance(result,bytes):
                    return self.send_bytes(result,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                return self.send_json(result)
            if path.startswith('/offline-media/'):
                name=path.split('/')[-1]
                if not re.fullmatch(r'[\da-f]{24,64}\.(?:png|jpg|jpeg|webp)',name):
                    raise ApiError(404,'Imagem inválida.')
                target=self.server.engine.store.media/name
                if not target.is_file():raise ApiError(404,'Imagem não encontrada.')
                return self.send_bytes(target.read_bytes(),mimetypes.guess_type(name)[0] or 'image/jpeg')
            if self.command not in ('GET','HEAD'):
                raise ApiError(405,'Método não permitido.')
            dist=self.server.dist
            if path in ('/selecionar','/selecionar/'):
                target=base_dir()/'desktop'/'selecionar.html'
            elif path in ('/admin','/admin/'):
                target=dist/'admin'/'index.html'
            elif path in ('/barbearia','/barbearia/'):
                target=dist/'barbearia'/'index.html'
            elif path=='/':
                target=dist/'index.html'
            else:
                relative=path.lstrip('/')
                target=(dist/relative).resolve()
                if not str(target).startswith(str(dist.resolve())+os.sep):
                    raise ApiError(403,'Caminho inválido.')
                if target.is_dir():target=target/'index.html'
            if not target.is_file():raise ApiError(404,'Recurso não encontrado: '+path)
            return self.send_bytes(target.read_bytes(),mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        except ApiError as e:
            self.fail(e.code,str(e))
        except OfflineConnection as e:
            self.fail(503,str(e))
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception as e:
            if os.getenv('BRENNER_HTTP_DEBUG')=='1':
                import traceback;traceback.print_exc()
            self.fail(500,'Erro interno no aplicativo local.')


def start_server(remote,port=0,folder=None,dist=None,background=True,offline_days=30):
    store=Store(folder)
    engine=Engine(remote,store,offline_login_valid_days=offline_days)
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.engine=engine
    server.dist=dist or frontend_dist()
    thread=threading.Thread(target=server.serve_forever,name='BrennerLocalHTTP',daemon=True)
    if background:thread.start()
    return server,engine,thread


def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('--panel',choices=('selecionar','admin','barbearia','both'),default='selecionar')
    parser.add_argument('--serve',action='store_true',help='Testar no navegador sem janela WebView')
    parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--api',help='URL local de testes; use config.json em produção')
    args=parser.parse_args()
    remote=args.api or load_config()
    dist=frontend_dist()
    if not (dist/'admin'/'index.html').is_file() or not (dist/'barbearia'/'index.html').is_file():
        raise RuntimeError('Frontend não compilado. Execute npm ci e npm run build:desktop em frontend/.')
    config_path=app_data_dir()/'config.json'
    config=json.loads(config_path.read_text('utf-8')) if config_path.exists() else {}
    days=int(config.get('offline_login_valid_days',30))
    if days<1 or days>365:
        raise RuntimeError('offline_login_valid_days deve estar entre 1 e 365.')
    server,engine,thread=start_server(remote,args.port,offline_days=days)
    base=f'http://127.0.0.1:{server.server_port}'
    print('Banco SQLite:',engine.store.db_file)
    print('URL:',base)
    background=threading.Thread(target=engine.background,daemon=True)
    background.start()
    try:
        if args.serve:
            print('Teste no navegador:',base+'/admin/','e',base+'/barbearia/')
            try:thread.join()
            except KeyboardInterrupt:pass
        else:
            try:import webview
            except ImportError as e:
                raise RuntimeError('Instale o componente de janela: pip install pywebview') from e
            windows=[]
            if args.panel=='selecionar':
                # windows.append(webview.create_window('Barbearia Brenner — Desktop',base+'/selecionar',width=1100,height=790,min_size=(800,640)))
                windows.append(
                    webview.create_window(
                        'Barbearia Brenner | Sistema de Gestão',
                        base + '/selecionar',
                        width=1100,
                        height=790,
                        min_size=(800, 640)
                    )
                )
            if args.panel in ('admin','both'):
                windows.append(webview.create_window('Brenner — Administração',base+'/admin/',width=1360,height=850,min_size=(940,650)))
            if args.panel in ('barbearia','both'):
                windows.append(webview.create_window('Brenner — Balcão',base+'/barbearia/',width=1240,height=790,min_size=(880,610)))
            # webview.start(debug=os.getenv('BRENNER_DEBUG')=='1',private_mode=False,storage_path=str(engine.store.folder/'webview'))
            #icon_path = base_dir() / 'desktop' / 'assets' / 'brenner.ico'

            # webview.start(
            #     debug=os.getenv('BRENNER_DEBUG') == '1',
            #     private_mode=False,
            #     storage_path=str(engine.store.folder / 'webview'),
            #     icon=str(icon_path)
            # )
                        # Ícone oficial da Barbearia Brenner
            icon_path = base_dir() / 'desktop' / 'assets' / 'brenner.ico'

            if not icon_path.is_file():
                raise FileNotFoundError(
                    f'Ícone da Barbearia Brenner não encontrado: {icon_path}'
                )

            # Iniciar a interface desktop
            webview.start(
                debug=os.getenv('BRENNER_DEBUG') == '1',
                private_mode=False,
                storage_path=str(engine.store.folder / 'webview'),
                icon=str(icon_path)
            )
    finally:
        engine.stop_event.set()
        server.shutdown()
        server.server_close()


if __name__=='__main__':run()
