from dataclasses import dataclass,field
from typing import Any
@dataclass
class SiteDataset:
 id:str
 name:str
 source:str
 rows:list[dict]
 created_at:str=''
@dataclass
class CandidateSite:
 id:str
 name:str
 latitude:float
 longitude:float
 cost:float
 created_at:str=''
@dataclass
class CoverageScenario:
 id:str
 name:str
 dataset_id:str
 candidate_ids:list[str]
 radius_km:float=4.5
 budget:float=9
 max_sites:int=6
 created_at:str=''
@dataclass
class CoverageRun:
 id:str
 scenario_id:str
 status:str='queued'
 result:dict[str,Any]=field(default_factory=dict)
 error:str=''
 created_at:str=''
@dataclass
class DecisionReview:
 id:str
 run_id:str
 comment:str
 status:str='pending'
 reviewer:str=''
 created_at:str=''
@dataclass
class Report:
 id:str
 run_id:str
 review_id:str
 title:str
 created_at:str=''
