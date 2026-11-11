from fastapi import APIRouter,Depends
from src.controllers import dataset as controller
from src.schemas.entities import DatasetInput,DatasetImportInput,RenameDataset
from src.services.auth import current,editor
router=APIRouter(prefix="/datasets",tags=["datasets"])
@router.get("")
def list_items(user=Depends(current)): return controller.list_items()
@router.post("",status_code=201)
def create(data:DatasetInput,user=Depends(editor)): return controller.create(data)
@router.get("/{id}")
def detail(id:str,user=Depends(current)): return controller.detail(id)
@router.patch('/{id}')
def rename(id:str,data:RenameDataset,user=Depends(editor)):
 from src.services.dataset import rename
 return rename(id,data)
@router.get("/{id}/imports")
def list_imports(id:str,user=Depends(current)): return controller.list_imports(id)
@router.post("/{id}/imports",status_code=201)
def append_import(id:str,data:DatasetImportInput,user=Depends(editor)): return controller.append_import(id,data)
@router.get("/{id}/imports/{batch_id}")
def import_detail(id:str,batch_id:str,user=Depends(current)): return controller.import_detail(id,batch_id)
@router.get("/{id}/imports/{batch_id}/replay")
def replay(id:str,batch_id:str,user=Depends(editor)): return controller.replay(id,batch_id)
