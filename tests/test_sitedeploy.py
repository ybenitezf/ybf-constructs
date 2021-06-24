import requests
import pytest as pt


@pt.mark.parametrize(
    'url,status', [
        ('https://testsitedeployment.datwit.com', 200),
        ('https://testsitedeployment.datwit.com/index.html', 200),
        ('http://testsitedeployment.datwit.com', 301)
    ]
)
def test_sitedeploy(url, status):
    r = requests.get(url, allow_redirects=False)
    assert r.status_code == status
