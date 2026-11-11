import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

_tmp = tempfile.mkdtemp(prefix='coverage-artifacts-')
os.environ['TASK_MODE'] = 'inline'
os.environ['ARTIFACT_DIR'] = _tmp

sys.path.insert(0, os.path.dirname(__file__))
import fake_repo
fake_repo.install()

from src.utils import repository as repo
from src.services import dataset as dataset_service
from src.services import run as run_service

HEADER = 'site_id,label,latitude,longitude,weight,surveyed_at\n'

def csv_text(*lines):
    return HEADER + '\n'.join(lines) + '\n'

class RunSnapshotTests(unittest.TestCase):
    def setUp(self):
        fake_repo._reset()
        repo.put('candidates', {'id': 'c-01', 'name': '候选甲', 'latitude': 31.30, 'longitude': 120.50, 'cost': 2.0})
        repo.put('candidates', {'id': 'c-02', 'name': '候选乙', 'latitude': 31.50, 'longitude': 120.70, 'cost': 3.0})

    def _scenario(self, ds_id):
        repo.put('scenarios', {'id': 'sc-1', 'name': '测试方案', 'dataset_id': ds_id,
                               'candidate_ids': ['c-01', 'c-02'], 'radius_km': 500.0,
                               'budget': 9.0, 'max_sites': 6, 'created_at': 't0'})

    def test_new_runs_use_latest_dataset_but_old_run_keeps_snapshot(self):
        first = csv_text(
            'YD-001,样点一,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,样点二,31.50,120.70,5,2026-11-01T08:00:00+00:00',
        )
        created = dataset_service.create(SimpleNamespace(
            name='野渡需求', source='a.csv', csv_text=first, idempotency_key=None))
        ds_id = created['id']
        self._scenario(ds_id)

        run_one = run_service.create(SimpleNamespace(scenario_id='sc-1'))
        self.assertEqual(run_one['status'], 'completed')
        self.assertEqual(run_one['result']['dataset_snapshot']['version'], 1)
        self.assertEqual(len(run_one['result']['points']), 2)
        snapshot_checksum = run_one['result']['checksum']

        # 补测：更新权重 + 新增第三个点
        supplement = csv_text(
            'YD-001,样点一,31.30,120.50,8,2026-11-08T09:00:00+00:00',
            'YD-003,样点三,31.40,120.60,2,2026-11-08T09:00:00+00:00',
        )
        updated = dataset_service.append_import(ds_id, SimpleNamespace(
            name='野渡需求', source='b.csv', csv_text=supplement, idempotency_key=None))
        self.assertEqual(updated['version'], 2)

        run_two = run_service.create(SimpleNamespace(scenario_id='sc-1'))
        self.assertEqual(run_two['result']['dataset_snapshot']['version'], 2)
        self.assertEqual(len(run_two['result']['points']), 3)
        self.assertNotEqual(run_two['result']['checksum'], snapshot_checksum)

        # 已完成的旧运行不被追溯修改
        old = repo.get('runs', run_one['id'])
        self.assertEqual(len(old['result']['points']), 2)
        self.assertEqual(old['result']['checksum'], snapshot_checksum)
        self.assertEqual(old['result']['dataset_snapshot']['version'], 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
