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

    ===================== log-csi Profile Validation =====================

    Profile: generic_iso
    Sample File: samples/example.log

    Detected Event Start Pattern:
      ^(\d{{4}}-\d{{2}}-\d{{2}}[ T]\d{{2}}:\d{{2}}:\d{{2}}(?:\.\d{{3,6}})?)\s+(TRACE|DEBUG|INFO|WARN|ERROR|FATAL)

    Parsed Events: 152
    Time Range Detected:
      2026-03-01 09:58:11 → 2026-03-01 10:52:44

    First Parsed Event:
      Timestamp : 2026-03-01 09:58:11
      Service   : api-gateway
      Severity  : INFO
      File Ref  : samples/example.log:1-3

    Status: ✔ Profile appears valid.

    =====================================================================

------------------------------------------------------------------------

## 🚀 Investigate an Incident

    log-csi query \
      --root ./logs \
      --profile profiles/generic_iso.yaml \
      --start "2026-03-01 10:15:00" \
      --end "2026-03-01 10:45:00" \
      --tz "America/Vancouver"

### 📝 Example Output (query)

    ===================== log-csi Incident Report =====================

    Time Window:
      2026-03-01 10:15:00 → 2026-03-01 10:45:00 (America/Vancouver)

    Summary Timeline (chronological):

    10:15:03 - postgres - ERROR
      Lock wait timeout exceeded; transaction aborted.
      [db/log-20260301.txt:88-95]

    10:16:20 - auth-service - ERROR
      Database connection timeout after 30 seconds.
      [auth-service/log-20260301.txt:342-358]

    10:17:05 - api-gateway - WARN
      Spike in 502 responses detected.
      [api-gateway/log-20260301.txt:120-125]

    10:18:10 - api-gateway - INFO
      Retry attempts increased (x4 per request).

    10:25–10:40 - multiple services - WARN/ERROR
      Elevated error rates observed across dependent services.

    Conclusion:

    Most likely root cause was database lock contention in Postgres, which led to
    authentication timeouts and cascading retries from api-gateway, causing 502s.

    Confidence: Medium (based on correlated timestamps and error patterns)

    ==================================================================

------------------------------------------------------------------------

## 🗺 Roadmap

v0.1 --- Basic forensic timeline\
v0.2 --- Add JSON cloud logs (Azure/AWS/GCP)\
v0.3 --- Add vector search (RAG retrieval)\
v1.0 --- MCP server + AI investigative agent
