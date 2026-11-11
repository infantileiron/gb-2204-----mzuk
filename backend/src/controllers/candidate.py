from src.services import candidate as service
def list_items():return service.list_candidates()
def create(data):return service.create(data)
