import json
from dataclasses import asdict
from urllib.parse import urlsplit,unquote
import pymysql
from fastapi import HTTPException
from src.config.settings import DATABASE_URL
TABLES=('datasets','candidates','scenarios','runs','reviews','reports','users','audit')
def connect():
 u=urlsplit(DATABASE_URL)
 return pymysql.connect(host=u.hostname,port=u.port or 3306,user=unquote(u.username),password=unquote(u.password),database=u.path.lstrip('/'),charset='utf8mb4')
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
