class MockedResponse:
    def __init__(self, url):
        self.url = url
        self.status_code = MockedUrls[url][0]
        self.text = MockedUrls[url][1]


MockedUrls = {
    'http://example.org/sample_version': (200, 'v1.0.1'),
    'http://example.org/non_existing_version': (404, '<html><head><title>404 Not Found</title></head><body><center><h1>404 Not Found</h1></center><hr><center>nginx/1.23.0</center></body></html>')
}


def mock_get(url, params={}, **kwargs):
    return MockedResponse(url)


def mock_get_OSError(url, params={}, **kwargs):
    raise OSError('No route to host')
