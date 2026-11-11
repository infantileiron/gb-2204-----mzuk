import json
from contextlib import contextmanager
from dataclasses import asdict
from urllib.parse import urlsplit,unquote
from pathlib import Path
import pymysql
from fastapi import HTTPException
from src.config.settings import DATABASE_URL
TABLES=('datasets','candidates','scenarios','runs','reviews','reports','users','audit','import_batches')
def connect():
 u=urlsplit(DATABASE_URL)
 return pymysql.connect(host=u.hostname,port=u.port or 3306,user=unquote(u.username),password=unquote(u.password),database=u.path.lstrip('/'),charset='utf8mb4',autocommit=False)
def init_db():
 conn=connect()
 try:
  with conn.cursor() as c:
   c.execute("SELECT GET_LOCK('coverage-map-init',30)")
   if c.fetchone()[0]!=1:raise RuntimeError('database initialization lock timeout')
   for table in TABLES:c.execute(f'CREATE TABLE IF NOT EXISTS {table} (id VARCHAR(128) PRIMARY KEY,payload LONGTEXT NOT NULL)')
  conn.commit()
 finally:conn.close()
def all_rows(table):
 assert table in TABLES;conn=connect()
 try:
  with conn.cursor() as c:c.execute(f'SELECT payload FROM {table} ORDER BY id');return [json.loads(x[0]) for x in c.fetchall()]
 finally:conn.close()
def get(table,id):
 assert table in TABLES;conn=connect()
 try:
  with conn.cursor() as c:c.execute(f'SELECT payload FROM {table} WHERE id=%s',(id,));row=c.fetchone()
  if row is None:raise HTTPException(404,'记录不存在')
  return json.loads(row[0])
 finally:conn.close()
def put(table,item,insert_only=False):
 assert table in TABLES
 if not isinstance(item,dict):item=asdict(item)
 conn=connect()
 try:
  payload=json.dumps(item,ensure_ascii=False,allow_nan=False)
  with conn.cursor() as c:
   if insert_only:c.execute(f'INSERT IGNORE INTO {table}(id,payload) VALUES(%s,%s)',(item['id'],payload))
   else:c.execute(f'INSERT INTO {table}(id,payload) VALUES(%s,%s) ON DUPLICATE KEY UPDATE payload=VALUES(payload)',(item['id'],payload))
  conn.commit();return item
 finally:conn.close()
@contextmanager
def transaction():
 conn=connect()
 try:
  yield conn
  conn.commit()
 except Exception:
  conn.rollback();raise
 finally:conn.close()
def tx_get(conn,table,id):
 assert table in TABLES
 with conn.cursor() as c:
  c.execute(f'SELECT payload FROM {table} WHERE id=%s',(id,));row=c.fetchone()
  if row is None:return None
  return json.loads(row[0])
def tx_all(conn,table):
 assert table in TABLES
 with conn.cursor() as c:
  c.execute(f'SELECT payload FROM {table} ORDER BY id')
  return [json.loads(x[0]) for x in c.fetchall()]
def tx_put(conn,table,item,insert_only=False):
 assert table in TABLES
 if not isinstance(item,dict):item=asdict(item)
 payload=json.dumps(item,ensure_ascii=False,allow_nan=False)
 with conn.cursor() as c:
  if insert_only:c.execute(f'INSERT IGNORE INTO {table}(id,payload) VALUES(%s,%s)',(item['id'],payload))
  else:c.execute(f'INSERT INTO {table}(id,payload) VALUES(%s,%s) ON DUPLICATE KEY UPDATE payload=VALUES(payload)',(item['id'],payload))
 return item
def acquire_lock(conn,key,timeout=30):
 with conn.cursor() as c:
  c.execute('SELECT GET_LOCK(%s,%s)',(key,timeout));ok=c.fetchone()[0]
 if ok!=1:raise RuntimeError('需求正在被其他导入处理，请稍后重试')
def release_lock(conn,key):
 with conn.cursor() as c:c.execute('SELECT RELEASE_LOCK(%s)',(key,))
def run_migrations():
 init_db()
 for path in sorted(Path(__file__).resolve().parents[2].joinpath('migrations').glob('*.sql')):
  conn=connect()
  try:
   with conn.cursor() as c:
    for statement in [s.strip() for s in path.read_text(encoding='utf-8').split(';') if s.strip()]:c.execute(statement)
   conn.commit()
  finally:conn.close()
