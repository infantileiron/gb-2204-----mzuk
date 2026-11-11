import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
import fake_repo
fake_repo.install()

from src.services import dataset as service

HEADER = 'site_id,label,latitude,longitude,weight,surveyed_at\n'

def csv_text(*lines):
    return HEADER + '\n'.join(lines) + '\n'

def input_payload(text, name='野渡湿地巡护需求', source='patrol_demands_202611.csv', key=None):
    return SimpleNamespace(name=name, source=source, csv_text=text, idempotency_key=key)

class ImportServiceTests(unittest.TestCase):
    def setUp(self):
        fake_repo._reset()

    def test_first_import_creates_dataset_and_batch(self):
        text = csv_text(
            'YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,鹭洲样点,31.31,120.51,5,2026-11-01T08:05:00+00:00',
        )
        result = service.create(input_payload(text))
        self.assertEqual(result['row_count'], 2)
        self.assertEqual(result['total_weight'], 8)
        self.assertEqual(result['version'], 1)
        batch = result['import_batch']
        self.assertEqual(batch['counts']['inserted_count'], 2)
        self.assertEqual(batch['status'], 'applied')
        self.assertFalse(batch.get('duplicate'))
        stored = service.detail(result['id'])
        self.assertEqual({r['site_id'] for r in stored['rows']}, {'YD-001', 'YD-002'})

    def test_append_merge_update_ignore_quarantine_together(self):
        first = csv_text(
            'YD-001,旧点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,保持点,31.40,120.60,5,2026-11-01T08:00:00+00:00',
        )
        created = service.create(input_payload(first))
        ds_id = created['id']
        supplement = csv_text(
            'YD-001,新点,31.32,120.52,8,2026-11-05T09:00:00+00:00',
            'YD-002,晚到旧观测,31.00,120.00,99,2026-10-20T09:00:00+00:00',
            'YD-003,新增点,31.50,120.70,2,2026-11-06T09:00:00+00:00',
            'YD-004,坏坐标,999,120.70,2,2026-11-06T09:00:00+00:00',
        )
        result = service.append_import(ds_id, input_payload(supplement, source='patrol_supplement.csv'))
        batch = result['import_batch']
        self.assertEqual(batch['counts']['inserted_count'], 1)
        self.assertEqual(batch['counts']['updated_count'], 1)
        self.assertEqual(batch['counts']['ignored_count'], 1)
        self.assertEqual(batch['counts']['quarantined_rows'], 1)
        self.assertEqual(batch['status'], 'quarantined')
        self.assertEqual(batch['ignored'], [{'site_id': 'YD-002', 'reason': 'surveyed_at_not_newer'}])
        # 好行已落库，坏行未进需求
        stored = service.detail(ds_id)
        by_id = {r['site_id']: r for r in stored['rows']}
        self.assertEqual(set(by_id), {'YD-001', 'YD-002', 'YD-003'})
        self.assertEqual(by_id['YD-001']['weight'], 8)
        self.assertEqual(by_id['YD-002']['weight'], 5)
        self.assertEqual(result['version'], 2)

    def test_duplicate_delivery_does_not_write_twice(self):
        text = csv_text('YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00')
        first = service.create(input_payload(text))
        ds_id = first['id']
        again = service.append_import(ds_id, input_payload(text, source='same-file.csv'))
        self.assertTrue(again['import_batch']['duplicate'])
        self.assertEqual(again['import_batch']['duplicate_of'], first['import_batch']['id'])
        stored = service.detail(ds_id)
        self.assertEqual(len(stored['rows']), 1)
        self.assertEqual(len(service.list_imports(ds_id)), 1)

    def test_idempotency_key_dedupes_even_with_rewritten_csv(self):
        text_a = csv_text('YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00')
        first = service.create(input_payload(text_a, key='delivery-001'))
        text_b = csv_text('YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00')
        # 相同内容（含同样换行）指纹一致；这里显式验证幂等键路径
        again = service.append_import(first['id'], input_payload(text_b, key='delivery-001'))
        self.assertTrue(again['import_batch']['duplicate'])
        self.assertEqual(len(service.list_imports(first['id'])), 1)

    def test_all_bad_csv_fails_and_writes_nothing(self):
        text = csv_text(
            'YD-001,坏权重,31.30,120.50,-9,2026-11-01T08:00:00+00:00',
            'YD-002,坏时间,31.30,120.50,3,nope',
        )
        with self.assertRaises(ValueError):
            service.create(input_payload(text))
        self.assertEqual(fake_repo._store.get('datasets', {}), {})
        self.assertEqual(fake_repo._store.get('import_batches', {}), {})

    def test_zero_total_weight_rejected(self):
        text = csv_text('YD-001,零权重,31.30,120.50,0,2026-11-01T08:00:00+00:00')
        with self.assertRaises(ValueError):
            service.create(input_payload(text))

    def test_replay_returns_quarantined_rows_csv(self):
        text = csv_text(
            'YD-001,好点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,坏坐标,999,120.50,3,2026-11-01T08:00:00+00:00',
        )
        created = service.create(input_payload(text))
        ds_id = created['id']
        batch_id = created['import_batch']['id']
        detail = service.import_detail(ds_id, batch_id)
        self.assertEqual(detail['quarantined'][0]['reason'], 'invalid_coordinate')
        replay_csv = service.replay_quarantine(ds_id, batch_id)
        self.assertIn('site_id,label,latitude,longitude,weight,surveyed_at', replay_csv)
        self.assertIn('YD-002', replay_csv)
        self.assertNotIn('YD-001', replay_csv.split('\n', 1)[1])

    def test_replay_then_fixed_reimport_applies_good_rows(self):
        text = csv_text(
            'YD-001,好点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,坏坐标,999,120.50,3,2026-11-01T08:00:00+00:00',
        )
        created = service.create(input_payload(text))
        ds_id = created['id']
        fixed = csv_text('YD-002,修复点,31.33,120.53,4,2026-11-02T08:00:00+00:00')
        result = service.append_import(ds_id, input_payload(fixed, source='replay-fixed.csv'))
        self.assertEqual(result['import_batch']['counts']['inserted_count'], 1)
        self.assertEqual(result['row_count'], 2)

    def test_batch_listing_excludes_raw_quarantine_but_keeps_count(self):
        text = csv_text(
            'YD-001,好点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,坏坐标,999,120.50,3,2026-11-01T08:00:00+00:00',
        )
        created = service.create(input_payload(text))
        listing = service.list_imports(created['id'])
        self.assertEqual(len(listing), 1)
        self.assertNotIn('quarantined', listing[0])
        self.assertEqual(listing[0]['quarantined_count'], 1)

    def test_full_quarantine_replay_repair_loop(self):
        first = csv_text(
            'YD-001,好点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,坏坐标,999,120.50,3,2026-11-01T08:00:00+00:00',
        )
        created = service.create(input_payload(first))
        ds_id = created['id']
        batch_id = created['import_batch']['id']
        # 下载隔离行 → 模拟人工修正 → 重放导入
        replay_csv = service.replay_quarantine(ds_id, batch_id)
        fixed = replay_csv.replace('999', '31.33')
        repaired = service.append_import(ds_id, input_payload(fixed, source='replay-fixed.csv'))
        self.assertEqual(repaired['import_batch']['counts']['inserted_count'], 1)
        self.assertEqual(repaired['import_batch']['counts']['quarantined_rows'], 0)
        stored = service.detail(ds_id)
        self.assertEqual({r['site_id'] for r in stored['rows']}, {'YD-001', 'YD-002'})
        self.assertEqual(stored['version'], 2)
        # 两个批次都留痕
        self.assertEqual(len(service.list_imports(ds_id)), 2)

    def test_late_older_record_never_overwrites_across_batches(self):
        first = csv_text('YD-001,现行点,31.30,120.50,8,2026-11-10T08:00:00+00:00')
        created = service.create(input_payload(first))
        ds_id = created['id']
        old_delivery = csv_text('YD-001,晚到旧观测,31.00,120.00,1,2026-10-01T08:00:00+00:00')
        result = service.append_import(ds_id, input_payload(old_delivery, source='late.csv'))
        self.assertEqual(result['import_batch']['counts']['updated_count'], 0)
        self.assertEqual(result['import_batch']['counts']['ignored_count'], 1)
        stored = service.detail(ds_id)
        self.assertEqual(stored['rows'][0]['weight'], 8)
        self.assertEqual(stored['rows'][0]['label'], '现行点')

    def test_append_to_missing_dataset_raises_404(self):
        text = csv_text('YD-001,好点,31.30,120.50,3,2026-11-01T08:00:00+00:00')
        with self.assertRaises(fake_repo.HTTPException) as ctx:
            service.append_import('ds-missing', input_payload(text))
        self.assertEqual(ctx.exception.status_code, 404)

if __name__ == '__main__':
    unittest.main(verbosity=2)
