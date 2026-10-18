import importlib.util
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location('profile_stats', Path(__file__).with_name('update-profile-stats.py'))
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


class ProfileStatsTest(unittest.TestCase):
    def test_zero_activity_renders_valid_svg_with_date_and_metrics(self):
        user = {'repositories': {'totalCount': 12}, 'followers': {'totalCount': 3},
                'contributionsCollection': {'startedAt': '2025-10-18T00:00:00Z',
                                            'endedAt': '2026-10-18T00:00:00Z',
                                            'totalCommitContributions': 0,
                                            'totalPullRequestContributions': 0}}
        svg = stats.render_stats(user, datetime(2026, 10, 18, tzinfo=timezone.utc))
        root = ET.fromstring(svg)
        texts = [node.text for node in root.findall('{http://www.w3.org/2000/svg}text')]
        self.assertIn('12', texts)
        self.assertEqual(texts.count('0'), 2)
        self.assertIn('UPDATED 2026-10-18 00:00 UTC', svg)
        compact = ET.fromstring(stats.render_stats(user, datetime.now(timezone.utc), compact=True))
        self.assertEqual(compact.attrib['viewBox'], '0 0 640 400')
        values = [node for node in compact.findall('{http://www.w3.org/2000/svg}text') if node.get('font-weight') == '700']
        self.assertEqual({(node.get('x'), node.get('y')) for node in values},
                         {('32', '115'), ('322', '115'), ('32', '235'), ('322', '235')})
        user['followers']['totalCount'] = -1
        with self.assertRaises(ValueError):
            stats.render_stats(user, datetime.now(timezone.utc))


if __name__ == '__main__':
    unittest.main()
