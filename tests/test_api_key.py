import pytest


@pytest.fixture(autouse=True)
def clear_key(monkeypatch):
    monkeypatch.delenv('MEETUP_API_KEY', raising=False)


def test_key_optional(client):
    assert client.get('/events').status_code == 200


@pytest.mark.parametrize('path', ['/events', '/events/EVT-01/menu', '/events/EVT-01/registrations',
                                  '/events/EVT-01/votes/results', '/reports/registrations'])
def test_get_requires_correct_key(client, monkeypatch, path):
    monkeypatch.setenv('MEETUP_API_KEY', 'test-only-key')
    assert client.get(path).status_code == 401
    assert client.get(path, headers={'X-API-Key': 'wrong'}).status_code == 401
    assert client.get(path, headers={'X-API-Key': 'test-only-key'}).status_code != 401


@pytest.mark.parametrize('path', ['/', '/health', '/docs', '/openapi.json', '/static/index.html'])
def test_public_get(client, monkeypatch, path):
    monkeypatch.setenv('MEETUP_API_KEY', 'test-only-key')
    assert client.get(path).status_code == 200


def test_write_requests_work_without_key(client, monkeypatch):
    monkeypatch.setenv('MEETUP_API_KEY', 'test-only-key')
    response = client.post('/events/EVT-01/registrations', json={'member_id': 'M-key-test'})
    assert response.status_code == 201
    assert client.delete('/registrations/' + response.json()['id']).status_code == 200
    assert client.post('/events/EVT-01/votes', json={'voter_id': 'M-key-test', 'option_id': 'MENU-1'}).status_code == 201
