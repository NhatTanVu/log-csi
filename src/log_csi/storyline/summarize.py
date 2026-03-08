from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field
from zoneinfo import ZoneInfo

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from log_csi.models import LogEvent


class TimelineEntry(BaseModel):
    timestamp: str = Field(description="Local datetime in format YYYY-MM-DD HH:MM:SS")
    service: str
    severity: str
    summary: str
    evidence: str = Field(description="file:line_start-line_end or equivalent source reference")


class IncidentReport(BaseModel):
    title: str
    time_window: str
    timeline: List[TimelineEntry]
    root_cause: str
    confidence: Literal["low", "medium", "high"]
    notes: str = Field(description="Any uncertainty, caveats, or missing evidence")


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are log-csi, a forensic incident investigator.

Your job is to reconstruct what happened from log events.

Rules:
- Use chronological order only.
- Every timeline entry must include the FULL local datetime in this exact format: YYYY-MM-DD HH:MM:SS
- Keep each timeline summary concise and factual.
- Prefer causal chains when supported by timestamps and messages.
- Do not invent evidence.
- If uncertain, say so in notes and lower confidence.
- Root cause should be one short paragraph.
""",
        ),
        (
            "human",
            """Investigate this incident.

Timezone: {tz_name}
Window: {window_start} -> {window_end}

Events:
{events_text}
""",
        ),
    ]
)


def build_events_text(events: List[LogEvent], tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    out: List[str] = []

    for e in events:
        dt = datetime.fromtimestamp(e.ts_event, tz)
        ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        ref = "unknown"
        if e.source_ref:
            ref = f"{e.source_ref.path}:{e.source_ref.line_start}-{e.source_ref.line_end}"

        out.append(
            "\n".join(
                [
                    f"- timestamp: {ts_str}",
                    f"  service: {e.service}",
                    f"  severity: {e.severity}",
                    f"  evidence: {ref}",
                    f"  message: {e.message}",
                ]
            )
        )

    return "\n\n".join(out)


def summarize_storyline(
    events: List[LogEvent],
    model: str,
    tz_name: str,
    window_start: str,
    window_end: str,
) -> IncidentReport:
    model_obj = ChatOpenAI(model=model, temperature=0)

    # Native structured output for OpenAI-capable models
    structured_model = model_obj.with_structured_output(
        IncidentReport,
        method="json_schema",
    )

    chain = PROMPT | structured_model

    return chain.invoke(
        {
            "tz_name": tz_name,
            "window_start": window_start,
            "window_end": window_end,
            "events_text": build_events_text(events, tz_name),
        }
    )


def render_report(report: IncidentReport) -> str:
    lines: List[str] = []
    lines.append("===================== log-csi Incident Report =====================")
    lines.append("")
    lines.append(f"Title: {report.title}")
    lines.append(f"Time Window: {report.time_window}")
    lines.append("")
    lines.append("Summary Timeline (chronological):")
    lines.append("")

    for item in report.timeline:
        lines.append(f"{item.timestamp} - {item.service} - {item.severity}")
        lines.append(f"  {item.summary}")
        lines.append(f"  [{item.evidence}]")
        lines.append("")

    lines.append("Root Cause:")
    lines.append(report.root_cause)
    lines.append("")
    lines.append(f"Confidence: {report.confidence.title()}")
    lines.append(f"Notes: {report.notes}")
    lines.append("")
    lines.append("==================================================================")
    return "\n".join(lines)