import csv,io,math
from dataclasses import asdict
from src.models.entities import SiteDataset
from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.services.geo import valid_coordinate

def summary(item):return {k:v for k,v in item.items() if k!='rows'}|{'row_count':len(item['rows']),'total_weight':sum(r['weight'] for r in item['rows'])}
def list_datasets():return [summary(x) for x in repo.all_rows('datasets')]
def detail(id):return repo.get('datasets',id)
def rename(id,data):
 item=repo.get('datasets',id);item['name']=data.name;repo.put('datasets',item);return summary(item)
def create(data):
 reader=csv.DictReader(io.StringIO(data.csv_text.lstrip('\ufeff')))
 if not {'site_id','label','latitude','longitude','weight'}.issubset(reader.fieldnames or []):raise ValueError('CSV需要site_id,label,latitude,longitude,weight列')
 rows=[];seen=set()
 for n,r in enumerate(reader,2):
  if n>5001:raise ValueError('最多5000需求点')
  try:
   lat,lon,weight=float(r['latitude']),float(r['longitude']),float(r['weight']);valid_coordinate(lat,lon)
   if not math.isfinite(weight) or weight<0 or not r['site_id'].strip() or r['site_id'] in seen or not r['label'].strip():raise ValueError()
  except (ValueError,TypeError):raise ValueError(f'第{n}行坐标/权重/编号无效或重复')
  seen.add(r['site_id']);rows.append({'site_id':r['site_id'],'label':r['label'],'latitude':lat,'longitude':lon,'weight':weight})
 if not rows or sum(x['weight'] for x in rows)<=0:raise ValueError('需求总权重必须大于0')
 item=SiteDataset(new_id('ds'),data.name,data.source,rows,now());repo.put('datasets',item);return summary(asdict(item))
