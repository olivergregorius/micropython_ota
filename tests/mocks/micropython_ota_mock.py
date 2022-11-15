def mock_check_version_true(host, project, auth, timeout):
    return True, 'v1.0.1'


def mock_check_version_false(host, project, auth, timeout):
    return False, 'v1.0.1'
