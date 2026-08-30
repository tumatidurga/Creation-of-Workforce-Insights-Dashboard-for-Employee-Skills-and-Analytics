import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.app.database import get_database

logger = logging.getLogger("uvicorn.error")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_emp_id(doc: Dict[str, Any]) -> Optional[str]:
    return (
        doc.get("empId")
        or doc.get("EmpID")
        or doc.get("EmpId")
        or doc.get("employeeId")
        or doc.get("EmployeeID")
    )


def _safe_date_value(doc: Dict[str, Any]) -> Optional[str]:
    return doc.get("Date") or doc.get("date") or doc.get("ShiftDate") or doc.get("requestedDate")


def _safe_checkin_value(doc: Dict[str, Any]) -> Optional[str]:
    return doc.get("CheckIn") or doc.get("checkIn")


def _coerce_datetime_utc(value: Any, default_date: Optional[str] = None) -> Optional[datetime]:
    if value is None or value in ("", "N/A", "--:--", "None", "null"):
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        if isinstance(value, datetime):
            dt = value
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        if "T" in text or text.endswith("Z"):
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        if ":" in text:
            if ":" in text and len(text.split(":")) == 2:
                base = datetime.strptime(default_date or "2020-01-01", "%Y-%m-%d").date() if default_date else datetime(2020, 1, 1).date()
                hh, mm = map(int, text.split(":")[:2])
                return datetime.combine(base, datetime.strptime(f"{hh:02d}:{mm:02d}", "%H:%M").time()).replace(tzinfo=timezone.utc)
            parsed = datetime.strptime(text, "%H:%M:%S")
            base = datetime.strptime(default_date or "2020-01-01", "%Y-%m-%d").date() if default_date else datetime(2020, 1, 1).date()
            return datetime.combine(base, parsed.time()).replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    try:
        parsed_date = datetime.strptime(text, "%Y-%m-%d")
        return parsed_date.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_clock_time(value: Any) -> Optional[datetime]:
    return _coerce_datetime_utc(value)


def _time_to_minutes(value: Any) -> Optional[int]:
    dt = _coerce_datetime_utc(value)
    if dt is None:
        return None
    return dt.hour * 60 + dt.minute


def _combine_attendance_datetime(date_value: Optional[str], time_value: Any) -> Optional[datetime]:
    if time_value is None:
        return None
    if isinstance(time_value, datetime):
        dt = _coerce_datetime_utc(time_value)
        if dt is None:
            return None
        if date_value is None:
            return dt
        try:
            parsed_date = datetime.strptime(str(date_value), "%Y-%m-%d").date()
            return datetime.combine(parsed_date, dt.time()).replace(tzinfo=timezone.utc)
        except ValueError:
            return dt
    if date_value is None:
        return _coerce_datetime_utc(time_value)
    return _coerce_datetime_utc(time_value, default_date=str(date_value))


def _shift_duration_minutes(start_minutes: int, end_minutes: int) -> int:
    delta = end_minutes - start_minutes
    if delta < 0:
        delta += 24 * 60
    return max(delta, 0)


async def _get_shift_window(db: Any, emp_id: str, attendance_date: str) -> Optional[Tuple[Optional[int], Optional[int], Optional[str]]]:
    if db is None or not emp_id:
        return None
    shift_query = {
        "$or": [
            {"EmpID": emp_id, "ShiftDate": attendance_date},
            {"EmpID": emp_id, "Date": attendance_date},
            {"EmpID": emp_id, "requestedDate": attendance_date},
        ]
    }
    shift_doc = await db.shifts.find_one(shift_query)
    if not shift_doc:
        return None
    start_val = shift_doc.get("ShiftStart") or shift_doc.get("shiftStart")
    end_val = shift_doc.get("ShiftEnd") or shift_doc.get("shiftEnd")
    start_minutes = _time_to_minutes(start_val)
    end_minutes = _time_to_minutes(end_val)
    if start_minutes is None or end_minutes is None:
        return None
    shift_name = shift_doc.get("ShiftName") or shift_doc.get("shiftName") or "shift"
    return start_minutes, end_minutes, shift_name


async def _get_employee_status(db: Any, emp_id: Optional[str]) -> Optional[str]:
    if db is None or not emp_id:
        return None
    employee = await db.employees.find_one({"EmpID": emp_id}, {"_id": 0})
    if not employee:
        return None
    return employee.get("EmploymentStatus") or employee.get("status")


def _get_leave_request_timestamp(doc: Dict[str, Any]) -> Optional[datetime]:
    for key in ("submittedAt", "submitted_at", "requestedAt", "requested_at", "requestDate", "requestedDate", "createdAt", "created_at", "appliedAt", "applied_at"):
        value = doc.get(key)
        if value in (None, "", "N/A"):
            continue
        try:
            if isinstance(value, datetime):
                dt = value
            elif "T" in str(value) or str(value).endswith("Z"):
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(str(value), "%Y-%m-%d")
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    start_date = doc.get("StartDate") or doc.get("startDate")
    if not start_date:
        return None
    try:
        start_dt = datetime.strptime(str(start_date), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if start_dt <= datetime.now(timezone.utc):
            return start_dt
    except ValueError:
        pass
    return None


async def _bulk_existing_event_keys(db: Any, event_keys: List[str]) -> set:
    existing = set()
    if db is None or not event_keys:
        return existing

    unique_keys = []
    seen = set()
    for key in event_keys:
        if key and key not in seen:
            unique_keys.append(key)
            seen.add(key)
    if not unique_keys:
        return existing

    if hasattr(db, "audit_logs"):
        existing.update(await db.audit_logs.distinct("AutomationEventKey", {"AutomationEventKey": {"$in": unique_keys}}))
    if hasattr(db, "notifications"):
        existing.update(await db.notifications.distinct("AutomationEventKey", {"AutomationEventKey": {"$in": unique_keys}}))
    return existing


async def _write_automation_event(
    db: Any,
    *,
    event_key: str,
    event_type: str,
    emp_id: Optional[str],
    attendance_date: Optional[str],
    severity: str,
    description: str,
    employee_message: Optional[str],
    hr_message: Optional[str] = None,
    status: str = "SUCCESS",
) -> Dict[str, int]:
    created = {"audit": 0, "employee_notification": 0, "hr_notification": 0}
    if db is None:
        return created

    if hasattr(db, "audit_logs"):
        audit_existing = await db.audit_logs.find_one({"AutomationEventKey": event_key})
        if not audit_existing:
            await db.audit_logs.insert_one({
                "actor": "AutomationEngine",
                "action": event_type,
                "module": "Automation",
                "ipAddress": "127.0.0.1",
                "status": status,
                "severity": severity,
                "description": description,
                "employeeId": emp_id,
                "attendanceDate": attendance_date,
                "AutomationEventKey": event_key,
                "timestamp": _utc_now_iso(),
            })
            created["audit"] = 1

    if hasattr(db, "notifications"):
        if emp_id and employee_message:
            employee_existing = await db.notifications.find_one({
                "AutomationEventKey": event_key,
                "NotificationScope": "employee",
            })
            if not employee_existing:
                await db.notifications.insert_one({
                    "EmpID": emp_id,
                    "Type": "Attendance",
                    "Message": employee_message,
                    "Status": "Unread",
                    "NotificationDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "AutomationEventKey": event_key,
                    "NotificationScope": "employee",
                    "priority": severity.upper(),
                })
                created["employee_notification"] = 1

        if hr_message:
            hr_existing = await db.notifications.find_one({
                "AutomationEventKey": event_key,
                "NotificationScope": "hr",
            })
            if not hr_existing:
                await db.notifications.insert_one({
                    "Type": "HR",
                    "Message": hr_message,
                    "Status": "Unread",
                    "NotificationDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "AutomationEventKey": event_key,
                    "NotificationScope": "hr",
                    "priority": severity.upper(),
                    "employeeId": emp_id,
                })
                created["hr_notification"] = 1

    return created


async def attendance_reconciliation_job():
    """Attendance reconciliation job.

    Scans recent attendance records and collects findings for:
      - missing checkout
      - suspicious zero-hour present records
      - late arrivals
      - inconsistent working hours
      - malformed/missing fields

    This job is read-only and will not modify attendance documents.
    Findings are logged and an audit record is emitted to audit_logs collection if available.
    Returns a summary dict.
    """
    start_ts = time.time()
    started_at = _utc_now_iso()
    findings: List[Dict[str, Any]] = []
    scanned = 0

    try:
        db = get_database()
        if db is None:
            logger.warning("[Automation] attendance_reconciliation: No database available")
            return {
                "job_name": "attendance_reconciliation",
                "started_at": started_at,
                "finished_at": _utc_now_iso(),
                "status": "NO_DB",
                "duration_ms": int((time.time() - start_ts) * 1000),
                "records_scanned": 0,
                "findings_count": 0,
            }

        today = datetime.utcnow().date()
        min_date = (today - timedelta(days=2)).isoformat()

        query = {
            "$and": [
                {"$or": [{"CheckIn": {"$exists": True}}, {"checkIn": {"$exists": True}}, {"CheckIn": {"$ne": None}}]},
                {"$or": [
                    {"CheckOut": {"$exists": False}},
                    {"CheckOut": None},
                    {"CheckOut": ""},
                    {"CheckOut": "N/A"},
                    {"checkOut": {"$exists": False}},
                    {"checkOut": None},
                ]},
                {"$or": [
                    {"Date": {"$gte": min_date}},
                    {"date": {"$gte": min_date}},
                ]}
            ]
        }

        cursor = db.attendance.find(query)
        docs = await cursor.to_list(length=1000)
        scanned = len(docs)

        for doc in docs:
            try:
                emp_id = _safe_emp_id(doc)
                date = str(_safe_date_value(doc) or "")
                check_in = _safe_checkin_value(doc)
                check_out = doc.get("CheckOut") or doc.get("checkOut") or None
                working_hours = doc.get("WorkingHours") or doc.get("workingHours") or doc.get("working_hours") or None
                late_flag = doc.get("LateArrival") or doc.get("lateArrival") or False

                record_findings = []

                if check_in and (not check_out or str(check_out).strip().upper() == "N/A"):
                    record_findings.append({"type": "missing_checkout", "message": "CheckOut missing or N/A"})

                try:
                    wh_val = float(working_hours) if working_hours is not None else None
                except Exception:
                    wh_val = None

                if check_in and (wh_val == 0 or wh_val == 0.0):
                    record_findings.append({"type": "suspicious_zero_hours", "message": "WorkingHours is zero despite CheckIn present"})

                is_late = False
                if late_flag is True:
                    is_late = True
                else:
                    if isinstance(check_in, str) and ":" in check_in:
                        try:
                            hh_mm = check_in.split(":")
                            hh = int(hh_mm[0])
                            mm = int(hh_mm[1])
                            if hh > 9 or (hh == 9 and mm > 30):
                                is_late = True
                        except Exception:
                            pass
                if is_late:
                    record_findings.append({"type": "late_arrival", "message": "Late arrival detected"})

                if check_in and check_out and wh_val is not None:
                    try:
                        t_in = None
                        t_out = None
                        if isinstance(check_in, str) and ":" in check_in:
                            ih, im = map(int, check_in.split(":")[:2])
                            t_in = ih + im / 60.0
                        if isinstance(check_out, str) and ":" in check_out:
                            oh, om = map(int, check_out.split(":")[:2])
                            t_out = oh + om / 60.0

                        if t_in is not None and t_out is not None:
                            calc_hours = max(0.0, t_out - t_in)
                            if abs(calc_hours - wh_val) > 0.5:
                                record_findings.append({"type": "inconsistent_working_hours", "message": f"Computed {calc_hours:.2f}h vs WorkingHours {wh_val}"})
                    except Exception:
                        pass

                if not emp_id or not date or not check_in:
                    record_findings.append({"type": "malformed", "message": "Missing empId/date/checkIn"})

                if record_findings:
                    findings.append({
                        "emp_id": emp_id,
                        "date": date,
                        "record_id": str(doc.get("_id")),
                        "findings": record_findings,
                    })
            except Exception as e:
                logger.exception(f"Error analysing attendance doc {doc.get('_id')}: {e}")

        try:
            summary = {
                "job_name": "attendance_reconciliation",
                "started_at": started_at,
                "finished_at": _utc_now_iso(),
                "status": "COMPLETED",
                "duration_ms": int((time.time() - start_ts) * 1000),
                "records_scanned": scanned,
                "findings_count": len(findings),
            }
            if hasattr(db, "audit_logs"):
                audit_doc = {
                    "actor": "AutomationEngine",
                    "action": "attendance_reconciliation",
                    "module": "Automation",
                    "status": "SUCCESS",
                    "details": summary,
                    "timestamp": _utc_now_iso(),
                }
                try:
                    await db.audit_logs.insert_one(audit_doc)
                except Exception:
                    logger.exception("Failed to write audit log for automation job")

            logger.info(f"[Automation] attendance_reconciliation completed records_scanned={scanned} findings={len(findings)}")

            return {
                "job_name": "attendance_reconciliation",
                "started_at": started_at,
                "finished_at": _utc_now_iso(),
                "status": "COMPLETED",
                "duration_ms": int((time.time() - start_ts) * 1000),
                "records_scanned": scanned,
                "findings_count": len(findings),
                "findings_sample": findings[:25],
            }
        except Exception as e:
            logger.exception(f"attendance_reconciliation job failed: {e}")
            return {
                "job_name": "attendance_reconciliation",
                "started_at": started_at,
                "finished_at": _utc_now_iso(),
                "status": "FAILED",
                "duration_ms": int((time.time() - start_ts) * 1000),
                "records_scanned": scanned,
                "findings_count": len(findings),
                "error": str(e),
            }
    except Exception as ex:
        logger.exception(f"attendance_reconciliation job unexpected error: {ex}")
        return {
            "job_name": "attendance_reconciliation",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "status": "FAILED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "records_scanned": scanned,
            "findings_count": len(findings),
            "error": str(ex),
        }


async def missing_checkout_detection_job() -> Dict[str, Any]:
    """Create a single attendance anomaly event when an employee has checked in but not checked out past the expected shift window."""
    start_ts = time.time()
    started_at = _utc_now_iso()
    db = get_database()
    events_detected = 0
    created = {"audit": 0, "employee_notification": 0, "hr_notification": 0}

    if db is None:
        return {"job_name": "missing_checkout_detection", "status": "NO_DB", "started_at": started_at, "finished_at": _utc_now_iso(), "events_detected": 0}

    try:
        attendance_docs = await db.attendance.find({
            "CheckIn": {"$exists": True, "$ne": None, "$ne": ""},
            "CheckOut": {"$in": [None, "", "N/A", "--:--"]},
        }).to_list(length=2000)

        relevant_emp_ids = {doc.get("EmpID") or doc.get("empId") for doc in attendance_docs if doc.get("EmpID") or doc.get("empId")}
        employee_status_map = {}
        if relevant_emp_ids:
            employee_docs = await db.employees.find(
                {"EmpID": {"$in": sorted(relevant_emp_ids)}},
                {"_id": 0, "EmpID": 1, "EmploymentStatus": 1, "status": 1},
            ).to_list(length=None)
            for employee_doc in employee_docs:
                emp_id = employee_doc.get("EmpID")
                if emp_id:
                    employee_status_map[emp_id] = employee_doc.get("EmploymentStatus") or employee_doc.get("status")

        shift_cache = {}
        if relevant_emp_ids:
            shift_docs = await db.shifts.find(
                {"EmpID": {"$in": sorted(relevant_emp_ids)}},
                {"_id": 0, "EmpID": 1, "ShiftDate": 1, "Date": 1, "requestedDate": 1, "ShiftStart": 1, "shiftStart": 1, "ShiftEnd": 1, "shiftEnd": 1, "ShiftName": 1, "shiftName": 1},
            ).to_list(length=None)
            for shift_doc in shift_docs:
                shift_emp_id = shift_doc.get("EmpID")
                if not shift_emp_id:
                    continue
                for date_field in ("ShiftDate", "Date", "requestedDate"):
                    date_value = shift_doc.get(date_field)
                    if date_value is None:
                        continue
                    shift_cache[(str(shift_emp_id), str(date_value))] = shift_doc

        for doc in attendance_docs:
            emp_id = _safe_emp_id(doc)
            attendance_date = _safe_date_value(doc)
            check_in = _safe_checkin_value(doc)
            if not emp_id or not attendance_date or not check_in:
                continue

            status_value = employee_status_map.get(emp_id)
            if status_value and str(status_value).strip().lower() not in {"active", "working", "on duty"}:
                continue

            expected_duration_hours = 8.0
            shift_doc = shift_cache.get((emp_id, attendance_date))
            if shift_doc:
                start_val = shift_doc.get("ShiftStart") or shift_doc.get("shiftStart")
                end_val = shift_doc.get("ShiftEnd") or shift_doc.get("shiftEnd")
                start_minutes = _time_to_minutes(start_val)
                end_minutes = _time_to_minutes(end_val)
                if start_minutes is not None and end_minutes is not None:
                    shift_delta_minutes = _shift_duration_minutes(start_minutes, end_minutes)
                    if shift_delta_minutes > 0:
                        expected_duration_hours = max(shift_delta_minutes / 60.0, 0.5)

            check_in_dt = _combine_attendance_datetime(attendance_date, check_in)
            if check_in_dt is None:
                continue

            elapsed_hours = (datetime.now(timezone.utc) - check_in_dt).total_seconds() / 3600.0
            if elapsed_hours < expected_duration_hours:
                continue

            event_key = f"{emp_id}:{attendance_date}:missing_checkout"
            employee_message = (
                f"Your attendance record for {attendance_date} has no checkout yet. Please review your attendance."
            )
            hr_message = (
                f"Employee {emp_id} attendance record for {attendance_date} requires checkout review."
            )
            event_result = await _write_automation_event(
                db,
                event_key=event_key,
                event_type="missing_checkout",
                emp_id=emp_id,
                attendance_date=attendance_date,
                severity="warning",
                description="Missing checkout was detected after the expected shift window elapsed.",
                employee_message=employee_message,
                hr_message=hr_message,
                status="SUCCESS",
            )
            created["audit"] += event_result["audit"]
            created["employee_notification"] += event_result["employee_notification"]
            created["hr_notification"] += event_result["hr_notification"]
            if any(event_result.values()):
                events_detected += 1

        result = {
            "job_name": "missing_checkout_detection",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "status": "COMPLETED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "events_detected": events_detected,
            "created": created,
        }
        logger.info("[Automation] missing_checkout_detection completed events_detected=%s", events_detected)
        return result
    except Exception as exc:
        logger.exception("missing_checkout_detection failed: %s", exc)
        return {
            "job_name": "missing_checkout_detection",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "status": "FAILED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "events_detected": events_detected,
            "created": created,
            "error": str(exc),
        }


async def late_arrival_detection_job() -> Dict[str, Any]:
    """Create late-arrival alerts only when a shift start exists and the actual check-in is later than expected."""
    start_ts = time.time()
    started_at = _utc_now_iso()
    db = get_database()
    events_detected = 0
    created = {"audit": 0, "employee_notification": 0, "hr_notification": 0}

    if db is None:
        return {"job_name": "late_arrival_detection", "status": "NO_DB", "started_at": started_at, "finished_at": _utc_now_iso(), "events_detected": 0}

    try:
        cutoff_date = (datetime.now(timezone.utc).date() - timedelta(days=14)).isoformat()
        attendance_docs = await db.attendance.find({
            "CheckIn": {"$exists": True, "$ne": None, "$ne": ""},
            "$or": [
                {"Date": {"$gte": cutoff_date}},
                {"date": {"$gte": cutoff_date}},
                {"ShiftDate": {"$gte": cutoff_date}},
                {"requestedDate": {"$gte": cutoff_date}},
            ],
        }).to_list(length=2000)

        relevant_emp_ids = {doc.get("EmpID") or doc.get("empId") for doc in attendance_docs if doc.get("EmpID") or doc.get("empId")}
        shift_cache = {}
        if relevant_emp_ids:
            shift_docs = await db.shifts.find(
                {"EmpID": {"$in": sorted(relevant_emp_ids)}},
                {"_id": 0, "EmpID": 1, "ShiftDate": 1, "Date": 1, "requestedDate": 1, "ShiftStart": 1, "shiftStart": 1, "ShiftEnd": 1, "shiftEnd": 1, "ShiftName": 1, "shiftName": 1},
            ).to_list(length=None)
            for shift_doc in shift_docs:
                shift_emp_id = shift_doc.get("EmpID")
                if not shift_emp_id:
                    continue
                for date_field in ("ShiftDate", "Date", "requestedDate"):
                    date_value = shift_doc.get(date_field)
                    if date_value is None:
                        continue
                    shift_cache[(str(shift_emp_id), str(date_value))] = shift_doc

        candidate_event_keys = []
        for doc in attendance_docs:
            emp_id = _safe_emp_id(doc)
            attendance_date = _safe_date_value(doc)
            check_in = _safe_checkin_value(doc)
            if not emp_id or not attendance_date or not check_in:
                continue
            if doc.get("LateArrival") is True or doc.get("lateArrival") is True:
                continue
            shift_doc = shift_cache.get((emp_id, attendance_date))
            if not shift_doc:
                continue
            shift_start_val = shift_doc.get("ShiftStart") or shift_doc.get("shiftStart")
            shift_start = _time_to_minutes(shift_start_val)
            if shift_start is None:
                continue
            actual_dt = _combine_attendance_datetime(attendance_date, check_in)
            if actual_dt is None:
                continue
            actual_minutes = actual_dt.hour * 60 + actual_dt.minute
            if actual_minutes <= shift_start + 15:
                continue
            candidate_event_keys.append(f"{emp_id}:{attendance_date}:late_arrival")

        existing_event_keys = await _bulk_existing_event_keys(db, candidate_event_keys)
        seen_event_keys = set(existing_event_keys)

        for doc in attendance_docs:
            emp_id = _safe_emp_id(doc)
            attendance_date = _safe_date_value(doc)
            check_in = _safe_checkin_value(doc)
            if not emp_id or not attendance_date or not check_in:
                continue

            if doc.get("LateArrival") is True or doc.get("lateArrival") is True:
                continue

            shift_doc = shift_cache.get((emp_id, attendance_date))
            if not shift_doc:
                continue
            shift_start_val = shift_doc.get("ShiftStart") or shift_doc.get("shiftStart")
            shift_name = shift_doc.get("ShiftName") or shift_doc.get("shiftName") or "shift"
            shift_start = _time_to_minutes(shift_start_val)
            if shift_start is None:
                continue

            actual_dt = _combine_attendance_datetime(attendance_date, check_in)
            if actual_dt is None:
                continue

            actual_minutes = actual_dt.hour * 60 + actual_dt.minute
            late_threshold = shift_start + 15
            if actual_minutes <= late_threshold:
                continue

            lateness_minutes = actual_minutes - shift_start
            event_key = f"{emp_id}:{attendance_date}:late_arrival"
            if event_key in seen_event_keys:
                continue
            seen_event_keys.add(event_key)

            employee_message = (
                f"Your attendance for {attendance_date} started {lateness_minutes} minutes late versus the {shift_name} shift start."
            )
            hr_message = (
                f"Employee {emp_id} arrived late for the {shift_name} shift on {attendance_date} ({lateness_minutes} minutes late)."
            )
            event_result = await _write_automation_event(
                db,
                event_key=event_key,
                event_type="late_arrival",
                emp_id=emp_id,
                attendance_date=attendance_date,
                severity="medium",
                description="Employee check-in occurred after the configured shift start threshold.",
                employee_message=employee_message,
                hr_message=hr_message,
                status="SUCCESS",
            )
            created["audit"] += event_result["audit"]
            created["employee_notification"] += event_result["employee_notification"]
            created["hr_notification"] += event_result["hr_notification"]
            if any(event_result.values()):
                events_detected += 1

        result = {
            "job_name": "late_arrival_detection",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "status": "COMPLETED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "events_detected": events_detected,
            "created": created,
        }
        logger.info("[Automation] late_arrival_detection completed events_detected=%s", events_detected)
        return result
    except Exception as exc:
        logger.exception("late_arrival_detection failed: %s", exc)
        return {
            "job_name": "late_arrival_detection",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "status": "FAILED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "events_detected": events_detected,
            "created": created,
            "error": str(exc),
        }


async def leave_reminder_job() -> Dict[str, Any]:
    """Create a conservative reminder for pending leave requests older than 48 hours without changing leave status."""
    start_ts = time.time()
    started_at = _utc_now_iso()
    db = get_database()
    events_detected = 0
    created = {"audit": 0, "employee_notification": 0, "hr_notification": 0}

    if db is None:
        return {"job_name": "leave_reminder", "status": "NO_DB", "started_at": started_at, "finished_at": _utc_now_iso(), "events_detected": 0}

    try:
        pending_leaves = await db.leaves.find({
            "Status": {"$in": ["Pending", "pending"]}
        }).to_list(length=2000)

        candidate_event_keys = []
        for doc in pending_leaves:
            emp_id = _safe_emp_id(doc)
            leave_start = doc.get("StartDate") or doc.get("startDate")
            if not emp_id:
                continue

            request_time = _get_leave_request_timestamp(doc)
            if request_time is None:
                continue

            age_hours = (datetime.now(timezone.utc) - request_time).total_seconds() / 3600.0
            if age_hours < 72:
                continue

            reminder_date = leave_start or request_time.strftime("%Y-%m-%d")
            event_key = f"{emp_id}:{request_time.isoformat()}:leave_reminder"
            candidate_event_keys.append(event_key)

        existing_event_keys = await _bulk_existing_event_keys(db, candidate_event_keys)
        seen_event_keys = set(existing_event_keys)

        for doc in pending_leaves:
            emp_id = _safe_emp_id(doc)
            leave_start = doc.get("StartDate") or doc.get("startDate")
            if not emp_id:
                continue

            request_time = _get_leave_request_timestamp(doc)
            if request_time is None:
                continue

            age_hours = (datetime.now(timezone.utc) - request_time).total_seconds() / 3600.0
            if age_hours < 72:
                continue

            reminder_date = leave_start or request_time.strftime("%Y-%m-%d")
            event_key = f"{emp_id}:{request_time.isoformat()}:leave_reminder"
            if event_key in seen_event_keys:
                continue
            seen_event_keys.add(event_key)

            employee_message = (
                f"Your leave request submitted on {request_time.date().isoformat()} remains pending. Please review the current status."
            )
            hr_message = (
                f"Pending leave request for employee {emp_id} submitted on {request_time.date().isoformat()} needs review."
            )
            event_result = await _write_automation_event(
                db,
                event_key=event_key,
                event_type="leave_reminder",
                emp_id=emp_id,
                attendance_date=str(reminder_date),
                severity="medium",
                description="A pending leave request remained unresolved beyond the reminder threshold.",
                employee_message=employee_message,
                hr_message=hr_message,
                status="SUCCESS",
            )
            created["audit"] += event_result["audit"]
            created["employee_notification"] += event_result["employee_notification"]
            created["hr_notification"] += event_result["hr_notification"]
            if any(event_result.values()):
                events_detected += 1

        result = {
            "job_name": "leave_reminder",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "status": "COMPLETED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "events_detected": events_detected,
            "created": created,
        }
        logger.info("[Automation] leave_reminder completed events_detected=%s", events_detected)
        return result
    except Exception as exc:
        logger.exception("leave_reminder failed: %s", exc)
        return {
            "job_name": "leave_reminder",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "status": "FAILED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "events_detected": events_detected,
            "created": created,
            "error": str(exc),
        }
