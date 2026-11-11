from fastapi import APIRouter,Depends
from src.controllers import candidate as controller
from src.schemas.entities import CandidateInput
from src.services.auth import current,editor
router=APIRouter(prefix='/candidates',tags=['candidates'])
@router.get('')
def list_items(user=Depends(current)):return controller.list_items()
@router.post('',status_code=201)
def create(data:CandidateInput,user=Depends(editor)):return controller.create(data)
