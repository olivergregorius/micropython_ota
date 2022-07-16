import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.modules['machine'] = Mock()
sys.modules['urequests'] = Mock()
sys.modules['uos'] = __import__('os')
import micropython_ota
from mocks import micropython_ota_mock, urequests_mock


class TestMicropythonOTA(unittest.TestCase):
    def tearDown(self) -> None:
        for filename in ['version', 'main.py', 'library.py']:
            try:
                os.remove(filename)
            except OSError:
                pass

    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_check_version_no_local_version_file(self):
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertTrue(version_changed)
        self.assertEqual(remote_version, 'v1.0.1')

    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_check_version_with_local_version_matching_remote_version(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.1')
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertFalse(version_changed)
        self.assertEqual(remote_version, 'v1.0.1')

    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_check_version_with_local_version_not_matching_remote_version(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.0')
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertTrue(version_changed)
        self.assertEqual(remote_version, 'v1.0.1')

    @patch(
        'urequests.get', urequests_mock.mock_get_OSError
    )
    def test_check_version_remote_host_unavailable(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.0')
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertFalse(version_changed)
        self.assertEqual(remote_version, 'v1.0.0')

    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_check_version_remote_version_file_not_found(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.0')
        version_changed, remote_version = micropython_ota.check_version('http://example.org', 'non_existing')
        self.assertFalse(version_changed)
        self.assertEqual(remote_version, 'v1.0.0')

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_ota_update_on_version_changed(self):
        micropython_ota.ota_update('http://example.org', 'sample', ['main.py', 'library.py'])
        with open('version', 'r') as current_version_file:
            self.assertEqual(current_version_file.readline(), 'v1.0.1')
        with open('main.py', 'r') as source_file:
            self.assertEqual(source_file.readline(), 'print("Hello World")')
        with open('library.py', 'r') as source_file:
            self.assertEqual(source_file.readline(), 'print("This is a library")')

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_false
    )
    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_ota_update_on_version_not_changed(self):
        micropython_ota.ota_update('http://example.org', 'sample', ['main.py', 'library.py'])
        # For this test to pass the files 'version', 'main.py' and 'library.py' must not have been created because no update is needed
        self.assertFalse('version' in os.listdir())
        self.assertFalse('main.py' in os.listdir())
        self.assertFalse('library.py' in os.listdir())

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    @patch(
        'urequests.get', urequests_mock.mock_get_OSError
    )
    def test_ota_update_host_unavailable(self):
        micropython_ota.ota_update('http://example.org', 'sample', ['main.py', 'library.py'])
        # For this test to pass the files 'version', 'main.py' and 'library.py' must not have been created because no update is needed
        self.assertFalse('version' in os.listdir())
        self.assertFalse('main.py' in os.listdir())

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_ota_update_source_file_not_found(self):
        micropython_ota.ota_update('http://example.org', 'non_existing', ['main.py', 'library.py'])
        # For this test to pass the files 'version', 'main.py' and 'library.py' must not have been created because no update is needed
        self.assertFalse('version' in os.listdir())
        self.assertFalse('main.py' in os.listdir())
        self.assertFalse('library.py' in os.listdir())

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    def test_check_for_ota_update_on_version_changed(self):
        with patch('machine.reset') as machine_reset_call:
            micropython_ota.check_for_ota_update('http://example.org', 'sample')
            machine_reset_call.assert_called_once()

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_false
    )
    def test_check_for_ota_update_on_version_not_changed(self):
        with patch('machine.reset') as machine_reset_call:
            micropython_ota.check_for_ota_update('http://example.org', 'sample')
            machine_reset_call.assert_not_called()
