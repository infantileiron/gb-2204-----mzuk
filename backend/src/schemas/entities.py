from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
class StrictModel(BaseModel):
 model_config=ConfigDict(allow_inf_nan=False)
class LoginInput(StrictModel):
 email:str
 password:str
class DatasetInput(StrictModel):
 name:str=Field(min_length=2,max_length=100)
 source:str=Field(default='patrol_demands_202611.csv',max_length=100)
 csv_text:str=Field(min_length=20,max_length=1000000)
 idempotency_key:str|None=Field(default=None,max_length=128)
class DatasetImportInput(StrictModel):
 source:str=Field(default='patrol_supplement_202612.csv',max_length=100)
 csv_text:str=Field(min_length=20,max_length=1000000)
 idempotency_key:str|None=Field(default=None,max_length=128)
class RenameDataset(StrictModel):
 name:str=Field(min_length=2,max_length=100)
class CandidateInput(StrictModel):
 name:str=Field(min_length=2,max_length=80)
 latitude:float=Field(ge=-90,le=90)
 longitude:float=Field(ge=-180,le=180)
 cost:float=Field(gt=0,le=100000)
class CoverageScenarioInput(StrictModel):
 name:str=Field(min_length=2,max_length=100)
 dataset_id:str
 candidate_ids:list[str]=Field(min_length=1,max_length=100)
 radius_km:float=Field(default=4.5,gt=0,le=1000)
 budget:float=Field(default=9,ge=0,le=100000)
 max_sites:int=Field(default=6,ge=1,le=100)
class RunInput(StrictModel):
 scenario_id:str
class ReviewInput(StrictModel):
 run_id:str
 comment:str=Field(min_length=5,max_length=2000)
class DecisionInput(StrictModel):
 status:Literal['approved','rejected']
 comment:str=Field(min_length=5,max_length=2000)
class ReportInput(StrictModel):
 run_id:str
 review_id:str
 title:str=Field(min_length=2,max_length=100)
