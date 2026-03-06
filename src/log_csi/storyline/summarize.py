from __future__ import annotations
from typing import List
from langchain_openai import ChatOpenAI
from log_csi.models import LogEvent
from datetime import datetime
from zoneinfo import ZoneInfo

PROMPT = """You are an incident investigator.

Given log events from multiple services in a time window, write a single storyline:
- Use chronological order
- For every timeline entry, include the FULL local datetime in this format: YYYY-MM-DD HH:MM:SS
- Do not shorten timestamps to time-only
- Group repeated/retry spam
- Highlight key errors/warnings
- Conclude with likely cause (if inferable), otherwise state uncertainty clearly

Include evidence references in brackets like [service @ YYYY-MM-DD HH:MM:SS | file:line_start-line_end].

Events:
{events}
"""


def build_events_text(events: List[LogEvent], tz_name: str) -> str:
    tz = ZoneInfo(tz_name)

    # Events are already filtered + sorted
    out = []
    for e in events:
        ref = ""
        if e.source_ref:
            ref = f"{e.source_ref.path}:{e.source_ref.line_start}-{e.source_ref.line_end}"

        dt = datetime.fromtimestamp(e.ts_event, tz)
        ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        out.append(
            f"- {ts_str} | {e.service} | {e.severity} | {ref}\n{e.message}")
    return "\n\n".join(out)


def summarize_storyline(events: List[LogEvent], model: str, tz_name: str) -> str:
    llm = ChatOpenAI(model=model, temperature=0)
    text = build_events_text(events, tz_name)
    msg = PROMPT.format(events=text)
    return llm.invoke(msg).content
