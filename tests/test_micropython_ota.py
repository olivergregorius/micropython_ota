import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.modules['machine'] = Mock()
sys.modules['urequests'] = Mock()
sys.modules['uos'] = __import__('os')
sys.modules['ubinascii'] = __import__('binascii')
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

    def test_check_version_with_local_version_matching_remote_version_no_auth(self):
        with open('version', 'w') as current_version_file:
            current_version_file.write('v1.0.1')
        with patch('urequests.get') as urequests_call:
            urequests_call.return_value = urequests_mock.mock_get
            version_changed, remote_version = micropython_ota.check_version('http://example.org', 'sample')
        self.assertFalse(version_changed)
        self.assertEqual(remote_version, 'v1.0.1')
        urequests_call.assert_called_with('http://example.org/sample/version', timeout=5)

    def test_check_version_with_local_version_matching_remote_version_with_auth(self):
        with patch('urequests.get') as urequests_call:
            micropython_ota.check_version('http://example.org', 'sample', auth='aGVsbG86d29ybGQ=')
        urequests_call.assert_called_with('http://example.org/sample/version', headers={'Authorization': 'Basic aGVsbG86d29ybGQ='}, timeout=5)

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
    def test_ota_update_on_version_changed_with_device_hard_reset(self):
        with patch('machine.reset') as machine_reset_call, patch('machine.soft_reset') as machine_soft_reset_call:
            micropython_ota.ota_update('http://example.org', 'sample', ['main.py', 'library.py'])
        with open('version', 'r') as current_version_file:
            self.assertEqual(current_version_file.readline(), 'v1.0.1')
        with open('main.py', 'r') as source_file:
            self.assertEqual(source_file.readline(), 'print("Hello World")')
        with open('library.py', 'r') as source_file:
            self.assertEqual(source_file.readline(), 'print("This is a library")')
        machine_reset_call.assert_called_once()
        machine_soft_reset_call.assert_not_called()

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_ota_update_on_version_changed_with_device_soft_reset(self):
        with patch('machine.reset') as machine_hard_reset_call, patch('machine.soft_reset') as machine_soft_reset_call:
            micropython_ota.ota_update('http://example.org', 'sample', ['main.py', 'library.py'], hard_reset_device=False, soft_reset_device=True)
        with open('version', 'r') as current_version_file:
            self.assertEqual(current_version_file.readline(), 'v1.0.1')
        with open('main.py', 'r') as source_file:
            self.assertEqual(source_file.readline(), 'print("Hello World")')
        with open('library.py', 'r') as source_file:
            self.assertEqual(source_file.readline(), 'print("This is a library")')
        machine_hard_reset_call.assert_not_called()
        machine_soft_reset_call.assert_called_once()

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    def test_ota_update_on_version_changed_with_auth(self):
        with patch('urequests.get') as urequests_call:
            micropython_ota.ota_update('http://example.org', 'sample', ['main.py'], user='hello', passwd='world')
        urequests_call.assert_called_with('http://example.org/sample/v1.0.1_main.py', headers={'Authorization': 'Basic aGVsbG86d29ybGQ='}, timeout=5)

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    def test_ota_update_on_version_changed_no_auth(self):
        with patch('urequests.get') as urequests_call:
            micropython_ota.ota_update('http://example.org', 'sample', ['main.py'])
        urequests_call.assert_called_with('http://example.org/sample/v1.0.1_main.py', timeout=5)

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_ota_update_on_version_changed_with_version_subdirectory_structure(self):
        micropython_ota.ota_update('http://example.org', 'sample', ['main.py', 'library.py'], use_version_prefix=False)
        with open('version', 'r') as current_version_file:
            self.assertEqual(current_version_file.readline(), 'v1.0.1')
        with open('main.py', 'r') as source_file:
            self.assertEqual(source_file.readline(), 'print("Hello Universe")')
        with open('library.py', 'r') as source_file:
            self.assertEqual(source_file.readline(), 'print("This is a very nice library")')

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    @patch(
        'urequests.get', urequests_mock.mock_get
    )
    def test_ota_update_on_version_changed_without_device_reset(self):
        with patch('machine.reset') as machine_hard_reset_call, patch('machine.soft_reset') as machine_soft_reset_call:
            micropython_ota.ota_update('http://example.org', 'sample', ['main.py', 'library.py'], hard_reset_device=False)
        machine_hard_reset_call.assert_not_called()
        machine_soft_reset_call.assert_not_called()

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
        with patch('machine.reset') as machine_hard_reset_call, patch('machine.soft_reset') as machine_soft_reset_call:
            micropython_ota.check_for_ota_update('http://example.org', 'sample')
            machine_hard_reset_call.assert_called_once()
            machine_soft_reset_call.assert_not_called()

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_true
    )
    def test_check_for_ota_update_on_version_changed_with_device_soft_reset(self):
        with patch('machine.reset') as machine_hard_reset_call, patch('machine.soft_reset') as machine_soft_reset_call:
            micropython_ota.check_for_ota_update('http://example.org', 'sample', soft_reset_device=True)
            machine_hard_reset_call.assert_not_called()
            machine_soft_reset_call.assert_called_once()

    @patch(
        'micropython_ota.check_version', micropython_ota_mock.mock_check_version_false
    )
    def test_check_for_ota_update_on_version_not_changed(self):
        with patch('machine.reset') as machine_reset_call, patch('machine.soft_reset') as machine_soft_reset_call:
            micropython_ota.check_for_ota_update('http://example.org', 'sample')
            machine_reset_call.assert_not_called()
            machine_soft_reset_call.assert_not_called()

    def test_generate_auth_user_and_passwd_provided(self):
        auth = micropython_ota.generate_auth(user='hello', passwd='world')
        self.assertEqual('aGVsbG86d29ybGQ=', auth)

    def test_generate_auth_only_user_provided(self):
        with self.assertRaises(ValueError):
            micropython_ota.generate_auth(user='hello')

    def test_generate_auth_only_passwd_provided(self):
        with self.assertRaises(ValueError):
            micropython_ota.generate_auth(passwd='world')

    def test_generate_auth_no_user_and_passwd_provided(self):
        auth = micropython_ota.generate_auth()
        self.assertIsNone(auth)
