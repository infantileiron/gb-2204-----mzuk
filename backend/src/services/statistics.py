import hashlib,json
from src.services.coverage import weighted_coverage

def analyze(points,candidates,radius_km=4.5,budget=9,max_sites=6):
 result=weighted_coverage(points,candidates,radius_km,budget,max_sites)
 result['checksum']=hashlib.sha256(json.dumps({'points':points,'candidates':sorted(candidates,key=lambda c:c['id']),'radius_km':radius_km,'budget':budget,'max_sites':max_sites},sort_keys=True).encode()).hexdigest()
 result['limitations']=['球面直线距离不是道路/航道通行距离，地图仅局部示意','贪心按新增覆盖权重/成本排序，并列按增益再按ID确定，属于启发式，不保证全局最优','半径以km计；权重是模拟巡护需求，成本为模拟万元','移除敏感性固定其余点位，不重新优化，也不表示因果效应']
 return result
