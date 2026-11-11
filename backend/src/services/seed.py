import random
from src.utils import repository as repo
from src.utils.identity import now
from src.utils.security import hash_password
from src.services.statistics import analyze

def demo_data():
 rng=random.Random(2204);points=[]
 for i in range(180):
  points.append({'site_id':f'YD-{i+1:03d}','label':f'{["芦汀","鹭洲","浅滩","杉湾"][i%4]}样点{i+1:03d}','latitude':round(31.26+rng.random()*.25,6),'longitude':round(120.44+rng.random()*.37,6),'weight':rng.choice([1,2,3,5,8])})
 candidates=[{'id':f'candidate-{i+1:02d}','name':f'{["芦汀","鹭洲","浅滩","杉湾"][i%4]}候选点{i+1:02d}','latitude':round(31.28+(i//6)*.065,6),'longitude':round(120.46+(i%6)*.065,6),'cost':float(1+i%3),'created_at':now()} for i in range(24)]
 return points,candidates

def seed():
 repo.init_db()
 for role,name in [('admin','巡护决策复核人'),('analyst','湿地空间分析员'),('viewer','巡护队观察员')]:
  email=f'{role}@yedu.test';repo.put('users',{'id':email,'email':email,'name':name,'role':role,'password_hash':hash_password('Patrol2026!')},insert_only=True)
 points,candidates=demo_data();repo.put('datasets',{'id':'ds-patrol','name':'野渡湿地巡护需求 · 180点','source':'patrol_demands_202611.csv','rows':points,'created_at':now()},insert_only=True)
 for c in candidates:repo.put('candidates',c,insert_only=True)
 repo.put('scenarios',{'id':'scenario-wetland','name':'秋季巡护 · 九万元六点上限','dataset_id':'ds-patrol','candidate_ids':[c['id'] for c in candidates],'radius_km':4.5,'budget':9,'max_sites':6,'created_at':now()},insert_only=True)
 repo.put('runs',{'id':'run-baseline','scenario_id':'scenario-wetland','status':'completed','result':analyze(points,candidates),'error':'','created_at':now()},insert_only=True)
 repo.put('reviews',{'id':'review-baseline','run_id':'run-baseline','comment':'球面直线距离及预算口径已检查；不替代航道可达性勘测。','status':'approved','reviewer':'admin@yedu.test','created_at':now()},insert_only=True)
 repo.put('reports',{'id':'report-baseline','run_id':'run-baseline','review_id':'review-baseline','title':'秋季补给点覆盖复核图册','created_at':now()},insert_only=True)
 return {t:len(repo.all_rows(t)) for t in ('users','datasets','candidates','scenarios','runs','reviews','reports')}
