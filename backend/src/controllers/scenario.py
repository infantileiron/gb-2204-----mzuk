from src.services import scenario as service
def list_items(): return service.list_scenarios()
def create(data): return service.create(data)
