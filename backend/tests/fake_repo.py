import sys
import types
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass

class HTTPException(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail

TABLES = ('datasets', 'candidates', 'scenarios', 'runs', 'reviews', 'reports', 'users', 'audit', 'import_batches')

_store = {}

def _reset():
    _store.clear()

def all_rows(table):
    return [dict(v) for v in _store.get(table, {}).values()]

def get(table, id):
    if id not in _store.setdefault(table, {}):
        raise HTTPException(404, '记录不存在')
    return dict(_store[table][id])

def put(table, item, insert_only=False):
    if is_dataclass(item):
        item = asdict(item)
    if insert_only and item['id'] in _store.setdefault(table, {}):
        return item
    _store.setdefault(table, {})[item['id']] = dict(item)
    return item

@contextmanager
def transaction():
    yield _CONN

class _Conn:
    pass

_CONN = _Conn()

def tx_get(conn, table, id):
    row = _store.setdefault(table, {}).get(id)
    return dict(row) if row is not None else None

def tx_all(conn, table):
    return [dict(v) for v in _store.get(table, {}).values()]

def tx_put(conn, table, item, insert_only=False):
    if is_dataclass(item):
        item = asdict(item)
    if insert_only and item['id'] in _store.setdefault(table, {}):
        return item
    _store.setdefault(table, {})[item['id']] = dict(item)
    return item

def acquire_lock(conn, key, timeout=30):
    return 1

def release_lock(conn, key):
    return None

def init_db():
    pass

def run_migrations():
    pass

def install():
    module = types.ModuleType('src.utils.repository')
    for name, value in list(globals().items()):
        if name not in ('sys', 'types', 'contextmanager'):
            setattr(module, name, value)
    sys.modules['src.utils.repository'] = module
    return module
