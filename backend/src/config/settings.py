import os
from pathlib import Path
DATABASE_URL=os.getenv('DATABASE_URL','mysql://patrol:patrol_demo_password@127.0.0.1:17713/coverage_map')
REDIS_URL=os.getenv('REDIS_URL','redis://redis:6379/0')
JWT_SECRET=os.getenv('JWT_SECRET','coverage-map-demo-change-before-public-use')
SEED_DEMO=os.getenv('SEED_DEMO','true').lower()=='true'
TASK_MODE=os.getenv('TASK_MODE','redis')
ARTIFACT_DIR=Path(os.getenv('ARTIFACT_DIR','/artifacts'))
