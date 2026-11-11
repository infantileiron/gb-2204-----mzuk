from src.models.entities import CoverageScenario
from src.utils import repository as repo
from src.utils.identity import new_id,now

def list_scenarios():return repo.all_rows('scenarios')
def create(data):
 repo.get('datasets',data.dataset_id)
 if len(set(data.candidate_ids))!=len(data.candidate_ids):raise ValueError('候选点不能重复')
 for id in data.candidate_ids:repo.get('candidates',id)
 return repo.put('scenarios',CoverageScenario(new_id('scenario'),data.name,data.dataset_id,data.candidate_ids,data.radius_km,data.budget,data.max_sites,now()))
