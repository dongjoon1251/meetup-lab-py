"""데모 데이터 입력 — 서버가 떠 있어야 한다 (`python -m uvicorn meetup_lab.app:app --reload`).

    python scripts/seed_demo.py                                    # 투표자 M-01·M-02·M-03 의 투표 3건
    python scripts/seed_demo.py --replay data/samples/waitlist.log # 신청·취소 기록 재생

재생은 각 줄의 시각을 X-Replay-At 헤더로 넘겨 서버가 그 시각으로 기록하게 한다.
투표·신청·취소는 POST·DELETE 라 API 키 없이 동작한다. API 주소는 MEETUP_API(기본 http://127.0.0.1:8000).
"""

import argparse
import os
import sys

import httpx

from meetup_lab.replay_log import read_log

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

API = os.environ.get("MEETUP_API", "http://127.0.0.1:8000")
EVENT_ID = "EVT-01"
DEMO_VOTES = [("M-01", "MENU-1"), ("M-02", "MENU-2"), ("M-03", "MENU-1")]  # 피자 2 · 김밥 1 · 샌드위치 0


def detail(response: httpx.Response) -> str:
    try:
        return str(response.json().get("detail", ""))
    except ValueError:
        return response.text


def seed_votes(client: httpx.Client) -> None:
    for voter_id, option_id in DEMO_VOTES:
        r = client.post(f"/events/{EVENT_ID}/votes", json={"voter_id": voter_id, "option_id": option_id})
        print(f"POST /events/{EVENT_ID}/votes  {voter_id} → {option_id}  {r.status_code} {detail(r) if r.is_error else ''}")

    r = client.get(f"/events/{EVENT_ID}/votes/results")
    if r.status_code == 200:
        print()
        for row in r.json()["results"]:
            print(f"  {row['name']} {row['votes']}")
    else:
        print(f"\n결과는 /docs 의 GET /events/{{event_id}}/votes/results 로 확인하세요 (조회 {r.status_code}).")


def replay(client: httpx.Client, path: str) -> None:
    registration_ids: dict[tuple[str, str], str] = {}  # (event_id, member_id) → 신청 ID
    for line in read_log(path):
        headers = {"X-Replay-At": line.at.isoformat()}
        key = (line.event_id, line.member_id)
        if line.action == "register":
            r = client.post(f"/events/{line.event_id}/registrations", json={"member_id": line.member_id}, headers=headers)
            if r.status_code == 201:
                registration_ids[key] = r.json()["id"]
        else:
            registration_id = registration_ids.get(key)
            if registration_id is None:
                print(f"{line.at.isoformat()} cancel   {line.event_id} {line.member_id}  건너뜀 — 접수된 신청 없음")
                continue
            r = client.delete(f"/registrations/{registration_id}", headers=headers)

        body = r.json() if r.status_code < 300 else {}
        result = f"{body.get('id')} {body.get('status')}" if body else detail(r)
        print(f"{line.at.isoformat()} {line.action:<8} {line.event_id} {line.member_id}  {r.status_code} {result}")


def main() -> int:
    parser = argparse.ArgumentParser(description="meetup-lab 데모 데이터 입력")
    parser.add_argument("--replay", metavar="LOG", help="신청·취소 기록 파일 재생 (예: data/samples/waitlist.log)")
    args = parser.parse_args()

    try:
        with httpx.Client(base_url=API, timeout=10) as client:
            if args.replay:
                replay(client, args.replay)
            else:
                seed_votes(client)
    except httpx.ConnectError:
        print(f"서버에 연결할 수 없습니다: {API}  → 다른 터미널에서 python -m uvicorn meetup_lab.app:app --reload")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
