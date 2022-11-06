def mock_check_version_true(host, project, timeout):
    return True, 'v1.0.1'


def mock_check_version_false(host, project, timeout):
    return False, 'v1.0.1'
