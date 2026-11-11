from fastapi.responses import PlainTextResponse
from src.services import dataset as service
def list_items(): return service.list_datasets()
def detail(id): return service.detail(id)
def create(data): return service.create(data)
def list_imports(id): return service.list_imports(id)
def import_detail(id,batch_id): return service.import_detail(id,batch_id)
def replay(id,batch_id): return PlainTextResponse(service.replay_quarantine(id,batch_id),media_type='text/csv; charset=utf-8')
def append_import(id,data): return service.append_import(id,data)
