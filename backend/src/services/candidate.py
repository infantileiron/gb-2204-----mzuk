from src.models.entities import CandidateSite
from src.utils import repository as repo
from src.utils.identity import new_id,now

def list_candidates():return repo.all_rows('candidates')
def create(data):return repo.put('candidates',CandidateSite(new_id('site'),data.name,data.latitude,data.longitude,data.cost,now()))
