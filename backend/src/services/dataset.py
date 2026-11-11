from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.services import importing

def summary(item):
 return {k:v for k,v in item.items() if k!='rows'}|{'row_count':len(item['rows']),'total_weight':sum(r['weight'] for r in item['rows'])}

def list_datasets():return [summary(x) for x in repo.all_rows('datasets')]
def detail(id):return repo.get('datasets',id)
def rename(id,data):
 item=repo.get('datasets',id);item['name']=data.name;repo.put('datasets',item);return summary(item)

def list_imports(dataset_id):
 repo.get('datasets',dataset_id)
 return [_batch_summary(b) for b in repo.all_rows('import_batches') if b['dataset_id']==dataset_id]

def import_detail(dataset_id,batch_id):
 batch=repo.get('import_batches',batch_id)
 if batch['dataset_id']!=dataset_id:raise repo.HTTPException(404,'批次不属于该需求')
 return batch

def replay_quarantine(dataset_id,batch_id):
 batch=import_detail(dataset_id,batch_id)
 if not batch['quarantined']:raise ValueError('该批次没有隔离行，无需重放')
 return importing.replay_payload(batch['quarantined'])

def _batch_summary(batch):
 return {k:v for k,v in batch.items() if k!='quarantined'}|{'quarantined_count':len(batch.get('quarantined',[]))}

def create(data):
 return _import(data,dataset_id=None)

def append_import(dataset_id,data):
 return _import(data,dataset_id=dataset_id)

def _import(data,dataset_id):
 text=data.csv_text
 digest=importing.fingerprint(text)
 lock_key=f'coverage-map-dataset-{dataset_id or "new"}'
 with repo.transaction() as conn:
  repo.acquire_lock(conn,lock_key)
  try:
   existing=repo.tx_get(conn,'datasets',dataset_id) if dataset_id else None
   if dataset_id and existing is None:raise repo.HTTPException(404,'记录不存在')
   for batch in repo.tx_all(conn,'import_batches'):
    same_scope=(dataset_id is None) or batch['dataset_id']==dataset_id
    if not same_scope:continue
    if (data.idempotency_key and batch.get('idempotency_key')==data.idempotency_key) or batch['fingerprint']==digest:
     prior=repo.tx_get(conn,'datasets',batch['dataset_id'])
     return summary(prior)|{'import_batch':_batch_summary(batch)|{'duplicate':True,'duplicate_of':batch['id']}}
   accepted,quarantined=importing.parse_csv(text)
   if not accepted:raise ValueError('没有可导入的有效行，请按隔离原因修正后重放')
   existing_rows=existing['rows'] if existing else []
   merged,merge=importing.merge_rows(existing_rows,accepted)
   if sum(r['weight'] for r in merged)<=0:raise ValueError('导入后需求总权重必须大于0')
   if existing:
    existing['rows']=merged;existing['version']=existing.get('version',1)+1;existing['updated_at']=now()
    repo.tx_put(conn,'datasets',existing);dataset=existing
   else:
    dataset={'id':new_id('ds'),'name':data.name,'source':data.source,'rows':merged,
             'created_at':now(),'updated_at':now(),'version':1}
    repo.tx_put(conn,'datasets',dataset)
   batch={
    'id':new_id('imp'),'dataset_id':dataset['id'],'fingerprint':digest,
    'idempotency_key':data.idempotency_key or None,'source':data.source,
    'created_at':now(),'status':'quarantined' if quarantined else 'applied',
    'counts':importing.summarize_batch(accepted,quarantined,merge),
    'inserted':merge['inserted'],'updated':merge['updated'],'ignored':merge['ignored'],
    'quarantined':quarantined,
   }
   repo.tx_put(conn,'import_batches',batch)
   return summary(dataset)|{'import_batch':_batch_summary(batch)}
  finally:
   repo.release_lock(conn,lock_key)
