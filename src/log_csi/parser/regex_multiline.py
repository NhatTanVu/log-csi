from __future__ import annotations
from pathlib import Path
import re
from typing import List, Tuple
from dateutil import parser as dtparser
from zoneinfo import ZoneInfo

from log_csi.models import LogEvent, SourceRef


def _compile_named_groups(pattern: str) -> re.Pattern:
    # Convert (?<name>...) into (?P<name>...) for Python
    pattern_py = re.sub(r"\(\?<([a-zA-Z_]\w*)>", r"(?P<\1>", pattern)
    return re.compile(pattern_py)

def parse_file_regex_multiline(
    file_path: Path,
    event_start_regex: str,
    tz: str,
    service_from_path: Tuple[str, int] | None = None,  # ("path_parent", depth)
) -> List[LogEvent]:
    rx = _compile_named_groups(event_start_regex)
    lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()

    events: List[LogEvent] = []
    cur_start = None  # (line_idx, match)
    cur_buf: List[str] = []

    def flush(cur_start, cur_buf, end_idx: int):
        if not cur_start:
            return
        start_idx, m = cur_start
        ts_raw = m.groupdict().get("ts")
        level = m.groupdict().get("level", "INFO")
        rest = m.groupdict().get("rest", "")

        # parse time
        dt = dtparser.parse(ts_raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(tz))
        ts_event = dt.timestamp()

        message = rest
        if cur_buf:
            message = rest + "\n" + "\n".join(cur_buf)

        # service naming
        service = "unknown"
        if service_from_path and service_from_path[0] == "path_parent":
            depth = service_from_path[1]
            parts = file_path.parts
            if len(parts) >= depth + 1:
                service = parts[-(depth + 1)]  # parent folder
        else:
            service = file_path.parent.name

        events.append(
            LogEvent(
                ts_event=ts_event,
                service=service,
                severity=level,
                message=message,
                source_ref=SourceRef(path=str(file_path), line_start=start_idx + 1, line_end=end_idx + 1),
            )
        )

    for i, line in enumerate(lines):
        m = rx.match(line)
        if m:
            flush(cur_start, cur_buf, i - 1)
            cur_start = (i, m)
            cur_buf = []
        else:
            # continuation line (stack trace etc.)
            if cur_start:
                cur_buf.append(line)

    flush(cur_start, cur_buf, len(lines) - 1)
    return events