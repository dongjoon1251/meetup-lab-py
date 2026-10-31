"""Read-only meetup MCP. Run with Python; optional --transport streamable-http."""
import argparse
import os
import secrets
from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from starlette.responses import JSONResponse

mcp = FastMCP("meetup-lab", host="127.0.0.1", port=8001)
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False)


def _get(path: str, params: dict | None = None):
    base = os.environ.get("MEETUP_API", "http://127.0.0.1:8000").rstrip("/")
    key = os.environ.get("MEETUP_API_KEY", "")
    try:
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            response = client.get(base + path, params=params,
                                  headers={"X-API-Key": key} if key else {})
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code == 401:
            raise ToolError("Meetup API 인증 실패(401). VS Code inputs에서 API 키를 다시 입력하세요. 키를 채팅에 보내지 마세요.") from None
        raise ToolError(f"Meetup API 오류(HTTP {code}). 행사 ID와 날짜 범위를 확인하세요.") from None
    except httpx.RequestError:
        raise ToolError("Meetup API에 연결할 수 없습니다. MEETUP_API와 API 서버 실행 상태를 확인하세요.") from None
    except ValueError:
        raise ToolError("Meetup API 응답이 올바른 JSON 형식이 아닙니다.") from None


@mcp.tool(annotations=READ_ONLY)
def list_events() -> list[dict]:
    """List events and capacities."""
    return _get("/events")


@mcp.tool(annotations=READ_ONLY)
def get_poll_results(event_id: str) -> dict:
    """Get menu vote counts for an event."""
    return _get(f"/events/{quote(event_id, safe='')}/votes/results")


@mcp.tool(annotations=READ_ONLY)
def list_registrations(event_id: str, status: str | None = None) -> list[dict]:
    """List registrations, optionally filtered by CONFIRMED, WAITLISTED or CANCELLED."""
    if status is not None and status not in {"CONFIRMED", "WAITLISTED", "CANCELLED"}:
        raise ToolError("status는 CONFIRMED, WAITLISTED, CANCELLED 중 하나여야 합니다.")
    rows = _get(f"/events/{quote(event_id, safe='')}/registrations")
    return [row for row in rows if status is None or row["status"] == status]


@mcp.tool(annotations=READ_ONLY)
def get_registration_report(event_id: str, from_date: str, to_date: str) -> dict:
    """Get daily registration, cancellation and promotion counts (YYYY-MM-DD)."""
    return _get("/reports/registrations", {"event_id": event_id, "from": from_date, "to": to_date})


class APIKeyMiddleware:
    """Protect every MCP HTTP request, including POST and DELETE."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        key = os.environ.get("MEETUP_API_KEY", "")
        if scope["type"] == "http" and key:
            headers = dict(scope["headers"])
            supplied = headers.get(b"x-api-key", b"")
            if not secrets.compare_digest(supplied, key.encode()):
                await JSONResponse({"detail": "invalid or missing X-API-Key"}, status_code=401)(scope, receive, send)
                return
        await self.app(scope, receive, send)


def http_app():
    app = mcp.streamable_http_app()
    app.add_middleware(APIKeyMiddleware)
    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--http", action="store_true", help="Alias for --transport streamable-http")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args(argv)
    if not os.environ.get("MEETUP_API_KEY"):
        raise SystemExit("MEETUP_API_KEY를 환경변수로 설정한 뒤 MCP 서버를 실행하세요. 키를 파일이나 채팅에 적지 마세요.")
    if args.http or args.transport == "streamable-http":
        import uvicorn
        uvicorn.run(http_app(), host="127.0.0.1", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
