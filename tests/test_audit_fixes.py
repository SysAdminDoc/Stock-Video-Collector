import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app


class TagBulkOperationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = app.DB(os.path.join(self.tmp.name, "test.db"))
        for i, tags in enumerate(["nature, sunset", "nature, ocean", "sunset, beach"]):
            self.db.save_clip({
                'clip_id': f'clip_{i}', 'title': f'Clip {i}',
                'source_url': f'https://example.com/{i}',
                'm3u8_url': f'https://example.com/{i}.m3u8',
            })
            self.db.set_user_tags(f'clip_{i}', tags)

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def test_rename_tag(self):
        n = self.db.rename_tag('nature', 'landscape')
        self.assertEqual(n, 2)
        tags = self.db.all_user_tags()
        self.assertIn('landscape', tags)
        self.assertNotIn('nature', tags)

    def test_merge_tags(self):
        n = self.db.merge_tags(['sunset', 'beach'], 'coastal')
        self.assertEqual(n, 2)
        tags = self.db.all_user_tags()
        self.assertIn('coastal', tags)
        self.assertNotIn('beach', tags)

    def test_split_tag(self):
        n = self.db.split_tag('nature', ['flora', 'fauna'])
        self.assertEqual(n, 2)
        tags = self.db.all_user_tags()
        self.assertIn('flora', tags)
        self.assertIn('fauna', tags)
        self.assertNotIn('nature', tags)

    def test_like_wildcard_in_tag_name(self):
        self.db.save_clip({
            'clip_id': 'clip_pct', 'title': 'Pct', 'source_url': 'x', 'm3u8_url': 'x',
        })
        self.db.set_user_tags('clip_pct', 'special%tag')
        n = self.db.rename_tag('special%tag', 'safe_tag')
        self.assertEqual(n, 1)
        row = self.db.execute("SELECT user_tags FROM clips WHERE clip_id='clip_pct'").fetchone()
        self.assertEqual(row['user_tags'], 'safe_tag')
        row0 = self.db.execute("SELECT user_tags FROM clips WHERE clip_id='clip_0'").fetchone()
        self.assertIn('nature', row0['user_tags'])


class CollectionLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = app.DB(os.path.join(self.tmp.name, "test.db"))
        self.db.save_clip({
            'clip_id': 'c1', 'title': 'C1', 'source_url': 'x', 'm3u8_url': 'x',
        })
        self.coll_id = self.db.create_collection("Portfolio")

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def test_add_to_unlocked_collection(self):
        result = self.db.add_to_collection('c1', self.coll_id)
        self.assertTrue(result)

    def test_lock_prevents_add(self):
        self.db.toggle_collection_lock(self.coll_id)
        self.assertTrue(self.db.is_collection_locked(self.coll_id))
        result = self.db.add_to_collection('c1', self.coll_id)
        self.assertFalse(result)

    def test_lock_prevents_remove(self):
        self.db.add_to_collection('c1', self.coll_id)
        self.db.toggle_collection_lock(self.coll_id)
        result = self.db.remove_from_collection('c1', self.coll_id)
        self.assertFalse(result)

    def test_unlock_allows_operations(self):
        self.db.toggle_collection_lock(self.coll_id)
        self.db.toggle_collection_lock(self.coll_id)
        self.assertFalse(self.db.is_collection_locked(self.coll_id))
        result = self.db.add_to_collection('c1', self.coll_id)
        self.assertTrue(result)


class PriorityQueueTests(unittest.TestCase):
    def test_priority_ordering(self):
        import queue
        q = queue.PriorityQueue()
        q.put((app.DownloadWorker.PRIORITY_LOW, 1, {'clip_id': 'low'}))
        q.put((app.DownloadWorker.PRIORITY_HIGH, 2, {'clip_id': 'high'}))
        q.put((app.DownloadWorker.PRIORITY_NORMAL, 3, {'clip_id': 'normal'}))
        first = q.get()
        self.assertEqual(first[2]['clip_id'], 'high')
        second = q.get()
        self.assertEqual(second[2]['clip_id'], 'normal')
        third = q.get()
        self.assertEqual(third[2]['clip_id'], 'low')

    def test_same_priority_preserves_order(self):
        import queue
        q = queue.PriorityQueue()
        for i in range(5):
            q.put((app.DownloadWorker.PRIORITY_NORMAL, i, {'clip_id': f'clip_{i}'}))
        for i in range(5):
            item = q.get()
            self.assertEqual(item[2]['clip_id'], f'clip_{i}')


class BandwidthScheduleTests(unittest.TestCase):
    def test_none_schedule_allows_always(self):
        worker = app.DownloadWorker.__new__(app.DownloadWorker)
        worker._bw_schedule = 'none'
        allowed, throttle = worker._check_bw_schedule()
        self.assertTrue(allowed)
        self.assertEqual(throttle, 0)

    def test_unknown_schedule_allows(self):
        worker = app.DownloadWorker.__new__(app.DownloadWorker)
        worker._bw_schedule = 'unknown_value'
        allowed, throttle = worker._check_bw_schedule()
        self.assertTrue(allowed)

    def test_nights_only_blocks_during_day(self):
        worker = app.DownloadWorker.__new__(app.DownloadWorker)
        worker._bw_schedule = 'nights_only'
        with patch('artlist_scraper.datetime') as mock_dt:
            mock_dt.now.return_value = type('DT', (), {'hour': 12, 'strftime': lambda s, f: ''})()
            allowed, throttle = worker._check_bw_schedule()
            self.assertFalse(allowed)

    def test_nights_only_allows_at_night(self):
        worker = app.DownloadWorker.__new__(app.DownloadWorker)
        worker._bw_schedule = 'nights_only'
        with patch('artlist_scraper.datetime') as mock_dt:
            mock_dt.now.return_value = type('DT', (), {'hour': 23, 'strftime': lambda s, f: ''})()
            allowed, throttle = worker._check_bw_schedule()
            self.assertTrue(allowed)

    def test_throttle_day_returns_kbps_during_hours(self):
        worker = app.DownloadWorker.__new__(app.DownloadWorker)
        worker._bw_schedule = 'throttle_day'
        with patch('artlist_scraper.datetime') as mock_dt:
            mock_dt.now.return_value = type('DT', (), {'hour': 12, 'strftime': lambda s, f: ''})()
            allowed, throttle = worker._check_bw_schedule()
            self.assertTrue(allowed)
            self.assertEqual(throttle, 500)

    def test_throttle_day_no_limit_outside_hours(self):
        worker = app.DownloadWorker.__new__(app.DownloadWorker)
        worker._bw_schedule = 'throttle_day'
        with patch('artlist_scraper.datetime') as mock_dt:
            mock_dt.now.return_value = type('DT', (), {'hour': 22, 'strftime': lambda s, f: ''})()
            allowed, throttle = worker._check_bw_schedule()
            self.assertTrue(allowed)
            self.assertEqual(throttle, 0)

    def test_throttle_biz_returns_200_kbps(self):
        worker = app.DownloadWorker.__new__(app.DownloadWorker)
        worker._bw_schedule = 'throttle_biz'
        with patch('artlist_scraper.datetime') as mock_dt:
            mock_dt.now.return_value = type('DT', (), {'hour': 14, 'strftime': lambda s, f: ''})()
            allowed, throttle = worker._check_bw_schedule()
            self.assertTrue(allowed)
            self.assertEqual(throttle, 200)


class FtsQuerySafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = app.DB(os.path.join(self.tmp.name, "test.db"))
        self.db.save_clip({
            'clip_id': 'c1', 'title': 'Beautiful sunset', 'source_url': 'x',
            'm3u8_url': 'x', 'creator': 'John',
        })

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def test_search_with_double_quotes_does_not_crash(self):
        results = self.db.search_assets(query='test"injection')
        self.assertIsNotNone(results)

    def test_search_with_special_fts_chars(self):
        for q in ['*', '+', '-', '^', 'test OR DROP']:
            results = self.db.search_assets(query=q)
            self.assertIsNotNone(results)

    def test_normal_search_still_works(self):
        results = self.db.search_assets(query='sunset')
        self.assertTrue(len(results) > 0)


class SavedSearchFeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = app.DB(os.path.join(self.tmp.name, "test.db"))

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def test_update_saved_search_count(self):
        self.db.save_search("test", "sunset", "{}")
        searches = self.db.get_saved_searches()
        sid = searches[0]['id']
        self.db.update_saved_search_count(sid, 42)
        s = self.db.get_saved_search_by_id(sid)
        self.assertEqual(s['last_count'], 42)
        self.assertTrue(s['last_run_at'])


class XmlExportSafetyTests(unittest.TestCase):
    def test_xml_special_chars_in_title(self):
        import xml.etree.ElementTree as ET
        root = ET.Element('test')
        ET.SubElement(root, 'title').text = 'Clip <with> "special" & chars'
        xml_str = ET.tostring(root, encoding='unicode')
        self.assertIn('&lt;', xml_str)
        self.assertIn('&amp;', xml_str)


if __name__ == "__main__":
    unittest.main()
