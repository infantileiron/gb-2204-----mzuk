import math
from src.services.geo import distance_matrix

def weighted_coverage(points,candidates,radius_km,budget,max_sites):
 if not points or not candidates:raise ValueError('需求点与候选点不能为空')
 if len(candidates)>100 or len(points)>5000:raise ValueError('最多100候选点/5000需求点')
 if not math.isfinite(radius_km) or radius_km<=0 or not math.isfinite(budget) or budget<0 or not isinstance(max_sites,int) or max_sites<1:raise ValueError('半径、预算或数量限制无效')
 if len({p['site_id'] for p in points})!=len(points) or len({c['id'] for c in candidates})!=len(candidates):raise ValueError('需求点/候选点编号必须唯一')
 weights=[p['weight'] for p in points]
 if any(not math.isfinite(w) or w<0 for w in weights) or sum(weights)<=0:raise ValueError('权重必须非负且总权重大于0')
 if any(not math.isfinite(c['cost']) or c['cost']<=0 for c in candidates):raise ValueError('候选建设成本必须是正有限数')
 candidates=sorted(candidates,key=lambda c:c['id']);dist=distance_matrix(points,candidates)
 sets=[{j for j,d in enumerate(row) if d<=radius_km+1e-9} for row in dist]
 covered=set();chosen=[];spent=0;steps=[];total=sum(weights)
 while len(chosen)<max_sites:
  options=[]
  for i,c in enumerate(candidates):
   if i in chosen or spent+c['cost']>budget+1e-9:continue
   gain=sum(weights[j] for j in sets[i]-covered)
   if gain>1e-12:options.append((-(gain/c['cost']),-gain,c['id'],i,gain))
  if not options:break
  _,_,_,i,gain=min(options);chosen.append(i);covered|=sets[i];spent+=candidates[i]['cost']
  steps.append({'step':len(chosen),'candidate_id':candidates[i]['id'],'name':candidates[i]['name'],'cost':candidates[i]['cost'],'gain_weight':gain,'covered_weight':sum(weights[j] for j in covered),'coverage_rate':sum(weights[j] for j in covered)/total,'spent':spent})
 sensitivity=[]
 for i in chosen:
  remaining=set().union(*(sets[k] for k in chosen if k!=i)) if len(chosen)>1 else set()
  lost=sum(weights[j] for j in covered-remaining)
  sensitivity.append({'candidate_id':candidates[i]['id'],'name':candidates[i]['name'],'unique_weight':lost,'coverage_rate_without':sum(weights[j] for j in remaining)/total})
 mapped=[{**p,'covered':j in covered,'nearest_selected_km':min((dist[i][j] for i in chosen),default=None)} for j,p in enumerate(points)]
 return {'points':mapped,'candidates':candidates,'selected_ids':[candidates[i]['id'] for i in chosen],'selected':[candidates[i] for i in chosen],'steps':steps,'sensitivity':sensitivity,'covered_weight':sum(weights[j] for j in covered),'total_weight':total,'coverage_rate':sum(weights[j] for j in covered)/total,'covered_points':len(covered),'uncovered_points':len(points)-len(covered),'spent':spent,'budget':budget,'radius_km':radius_km,'distance_matrix_km':dist,'max_sites':max_sites}
