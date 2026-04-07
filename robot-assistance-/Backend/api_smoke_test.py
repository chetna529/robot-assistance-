import json
from datetime import datetime, timedelta, timezone
from urllib import parse, request
from urllib.error import HTTPError, URLError

base = "http://127.0.0.1:8000"
results = []


def add(endpoint, ok, status, note):
    results.append({"endpoint": endpoint, "ok": bool(ok), "status": int(status), "note": note})


def call(method, path, expected=None, params=None, body=None):
    url = base + path
    if params:
        url += "?" + parse.urlencode(params)
    try:
        data_bytes = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data_bytes = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=data_bytes, headers=headers, method=method)
        with request.urlopen(req, timeout=30) as response:
            status = response.status
            raw = response.read().decode("utf-8")
        data = None
        if raw:
            try:
                data = json.loads(raw)
            except Exception:
                data = None

        if expected is None:
            ok = 200 <= status < 300
        elif isinstance(expected, (list, tuple, set)):
            ok = status in expected
        else:
            ok = status == expected

        return status, data, ok
    except HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8") if exc.fp else ""
        data = None
        if raw:
            try:
                data = json.loads(raw)
            except Exception:
                data = None

        if expected is None:
            ok = 200 <= status < 300
        elif isinstance(expected, (list, tuple, set)):
            ok = status in expected
        else:
            ok = status == expected

        return status, data, ok
    except URLError as exc:
        return 0, {"error": str(exc)}, False
    except Exception as exc:
        return 0, {"error": str(exc)}, False


status, data, ok = call("GET", "/", expected=200)
add("/", ok, status, "root")
status, data, ok = call("GET", "/api/health", expected=200)
add("/api/health", ok, status, "health")
status, data, ok = call("GET", "/api/info", expected=200)
add("/api/info", ok, status, "info")
status, data, ok = call("GET", "/api/weather/status", expected=200)
add("/api/weather/status", ok, status, "weather status")
status, data, ok = call(
    "GET", "/api/weather/current", expected=200, params={"city": "Kolkata", "units": "metric"}
)
add("/api/weather/current", ok, status, "weather current")
status, data, ok = call("GET", "/api/info/weather", expected=200, params={"city": "Kolkata", "units": "metric"})
add("/api/info/weather", ok, status, "info weather")
status, data, ok = call("GET", "/api/auth/google/status", expected=200)
add("/api/auth/google/status", ok, status, "auth status")
status, data, ok = call("GET", "/api/auth/google/url", expected={200, 400})
add("/api/auth/google/url", ok, status, "auth url")
status, data, ok = call("GET", "/api/auth/google/callback", expected=422)
add("/api/auth/google/callback without code", ok, status, "expected validation error")

meeting_id = None
reminder_id = None
notification_id = None
user_id = None
run_token = int(datetime.now(timezone.utc).timestamp())

status, data, ok = call(
    "POST",
    "/api/users",
    expected=201,
    body={
        "name": "API Test User",
        "email": f"api.test.user.{run_token}@example.com",
        "password": "Passw0rd!",
        "role": "employee",
        "department": "QA",
        "is_active": True,
        "preferred_language": "en",
    },
)
user_id = (data or {}).get("id") if isinstance(data, dict) else None
add("/api/users POST", ok and bool(user_id), status, f"created id={user_id}")
status, data, ok = call("GET", "/api/users", expected=200)
add("/api/users GET", ok, status, "list users")
if user_id:
    status, data, ok = call("GET", f"/api/users/{user_id}", expected=200)
    add("/api/users/{id} GET", ok, status, "get user")
    status, data, ok = call(
        "PUT",
        f"/api/users/{user_id}",
        expected=200,
        body={"department": "Engineering", "preferred_language": "hi"},
    )
    add("/api/users/{id} PUT", ok, status, "update user")
    status, data, ok = call("DELETE", f"/api/users/{user_id}", expected=200)
    add("/api/users/{id} DELETE", ok, status, "deactivate user")

start = datetime.now(timezone.utc) + timedelta(hours=2)
end = start + timedelta(minutes=45)
meeting_body = {
    "title": "API Validation Meeting",
    "description": "created by automated API test",
    "start_time": start.isoformat(),
    "end_time": end.isoformat(),
    "location": "Online",
    "availability": "busy",
    "alert_minutes": [15, 30],
    "is_recurring": False,
    "recurrence_frequency": None,
    "recurrence_interval": 1,
    "recurrence_count": None,
    "recurrence_until": None,
    "recurrence_by_weekday": [],
    "attendees": ["qa@example.com"],
    "user_id": 1,
}
status, data, ok = call("POST", "/api/meetings", expected=201, body=meeting_body)
meeting_id = (data or {}).get("id") if isinstance(data, dict) else None
add("/api/meetings POST", ok and bool(meeting_id), status, f"created id={meeting_id}")

status, data, ok = call("GET", "/api/meetings", expected=200)
add("/api/meetings GET", ok, status, "list meetings")
status, data, ok = call("GET", "/api/meetings/today", expected=200)
add("/api/meetings/today", ok, status, "today meetings")

if meeting_id:
    status, data, ok = call("GET", f"/api/meetings/{meeting_id}", expected=200)
    add("/api/meetings/{id} GET", ok, status, "get meeting")
    status, data, ok = call(
        "GET",
        f"/api/meetings/{meeting_id}/occurrences",
        expected=200,
        params={
            "range_start": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "range_end": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "limit": 10,
        },
    )
    add("/api/meetings/{id}/occurrences", ok, status, "occurrences")
    status, data, ok = call(
        "PATCH", f"/api/meetings/{meeting_id}/availability", expected=200, body={"availability": "free"}
    )
    add("/api/meetings/{id}/availability PATCH", ok, status, "patch availability")
    status, data, ok = call(
        "PATCH", f"/api/meetings/{meeting_id}/alerts", expected=200, body={"alert_minutes": [5, 10]}
    )
    add("/api/meetings/{id}/alerts PATCH", ok, status, "patch alerts")
    status, data, ok = call(
        "PUT",
        f"/api/meetings/{meeting_id}",
        expected=200,
        body={
            "title": "API Validation Meeting Updated",
            "is_recurring": True,
            "recurrence_frequency": "weekly",
            "recurrence_interval": 1,
            "recurrence_by_weekday": ["MO", "WE"],
        },
    )
    add("/api/meetings/{id} PUT", ok, status, "update meeting")

    status, data, ok = call(
        "POST",
        "/api/reminders",
        expected=201,
        body={"meeting_id": meeting_id, "message": "Reminder from test", "minutes_before": 20},
    )
    reminder_id = (data or {}).get("id") if isinstance(data, dict) else None
    add("/api/reminders POST", ok and bool(reminder_id), status, f"created id={reminder_id}")
    status, data, ok = call("GET", "/api/reminders", expected=200)
    add("/api/reminders GET", ok, status, "list reminders")
    status, data, ok = call("GET", f"/api/meetings/{meeting_id}/reminders", expected=200)
    add("/api/meetings/{id}/reminders GET", ok, status, "meeting reminders")
    if reminder_id:
        status, data, ok = call(
            "PUT",
            f"/api/reminders/{reminder_id}",
            expected=200,
            body={"message": "Updated reminder", "is_sent": True},
        )
        add("/api/reminders/{id} PUT", ok, status, "update reminder")

    status, data, ok = call(
        "POST",
        "/api/notifications",
        expected=201,
        body={
            "meeting_id": meeting_id,
            "channel": "email",
            "recipient": "user@example.com",
            "content": "Notification test",
            "delivered": False,
        },
    )
    notification_id = (data or {}).get("id") if isinstance(data, dict) else None
    add("/api/notifications POST", ok and bool(notification_id), status, f"created id={notification_id}")
    status, data, ok = call("GET", "/api/notifications", expected=200)
    add("/api/notifications GET", ok, status, "list notifications")
    status, data, ok = call("GET", f"/api/meetings/{meeting_id}/notifications", expected=200)
    add("/api/meetings/{id}/notifications GET", ok, status, "meeting notifications")
    if notification_id:
        status, data, ok = call(
            "PUT",
            f"/api/notifications/{notification_id}",
            expected=200,
            body={"content": "Updated content", "delivered": True},
        )
        add("/api/notifications/{id} PUT", ok, status, "update notification")

    status, data, ok = call("GET", "/api/executive-summary", expected=200, params={"city": "Kolkata", "units": "metric"})
    add("/api/executive-summary GET", ok, status, "executive summary")

    if notification_id:
        status, data, ok = call("DELETE", f"/api/notifications/{notification_id}", expected=200)
        add("/api/notifications/{id} DELETE", ok, status, "delete notification")
    if reminder_id:
        status, data, ok = call("DELETE", f"/api/reminders/{reminder_id}", expected=200)
        add("/api/reminders/{id} DELETE", ok, status, "delete reminder")
    status, data, ok = call("DELETE", f"/api/meetings/{meeting_id}", expected=200)
    add("/api/meetings/{id} DELETE", ok, status, "delete meeting")

passed = [item for item in results if item["ok"]]
failed = [item for item in results if not item["ok"]]
print(f"PASS={len(passed)} FAIL={len(failed)}")
print(json.dumps(results, indent=2))
