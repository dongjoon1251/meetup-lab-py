import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp.server.fastmcp.exceptions import ToolError

spec = importlib.util.spec_from_file_location('meetup_mcp', Path(__file__).resolve().parents[1] / 'mcp_server/meetup_mcp.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


@pytest.fixture
def mock_http(monkeypatch):
    # Every HTTP request in this module goes through MockTransport, never a socket.
    handler = Mock(return_value=httpx.Response(200, json=[]))
    client_type = httpx.Client
    monkeypatch.setattr(server.httpx, 'Client', lambda **kwargs: client_type(
        transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setenv('MEETUP_API', 'http://mock.invalid')
    monkeypatch.setenv('MEETUP_API_KEY', 'test-only-key')
    return handler


def test_four_readonly_tools():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {'list_events', 'get_poll_results', 'list_registrations', 'get_registration_report'}
    assert all(t.annotations.readOnlyHint for t in tools)


def test_all_tools_use_get_and_key(mock_http):
    assert server.list_events() == []
    mock_http.return_value = httpx.Response(200, json={'event_id': 'EVT-01', 'results': []})
    assert server.get_poll_results('EVT-01')['results'] == []
    assert mock_http.call_args.args[0].url.path == '/events/EVT-01/votes/results'
    mock_http.return_value = httpx.Response(200, json=[{'status': 'WAITLISTED'}, {'status': 'CONFIRMED'}])
    assert server.list_registrations('EVT-01', 'WAITLISTED') == [{'status': 'WAITLISTED'}]
    assert len(server.list_registrations('EVT-01')) == 2
    mock_http.return_value = httpx.Response(200, json={'days': []})
    assert server.get_registration_report('EVT-01', '2026-10-25', '2026-10-26') == {'days': []}
    request = mock_http.call_args.args[0]
    assert dict(request.url.params) == {'event_id': 'EVT-01', 'from': '2026-10-25', 'to': '2026-10-26'}
    assert all(call.args[0].method == 'GET' and call.args[0].headers['X-API-Key'] == 'test-only-key'
               for call in mock_http.call_args_list)


@pytest.mark.parametrize('code', [401, 404, 422, 500])
def test_http_errors_are_tool_errors(mock_http, code):
    mock_http.return_value = httpx.Response(code, text='sensitive upstream body')
    with pytest.raises(ToolError, match=str(code)) as error:
        server.list_events()
    assert 'sensitive' not in str(error.value)
    assert 'test-only-key' not in str(error.value)


def test_connection_and_json_errors(mock_http):
    mock_http.side_effect = httpx.ConnectError('private connection detail')
    with pytest.raises(ToolError, match='연결할 수 없습니다'):
        server.list_events()
    mock_http.side_effect = None
    mock_http.return_value = httpx.Response(200, text='not json')
    with pytest.raises(ToolError, match='JSON 형식'):
        server.list_events()


def test_invalid_status_does_not_call_http(mock_http):
    with pytest.raises(ToolError, match='status'):
        server.list_registrations('EVT-01', 'invalid')
    mock_http.assert_not_called()


@pytest.mark.parametrize('method', ['GET', 'POST', 'DELETE'])
def test_mcp_http_auth(monkeypatch, method):
    monkeypatch.setenv('MEETUP_API_KEY', 'test-only-key')
    monkeypatch.setattr(server, 'mcp', server.FastMCP('auth-test'))
    with TestClient(server.http_app()) as client:
        assert client.request(method, '/mcp').status_code == 401
        assert client.request(method, '/mcp', headers={'X-API-Key': 'wrong'}).status_code == 401
        assert client.request(method, '/mcp', headers={'X-API-Key': 'test-only-key'}).status_code != 401


def test_cli_transports(monkeypatch):
    monkeypatch.setenv("MEETUP_API_KEY", "test-only-key")
    run = Mock()
    monkeypatch.setattr(server.mcp, 'run', run)
    server.main([])
    run.assert_called_once_with(transport='stdio')
    import uvicorn
    http_run = Mock()
    monkeypatch.setattr(uvicorn, 'run', http_run)
    server.main(['--transport', 'streamable-http', '--port', '8001'])
    assert http_run.call_args.kwargs == {'host': '127.0.0.1', 'port': 8001}
    server.main(['--http'])
    assert http_run.call_count == 2


def test_cli_requires_key_before_starting(monkeypatch):
    monkeypatch.delenv("MEETUP_API_KEY", raising=False)
    run = Mock()
    monkeypatch.setattr(server.mcp, "run", run)
    import uvicorn
    http_run = Mock()
    monkeypatch.setattr(uvicorn, "run", http_run)
    for argv in [[], ["--http"], ["--transport", "streamable-http", "--port", "8001"]]:
        with pytest.raises(SystemExit, match="MEETUP_API_KEY"):
            server.main(argv)
    run.assert_not_called()
    http_run.assert_not_called()
