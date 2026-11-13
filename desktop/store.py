"""Persistência SQLite da versão desktop, sem alterar o PostgreSQL do servidor."""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def app_data_dir():
    if os.getenv('BRENNER_DATA_DIR'):
        root = Path(os.environ['BRENNER_DATA_DIR'])
    elif sys.platform == 'win32':
        root = Path(os.getenv('LOCALAPPDATA') or Path.home()) / 'BrennerDesktop'
    else:
        root = Path.home() / '.local' / 'share' / 'BrennerDesktop'
    root.mkdir(parents=True, exist_ok=True)
    return root


def windows_encrypt(data: bytes) -> str:
    """Protege o token remoto com DPAPI, vinculado ao usuário Windows."""
    if sys.platform != 'win32':
        return ''
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]
    source = ctypes.create_string_buffer(data)
    input_blob = Blob(len(data), ctypes.cast(source, ctypes.POINTER(ctypes.c_byte)))
    output_blob = Blob()
    ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    ctypes.windll.kernel32.LocalFree.restype = ctypes.c_void_p
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(input_blob), None, None, None, None, 0,
        ctypes.byref(output_blob)
    )
    if not ok:
        raise OSError('Não foi possível proteger o token com DPAPI.')
    try:
        return base64.b64encode(ctypes.string_at(output_blob.pbData, output_blob.cbData)).decode()
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))


def windows_decrypt(value: str) -> bytes:
    if sys.platform != 'win32' or not value:
        return b''
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]
    raw = base64.b64decode(value)
    source = ctypes.create_string_buffer(raw)
    input_blob = Blob(len(raw), ctypes.cast(source, ctypes.POINTER(ctypes.c_byte)))
    output_blob = Blob()
    ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    ctypes.windll.kernel32.LocalFree.restype = ctypes.c_void_p
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(input_blob), None, None, None, None, 0,
        ctypes.byref(output_blob)
    )
    if not ok:
        raise OSError('Não foi possível recuperar o token protegido.')
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))


class Store:
    def __init__(self, folder: Path | None = None):
        self.folder = folder or app_data_dir()
        self.folder.mkdir(parents=True, exist_ok=True)
        self.db_file = self.folder / 'brenner_offline.sqlite3'
        self.media = self.folder / 'imagens'
        self.media.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.db_file, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
          email TEXT PRIMARY KEY, username TEXT NOT NULL, role TEXT NOT NULL,
          salt TEXT NOT NULL, password_hash TEXT NOT NULL, remote_token TEXT,
          last_online_login TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS records (
          scope TEXT NOT NULL, type TEXT NOT NULL, id TEXT NOT NULL,
          body TEXT NOT NULL, updated_at TEXT NOT NULL,
          PRIMARY KEY(scope,type,id)
        );
        CREATE TABLE IF NOT EXISTS outbox (
          id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL,
          method TEXT NOT NULL, path TEXT NOT NULL, payload TEXT,
          file_path TEXT, status TEXT NOT NULL DEFAULT 'pending',
          error TEXT, created_at TEXT NOT NULL, sent_at TEXT
        );
        CREATE TABLE IF NOT EXISTS id_map (
          scope TEXT NOT NULL, type TEXT NOT NULL,
          local_id TEXT NOT NULL, remote_id TEXT NOT NULL,
          PRIMARY KEY(scope,type,local_id)
        );
        CREATE TABLE IF NOT EXISTS snapshots (
          scope TEXT NOT NULL, key TEXT NOT NULL, body BLOB NOT NULL,
          updated_at TEXT NOT NULL, PRIMARY KEY(scope,key)
        );
        CREATE TABLE IF NOT EXISTS metadata (
          scope TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
          PRIMARY KEY(scope,key)
        );
        CREATE TABLE IF NOT EXISTS media_cache (
          url TEXT PRIMARY KEY, file_path TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS outbox_scope_status ON outbox(scope,status,id);
        ''')
        self.db.commit()
        # Never persist the upstream token unencrypted on non-Windows systems.
        self.ephemeral_remote_tokens = {}

    def execute(self, sql, args=()):
        with self.lock:
            cur = self.db.execute(sql, args)
            self.db.commit()
            return cur

    def query(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def single(self, sql, args=()):
        with self.lock:
            row = self.db.execute(sql, args).fetchone()
            return dict(row) if row else None

    def save_user(self, email, password, username, role, remote_token):
        email = email.strip().lower()
        salt = secrets.token_bytes(24)
        verifier = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 600000)
        secret = windows_encrypt(remote_token.encode('utf-8'))
        self.ephemeral_remote_tokens[email] = remote_token
        self.execute('''INSERT INTO users(email,username,role,salt,password_hash,remote_token,last_online_login)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET
          username=excluded.username,role=excluded.role,salt=excluded.salt,
          password_hash=excluded.password_hash,remote_token=excluded.remote_token,
          last_online_login=excluded.last_online_login''',
          (email,username,role,salt.hex(),verifier.hex(),secret,now_iso()))

    def verify_user(self, email, password, role):
        user = self.single('SELECT * FROM users WHERE email=?', (email.strip().lower(),))
        if not user or user['role'] != role:
            return None
        computed = hashlib.pbkdf2_hmac(
            'sha256',password.encode('utf-8'),bytes.fromhex(user['salt']),600000
        )
        return user if secrets.compare_digest(computed, bytes.fromhex(user['password_hash'])) else None

    def remote_token(self, email):
        email = email.lower()
        if email in self.ephemeral_remote_tokens:
            return self.ephemeral_remote_tokens[email]
        user = self.single('SELECT remote_token FROM users WHERE email=?',(email,))
        try:
            return windows_decrypt(user['remote_token']).decode('utf-8') if user else ''
        except OSError:
            return ''

    def set_records(self, scope, type_, records):
        with self.lock:
            self.db.execute('DELETE FROM records WHERE scope=? AND type=?',(scope,type_))
            self.db.executemany('''INSERT INTO records(scope,type,id,body,updated_at)
            VALUES(?,?,?,?,?)''',[(scope,type_,str(record['id']),json.dumps(record,ensure_ascii=False),now_iso()) for record in records])
            self.db.commit()

    def put_record(self,scope,type_,record):
        self.execute('''INSERT INTO records(scope,type,id,body,updated_at) VALUES(?,?,?,?,?)
        ON CONFLICT(scope,type,id) DO UPDATE SET body=excluded.body,updated_at=excluded.updated_at''',
        (scope,type_,str(record['id']),json.dumps(record,ensure_ascii=False),now_iso()))

    def get_record(self,scope,type_,id_):
        item=self.single('SELECT body FROM records WHERE scope=? AND type=? AND id=?',(scope,type_,str(id_)))
        return json.loads(item['body']) if item else None

    def list_records(self,scope,type_):
        rows=self.query('SELECT body FROM records WHERE scope=? AND type=? ORDER BY CAST(id AS INTEGER) DESC',(scope,type_))
        return [json.loads(x['body']) for x in rows]

    def del_record(self,scope,type_,id_):
        self.execute('DELETE FROM records WHERE scope=? AND type=? AND id=?',(scope,type_,str(id_)))

    def enqueue(self,scope,method,path,payload=None,file_path=None):
        cur=self.execute('''INSERT INTO outbox(scope,method,path,payload,file_path,status,created_at)
        VALUES(?,?,?,?,?,'pending',?)''',
        (scope,method,path,json.dumps(payload,ensure_ascii=False) if payload is not None else None,file_path,now_iso()))
        return cur.lastrowid

    def pending(self,scope=None):
        if scope:
            return self.query("SELECT * FROM outbox WHERE scope=? AND status='pending' ORDER BY id",(scope,))
        return self.query("SELECT * FROM outbox WHERE status='pending' ORDER BY id")

    def queue(self,scope):
        return self.query("SELECT * FROM outbox WHERE scope=? AND status IN ('pending','sending','conflict') ORDER BY id DESC LIMIT 200",(scope,))

    def queue_count(self,scope,status):
        if status=='pending':
            row=self.single("SELECT COUNT(*) AS n FROM outbox WHERE scope=? AND status IN ('pending','sending')",(scope,))
        else:
            row=self.single('SELECT COUNT(*) AS n FROM outbox WHERE scope=? AND status=?',(scope,status))
        return row['n']

    def mark_sending(self,id_):
        self.execute("UPDATE outbox SET status='sending' WHERE id=? AND status='pending'",(id_,))

    def mark_pending(self,id_):
        self.execute("UPDATE outbox SET status='pending' WHERE id=? AND status='sending'",(id_,))

    def recover_inflight(self):
        # Após queda durante envio, a API pode ter gravado a venda.
        self.execute("UPDATE outbox SET status='conflict',error=? WHERE status='sending'",
            ('Resultado incerto após encerramento do programa. Confira no Django antes de reenviar.',))

    def finish(self,id_):
        self.execute("UPDATE outbox SET status='sent', error=NULL, sent_at=? WHERE id=?",(now_iso(),id_))

    def conflict(self,id_,error):
        self.execute("UPDATE outbox SET status='conflict',error=? WHERE id=?",(str(error)[:1000],id_))

    def retry(self,id_,scope):
        self.execute("UPDATE outbox SET status='pending',error=NULL WHERE id=? AND scope=? AND status='conflict'",(id_,scope))

    def set_map(self,scope,type_,local_id,remote_id):
        self.execute('''INSERT OR REPLACE INTO id_map(scope,type,local_id,remote_id)
        VALUES(?,?,?,?)''',(scope,type_,str(local_id),str(remote_id)))

    def get_map(self,scope,type_,local_id):
        row=self.single('SELECT remote_id FROM id_map WHERE scope=? AND type=? AND local_id=?',(scope,type_,str(local_id)))
        return row['remote_id'] if row else None

    def snapshot(self,scope,key,data):
        self.execute('''INSERT INTO snapshots(scope,key,body,updated_at) VALUES(?,?,?,?)
        ON CONFLICT(scope,key) DO UPDATE SET body=excluded.body,updated_at=excluded.updated_at''',
        (scope,key,json.dumps(data,ensure_ascii=False).encode('utf-8'),now_iso()))

    def get_snapshot(self,scope,key):
        r=self.single('SELECT body,updated_at FROM snapshots WHERE scope=? AND key=?',(scope,key))
        if not r:return None
        return json.loads(r['body']),r['updated_at']

    def meta(self,scope,key,default=None):
        r=self.single('SELECT value FROM metadata WHERE scope=? AND key=?',(scope,key))
        return r['value'] if r else default

    def set_meta(self,scope,key,value):
        self.execute('INSERT OR REPLACE INTO metadata(scope,key,value) VALUES(?,?,?)',(scope,key,str(value)))
