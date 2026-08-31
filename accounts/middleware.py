import re
from django.db import connections

from .models import SqlAuditLog

WRITE_ACTION_RE = re.compile(r"^\s*(INSERT|UPDATE|DELETE)\b", re.IGNORECASE)
TABLE_PATTERNS = {
    "INSERT": re.compile(r"\bINTO\s+[`\"]?([\w.]+)[`\"]?", re.IGNORECASE),
    "UPDATE": re.compile(r"^\s*UPDATE\s+[`\"]?([\w.]+)[`\"]?", re.IGNORECASE),
    "DELETE": re.compile(r"\bFROM\s+[`\"]?([\w.]+)[`\"]?", re.IGNORECASE),
}


class SqlAuditMiddleware:
    """Records database writes made while serving an HTTP request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        entries = []

        def capture(execute, sql, params, many, context):
            match = WRITE_ACTION_RE.match(sql)
            if not match or "accounts_sqlauditlog" in sql.lower():
                return execute(sql, params, many, context)
            cursor = execute(sql, params, many, context)
            action = match.group(1).upper()
            table_match = TABLE_PATTERNS[action].search(sql)
            entries.append({"action": action, "table_name": table_match.group(1) if table_match else "", "sql": sql[:4000], "affected_rows": getattr(context["cursor"], "rowcount", None)})
            return cursor

        wrapper = connections["default"].execute_wrapper(capture)
        try:
            wrapper.__enter__()
            return self.get_response(request)
        finally:
            wrapper.__exit__(None, None, None)
            self._save_entries(request, entries)

    @staticmethod
    def _save_entries(request, entries):
        if not entries:
            return
        user = getattr(request, "user", None)
        actor = user if getattr(user, "is_authenticated", False) else None
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")
        SqlAuditLog.objects.bulk_create([
            SqlAuditLog(actor=actor, request_method=request.method, request_path=request.path[:500], client_ip=client_ip or None, **entry)
            for entry in entries
        ])
