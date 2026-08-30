import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "provision_employee_accounts.py"
SPEC = importlib.util.spec_from_file_location("provision_employee_accounts", SCRIPT_PATH)
PROVISION_SCRIPT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROVISION_SCRIPT)


def _make_employee(emp_id, *, status="Active", email="employee@example.com", exit_date=None):
    doc = {"EmpID": emp_id, "EmploymentStatus": status, "Email": email}
    if exit_date is not None:
        doc["ExitDate"] = exit_date
    return doc


def test_provision_script_defaults_to_dry_run():
    assert PROVISION_SCRIPT.DRY_RUN is True


def test_active_employee_is_eligible():
    doc = _make_employee("EMP000123")
    result = PROVISION_SCRIPT._evaluate_employee_for_account(
        doc,
        set(),
        set(),
        {"empId": set(), "email": set()},
    )
    assert result is None


def test_exited_employee_is_rejected():
    doc = _make_employee("EMP000124", status="Exited")
    result = PROVISION_SCRIPT._evaluate_employee_for_account(
        doc,
        set(),
        set(),
        {"empId": set(), "email": set()},
    )
    assert result == "non_active_status"


def test_inactive_terminated_resigned_and_unknown_are_rejected():
    for status in ["Inactive", "Terminated", "Resigned", "Unknown"]:
        doc = _make_employee("EMP000125", status=status)
        result = PROVISION_SCRIPT._evaluate_employee_for_account(
            doc,
            set(),
            set(),
            {"empId": set(), "email": set()},
        )
        assert result == "non_active_status"


def test_exit_date_employee_is_rejected_even_if_active():
    doc = _make_employee("EMP000126", exit_date="2026-01-01")
    result = PROVISION_SCRIPT._evaluate_employee_for_account(
        doc,
        set(),
        set(),
        {"empId": set(), "email": set()},
    )
    assert result == "exit_date"


def test_missing_or_invalid_email_is_rejected():
    for email in ["", "invalid-email", "employee@local"]:
        doc = _make_employee("EMP000127", email=email)
        result = PROVISION_SCRIPT._evaluate_employee_for_account(
            doc,
            set(),
            set(),
            {"empId": set(), "email": set()},
        )
        assert result == "invalid_email"


def test_existing_empid_and_existing_email_are_skipped():
    active_doc = _make_employee("EMP000128")
    existing_emp = PROVISION_SCRIPT._evaluate_employee_for_account(
        active_doc,
        set(),
        set(),
        {"empId": {"EMP000128"}, "email": set()},
    )
    assert existing_emp == "existing_empid"

    email_doc = _make_employee("EMP000129", email="existing.user@example.com")
    existing_email = PROVISION_SCRIPT._evaluate_employee_for_account(
        email_doc,
        set(),
        set(),
        {"empId": set(), "email": {"existing.user@example.com"}},
    )
    assert existing_email == "existing_email"


def test_duplicate_employee_empid_and_email_are_rejected():
    duplicate_empid_doc = _make_employee("EMP000130")
    duplicate_email_doc = _make_employee("EMP000131", email="dup@example.com")

    emp_result = PROVISION_SCRIPT._evaluate_employee_for_account(
        duplicate_empid_doc,
        {"EMP000130"},
        set(),
        {"empId": set(), "email": set()},
    )
    assert emp_result == "duplicate_empid"

    email_result = PROVISION_SCRIPT._evaluate_employee_for_account(
        duplicate_email_doc,
        set(),
        {"dup@example.com"},
        {"empId": set(), "email": set()},
    )
    assert email_result == "duplicate_email"


def test_canary_rejects_exited_employee():
    doc = _make_employee("EMP000132", status="Exited")
    assert PROVISION_SCRIPT._is_active_employee(doc) is False
    assert PROVISION_SCRIPT._employee_has_exit_date(doc) is False


def test_dry_run_is_default_and_production_confirmation_still_required():
    assert PROVISION_SCRIPT.DRY_RUN is True
    assert PROVISION_SCRIPT.PRODUCTION_CONFIRMATION == ""
