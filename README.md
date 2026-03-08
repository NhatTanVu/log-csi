# log-csi

> From raw logs to reconstructed incident timeline.\
> Treat your system failure like a crime scene.

log-csi is a cross-platform CLI (Windows / Linux / macOS) that
investigates distributed logs and reconstructs what happened within a
specific time window.

------------------------------------------------------------------------

## 🔎 What It Answers

"What happened between 10:15 and 10:45 on 2026-03-01?"

Output: 
- Chronological storyline
- Key errors and warnings
- Cross-service correlation
- Evidence references (file + line numbers)
- Likely cause (if inferable)

log-csi sorts events by **event timestamp**.\
If ingestion timestamps are available in logs (e.g., cloud providers),
future versions may display both to highlight clock drift or delayed log
delivery.

------------------------------------------------------------------------

## 🚧 MVP v1 Scope

### Included

- Recursive log loading
- Multiline event parsing
- Normalization into LogEvent schema
- Time window filtering
- Forensic-style timeline summary (LangChain)

### Not Included (Future)

- MCP server
- Tool-calling agents
- Vector DB (RAG retrieval)
- Web UI

------------------------------------------------------------------------

## 🧠 LangChain Architecture

The current version of **log-csi** uses LangChain to build an LLM
processing pipeline.

### Pipeline Overview

    Log Files
       ↓
    Log Parser
       ↓
    Normalized LogEvent objects
       ↓
    build_events_text()
       ↓
    ChatPromptTemplate
       ↓
    ChatOpenAI.with_structured_output()
       ↓
    IncidentReport (Pydantic schema)
       ↓
    CLI formatted output

### LangChain Runnable Pipeline

In code, the pipeline is implemented using LangChain's Runnable API:

``` python
chain = PROMPT | structured_model
```

This pipe (`|`) operator composes components together so the output of
the prompt is automatically passed to the LLM.

Conceptually this behaves like:

    PROMPT → LLM → Structured Output Parser

Equivalent expanded logic:

``` python
prompt_value = PROMPT.invoke(inputs)
response = structured_model.invoke(prompt_value)
return response
```

### Why This Architecture

Benefits of this approach:

-   Clear separation between **data preparation and AI reasoning**
-   Structured outputs enforced through **Pydantic schemas**
-   Easy to extend into **multi-step AI pipelines**
-   Compatible with future **agents and tool-calling systems**

------------------------------------------------------------------------

## 📁 Project Structure

    log-csi/
      src/
        log_csi/
          __init__.py
          cli.py
          config.py
          models.py
          parser/
            __init__.py
            regex_multiline.py
          storyline/
            __init__.py
            summarize.py
          util/
            __init__.py
            time.py
      profiles/
        generic_iso.yaml
        sitecore_log4net.yaml
      samples/
        example.log
      tests/
        test_parser_basic.py
      .env.example
      pyproject.toml
      README.md
      LICENSE

------------------------------------------------------------------------

## ⚙ Setup

### Create virtual environment

Windows:

    python -m venv .venv
    .venv\Scripts\Activate.ps1

Linux/macOS:

    python -m venv .venv
    source .venv/bin/activate

### Install

    pip install -e .

------------------------------------------------------------------------

## 🔐 Environment Variables

Copy `.env.example` to `.env`:

    OPENAI_API_KEY=your_key_here
    STORYLINE_MODEL=gpt-4o-mini
    DEFAULT_TIMEZONE=America/Vancouver

------------------------------------------------------------------------

## 🧪 Validate Log Profile

    log-csi validate-profile \
      --profile profiles/generic_iso.yaml \
      --sample samples/example.log

### 📝 Example Output (validate-profile)

    [bold]Parsed events:[/bold] 10
    [bold]First event:[/bold]
    {'ts_event': '2026-03-01 10:14:55', 'service': 'samples', 'severity': 'INFO', 'message': 'api-gateway Starting API gateway service', 'attrs': {}, 'source_ref': {'path': 'samples\\example.log', 'line_start': 1, 'line_end': 1}}

------------------------------------------------------------------------

## 🚀 Investigate an Incident

    log-csi query \
      --root samples \
      --profile profiles/generic_iso.yaml \
      --start "2026-03-01 10:15:00" \
      --end "2026-03-01 10:45:00"

### 📝 Example Output (query)

    ===================== log-csi Incident Report =====================

    Title: Incident Report for Database Connection Issues
    Time Window: 2026-03-01 10:15:00 -> 2026-03-01 10:45:00

    Summary Timeline (chronological):

    2026-03-01 10:15:03 - samples - ERROR
      Postgres lock wait timeout exceeded; transaction aborted.
      [samples\example.log:2-7]

    2026-03-01 10:16:20 - samples - ERROR
      Auth-service database connection timeout after 30 seconds.
      [samples\example.log:8-13]

    2026-03-01 10:17:05 - samples - WARN
      API-gateway detected a spike in 502 responses.
      [samples\example.log:14-14]

    2026-03-01 10:18:10 - samples - INFO
      API-gateway retry attempts increased (x4 per request).
      [samples\example.log:15-16]

    2026-03-01 10:22:34 - samples - WARN
      Worker-service queue backlog growing rapidly.
      [samples\example.log:17-17]

    2026-03-01 10:25:12 - samples - ERROR
      Worker-service failed to process job id=84921 due to upstream timeout.
      [samples\example.log:18-19]

    2026-03-01 10:30:45 - samples - INFO
      Postgres lock cleared after transaction rollback.
      [samples\example.log:20-20]

    2026-03-01 10:32:02 - samples - INFO
      Auth-service database connections recovering.
      [samples\example.log:21-21]

    2026-03-01 10:40:15 - samples - INFO
      API-gateway error rate returning to normal.
      [samples\example.log:22-22]

    Root Cause:
    The incident was primarily caused by a database lock timeout, which led to cascading failures in the auth-service and worker-service, resulting in increased error rates and job processing failures.

    Confidence: High
    Notes: No additional evidence was found to suggest other underlying issues.

    ==================================================================

------------------------------------------------------------------------

## 🗺 Roadmap

v0.1 --- Basic forensic timeline\
v0.2 --- Add JSON cloud logs (Azure/AWS/GCP)\
v0.3 --- Add vector search (RAG retrieval)\
v1.0 --- MCP server + AI investigative agent
