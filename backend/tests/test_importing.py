import unittest

from src.services import importing

HEADER = 'site_id,label,latitude,longitude,weight,surveyed_at\n'

def csv_text(*lines):
    return HEADER + '\n'.join(lines) + '\n'

class ParseCsvTests(unittest.TestCase):
    def test_valid_rows_accepted(self):
        text = csv_text(
            'YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,鹭洲样点,31.31,120.51,0,2026-11-01T08:05:00Z',
        )
        accepted, quarantined = importing.parse_csv(text)
        self.assertEqual(len(accepted), 2)
        self.assertEqual(quarantined, [])
        self.assertEqual(accepted[0]['site_id'], 'YD-001')
        self.assertEqual(accepted[1]['surveyed_at'], '2026-11-01T08:05:00+00:00')

    def test_missing_column_rejected(self):
        with self.assertRaises(ValueError):
            importing.parse_csv('site_id,label,latitude,longitude,weight\nYD-1,x,1,2,3\n')

    def test_bad_rows_are_quarantined_not_raised(self):
        text = csv_text(
            'YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,坏坐标,999,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-003,坏权重,31.30,120.50,-1,2026-11-01T08:00:00+00:00',
            'YD-004,坏时间,31.30,120.50,2,not-a-time',
            ',空编号,31.30,120.50,2,2026-11-01T08:00:00+00:00',
            'YD-005,,31.30,120.50,2,2026-11-01T08:00:00+00:00',
        )
        accepted, quarantined = importing.parse_csv(text)
        self.assertEqual([r['site_id'] for r in accepted], ['YD-001'])
        self.assertEqual([q['reason'] for q in quarantined],
                         ['invalid_coordinate', 'invalid_weight', 'invalid_surveyed_at', 'empty_site_id', 'empty_label'])
        self.assertEqual([q['line_number'] for q in quarantined], [3, 4, 5, 6, 7])
        self.assertEqual(quarantined[0]['raw']['site_id'], 'YD-002')

    def test_duplicate_in_batch_goes_to_quarantine(self):
        text = csv_text(
            'YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-001,重复样点,31.32,120.52,5,2026-11-02T08:00:00+00:00',
        )
        accepted, quarantined = importing.parse_csv(text)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(quarantined[0]['reason'], 'duplicate_in_batch')
        self.assertEqual(quarantined[0]['line_number'], 3)

    def test_naive_timestamp_assumed_utc(self):
        accepted, _ = importing.parse_csv(csv_text('YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00'))
        self.assertEqual(accepted[0]['surveyed_at'], '2026-11-01T08:00:00+00:00')

    def test_non_finite_values_are_quarantined(self):
        text = csv_text(
            'YD-001,无限权重,31.30,120.50,inf,2026-11-01T08:00:00+00:00',
            'YD-002,NaN坐标,nan,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-003,越界纬度,91,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-004,正常点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
        )
        accepted, quarantined = importing.parse_csv(text)
        self.assertEqual([r['site_id'] for r in accepted], ['YD-004'])
        self.assertEqual([q['reason'] for q in quarantined],
                         ['invalid_weight', 'invalid_coordinate', 'invalid_coordinate'])

    def test_fingerprint_normalizes_newlines_and_bom(self):
        base = csv_text('YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00')
        crlf = '﻿' + base.replace('\n', '\r\n')
        self.assertEqual(importing.fingerprint(base), importing.fingerprint(crlf))
        other = csv_text('YD-002,其他样点,31.30,120.50,3,2026-11-01T08:00:00+00:00')
        self.assertNotEqual(importing.fingerprint(base), importing.fingerprint(other))

    def test_replay_payload_roundtrip(self):
        text = csv_text(
            'YD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00',
            'YD-002,坏坐标,999,120.50,3,2026-11-01T08:00:00+00:00',
        )
        _, quarantined = importing.parse_csv(text)
        replay = importing.replay_payload(quarantined)
        accepted2, quarantined2 = importing.parse_csv(replay)
        self.assertEqual(accepted2, [])
        self.assertEqual(len(quarantined2), 1)
        self.assertEqual(quarantined2[0]['raw']['latitude'], '999')

class MergeRowsTests(unittest.TestCase):
    existing = [
        {'site_id': 'YD-001', 'label': '旧点', 'latitude': 31.3, 'longitude': 120.5, 'weight': 3,
         'surveyed_at': '2026-11-01T08:00:00+00:00'},
        {'site_id': 'YD-002', 'label': '保持点', 'latitude': 31.4, 'longitude': 120.6, 'weight': 5,
         'surveyed_at': '2026-11-01T08:00:00+00:00'},
    ]

    def test_insert_update_ignore_decided_by_surveyed_at(self):
        incoming = [
            # 更晚采测 → 更新
            {'site_id': 'YD-001', 'label': '新点', 'latitude': 31.31, 'longitude': 120.51, 'weight': 8,
             'surveyed_at': '2026-11-05T09:00:00+00:00'},
            # 更早采测（晚到的旧记录）→ 忽略，不覆盖权重
            {'site_id': 'YD-002', 'label': '旧观测', 'latitude': 31.0, 'longitude': 120.0, 'weight': 99,
             'surveyed_at': '2026-10-20T09:00:00+00:00'},
            # 新编号 → 新增
            {'site_id': 'YD-003', 'label': '新增点', 'latitude': 31.5, 'longitude': 120.7, 'weight': 2,
             'surveyed_at': '2026-11-06T09:00:00+00:00'},
        ]
        merged, stats = importing.merge_rows(self.existing, incoming)
        self.assertEqual(stats['inserted'], ['YD-003'])
        self.assertEqual(stats['updated'], ['YD-001'])
        self.assertEqual(stats['ignored'], [{'site_id': 'YD-002', 'reason': 'surveyed_at_not_newer'}])
        by_id = {r['site_id']: r for r in merged}
        self.assertEqual(by_id['YD-001']['weight'], 8)
        self.assertEqual(by_id['YD-001']['label'], '新点')
        self.assertEqual(by_id['YD-002']['weight'], 5)
        self.assertEqual(by_id['YD-002']['label'], '保持点')
        self.assertEqual(len(merged), 3)
        # 原始数据不被修改
        self.assertEqual(self.existing[0]['weight'], 3)

    def test_equal_surveyed_at_does_not_overwrite(self):
        incoming = [dict(self.existing[0], weight=99)]
        merged, stats = importing.merge_rows(self.existing, incoming)
        self.assertEqual(stats['ignored'][0]['reason'], 'surveyed_at_not_newer')
        self.assertEqual({r['site_id']: r['weight'] for r in merged}['YD-001'], 3)

    def test_legacy_rows_without_surveyed_at_are_updateable(self):
        legacy = [{'site_id': 'OLD-1', 'label': '老数据', 'latitude': 1.0, 'longitude': 2.0, 'weight': 1}]
        incoming = [{'site_id': 'OLD-1', 'label': '补测', 'latitude': 1.1, 'longitude': 2.1, 'weight': 4,
                     'surveyed_at': '2026-11-01T00:00:00+00:00'}]
        merged, stats = importing.merge_rows(legacy, incoming)
        self.assertEqual(stats['updated'], ['OLD-1'])
        self.assertEqual(merged[0]['weight'], 4)
        self.assertEqual(merged[0]['surveyed_at'], '2026-11-01T00:00:00+00:00')

    def test_capacity_exceeded_rows_ignored_with_reason(self):
        legacy = [{'site_id': f'YD-{i:04d}', 'label': 'x', 'latitude': 1.0, 'longitude': 2.0,
                   'weight': 1, 'surveyed_at': '2026-11-01T00:00:00+00:00'} for i in range(importing.MAX_ROWS)]
        incoming = [{'site_id': 'YD-NEW', 'label': 'x', 'latitude': 1.0, 'longitude': 2.0,
                     'weight': 1, 'surveyed_at': '2026-11-02T00:00:00+00:00'}]
        merged, stats = importing.merge_rows(legacy, incoming)
        self.assertEqual(len(merged), importing.MAX_ROWS)
        self.assertEqual(stats['ignored'], [{'site_id': 'YD-NEW', 'reason': 'dataset_capacity_exceeded'}])

if __name__ == '__main__':
    unittest.main(verbosity=2)
