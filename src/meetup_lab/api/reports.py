from datetime import date

from fastapi import APIRouter, HTTPException, Query

from meetup_lab.reports.registrations import registration_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/registrations")
def get_registration_report(
    event_id: str,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
) -> dict:
    try:
        return registration_report(event_id, from_date, to_date)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
