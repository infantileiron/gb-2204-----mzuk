from fastapi import APIRouter,Depends
from src.controllers import scenario as controller
from src.schemas.entities import CoverageScenarioInput
from src.services.auth import current,editor,admin
router=APIRouter(prefix="/scenarios",tags=["scenarios"])
@router.get("")
def list_items(user=Depends(current)): return controller.list_items()
@router.post("",status_code=201)
def create(data:CoverageScenarioInput,user=Depends(editor)): return controller.create(data)
