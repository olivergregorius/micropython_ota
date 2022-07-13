import unittest
from unittest.mock import patch, Mock

import os

import urequests_mock
import sys
sys.modules['machine'] = Mock()

from micropython_ota import micropython_ota


class TestMicropythonOTA(unittest.TestCase):
    def setUp(self) -> None:
        try:
            os.remove('version')
        except OSError:
            pass

    @patch(
        'urequests.urequests.get', urequests_mock.mock_get
    )
    def test_check_version_no_local_version_file(self):
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertTrue(version_changed)
        self.assertEqual(remote_version, 'v1.0.1')

    @patch(
        'urequests.urequests.get', urequests_mock.mock_get
    )
    def test_check_version_with_local_version_matching_remote_version(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.1')
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertFalse(version_changed)
        self.assertEqual(remote_version, 'v1.0.1')

    @patch(
        'urequests.urequests.get', urequests_mock.mock_get
    )
    def test_check_version_with_local_version_not_matching_remote_version(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.0')
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertTrue(version_changed)
        self.assertEqual(remote_version, 'v1.0.1')

    @patch(
        'urequests.urequests.get', urequests_mock.mock_get_OSError
    )
    def test_check_version_remote_host_unavailable(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.0')
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertFalse(version_changed)
        self.assertEqual(remote_version, 'v1.0.0')

    @patch(
        'urequests.urequests.get', urequests_mock.mock_get
    )
    def test_check_version_remote_version_file_not_found(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.0')
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'non_existing')
        self.assertFalse(version_changed)
        self.assertEqual(remote_version, 'v1.0.0')

