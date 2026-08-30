import json
import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, Query

router = APIRouter(prefix="/holidays", tags=["Holiday Calendar"])

# Prefer a single canonical data source under backend/app/data/holidays.json
DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
# ensure data directory exists at runtime
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass

DATA_FILE = os.path.join(DATA_DIR, 'holidays.json')
LEGACY_FILE = os.path.join(os.path.dirname(__file__), 'holidays_data.json')

# If the canonical data file is missing but a legacy file exists, copy it into place (one-time runtime consolidation)
if not os.path.exists(DATA_FILE) and os.path.exists(LEGACY_FILE):
    try:
        with open(LEGACY_FILE, 'r', encoding='utf-8') as src, open(DATA_FILE, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    except Exception:
        # best-effort; fall back to reading legacy file
        pass


def _load_holidays() -> List[dict]:
    # Try the canonical data file first
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # Fallback to legacy file for backward compatibility
        try:
            with open(LEGACY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []


@router.get("")
async def get_holidays(month: str = Query(None, description="Optional month filter in YYYY-MM format")):
    """Return holidays. If month is provided (YYYY-MM) filter to that month, otherwise return all."""
    items = _load_holidays()
    if not month:
        return items

    # Validate month format YYYY-MM
    try:
        dt = datetime.strptime(month, "%Y-%m")
    except ValueError:
        # If invalid format, return full list instead of erroring to be tolerant
        return items

    year = dt.year
    month_num = dt.month

    filtered = []
    for h in items:
        try:
            hdate = datetime.strptime(h.get('date', ''), '%Y-%m-%d')
            if hdate.year == year and hdate.month == month_num:
                filtered.append(h)
        except Exception:
            continue

    return filtered
