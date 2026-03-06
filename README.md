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

    [bold]Parsed events:[/bold] 10
    [bold]First event:[/bold]
    {'ts_event': 1772388895.0, 'service': 'samples', 'severity': 'INFO', 'message': 'api-gateway Starting API gateway service', 'attrs': {}, 'source_ref': {'path': 'samples\\example.log', 'line_start': 1, 'line_end': 1}}

------------------------------------------------------------------------

## 🚀 Investigate an Incident

    log-csi query \
      --root samples \
      --profile profiles/generic_iso.yaml \
      --start "2026-03-01 10:15:00" \
      --end "2026-03-01 10:45:00"

### 📝 Example Output (query)

### Incident Timeline

    **2026-03-01 10:15:03**  
    The incident begins with an error in the `samples` service, indicating a **lock wait timeout** in PostgreSQL, which results in a transaction being aborted. The error traceback shows that the timeout occurred during a commit operation in the database transaction module.  
    *Evidence: [samples @ 2026-03-01 10:15:03 | samples\example.log:2-7]*

    **2026-03-01 10:16:20**  
    Shortly after, the `auth-service` logs a **database connection timeout** after 30 seconds, indicating that it was unable to establish a connection to the database. This suggests that the database may be experiencing issues, possibly related to the previous lock timeout.  
    *Evidence: [samples @ 2026-03-01 10:16:20 | samples\example.log:8-13]*

    **2026-03-01 10:17:05**  
    The `api-gateway` detects a **spike in 502 responses**, which typically indicates that the gateway is unable to reach the upstream services, likely due to the ongoing database issues affecting service availability.
    *Evidence: [samples @ 2026-03-01 10:17:05 | samples\example.log:14-14]*

    **2026-03-01 10:18:10**
    In response to the 502 errors, the `api-gateway` increases its **retry attempts** to four per request, indicating an attempt to mitigate the impact of the upstream failures.
    *Evidence: [samples @ 2026-03-01 10:18:10 | samples\example.log:15-16]*

    **2026-03-01 10:22:34**
    The `worker-service` reports a **growing queue backlog**, suggesting that jobs are not being processed in a timely manner, likely due to the issues with the database and the upstream services.
    *Evidence: [samples @ 2026-03-01 10:22:34 | samples\example.log:17-17]*

    **2026-03-01 10:25:12**
    The `worker-service` logs a critical error, stating it **failed to process job id=84921** due to an upstream timeout. This reinforces the impact of the database issues on downstream services.
    *Evidence: [samples @ 2026-03-01 10:25:12 | samples\example.log:18-19]*

    **2026-03-01 10:30:45**
    The `postgres` service indicates that the **lock has been cleared** after a transaction rollback, which may allow for normal operations to resume.
    *Evidence: [samples @ 2026-03-01 10:30:45 | samples\example.log:20-20]*

    **2026-03-01 10:32:02**
    The `auth-service` reports that **database connections are recovering**, suggesting that the service is beginning to stabilize following the resolution of the lock issue.  
    *Evidence: [samples @ 2026-03-01 10:32:02 | samples\example.log:21-21]*

    **2026-03-01 10:40:15**
    Finally, the `api-gateway` notes that the **error rate is returning to normal**, indicating that the services are recovering from the previous disruptions.
    *Evidence: [samples @ 2026-03-01 10:40:15 | samples\example.log:22-22]*

    ### Conclusion
    The incident appears to have been initiated by a **lock wait timeout** in the PostgreSQL database, which led to cascading failures across multiple services, including connection timeouts in the `auth-service`, increased error rates in the `api-gateway`, and job processing failures in the `worker-service`. The situation improved once the lock was cleared and database connections began to recover. The root cause can be attributed to database contention issues, but further investigation may be needed to identify specific contributing factors.

------------------------------------------------------------------------

## 🗺 Roadmap

v0.1 --- Basic forensic timeline\
v0.2 --- Add JSON cloud logs (Azure/AWS/GCP)\
v0.3 --- Add vector search (RAG retrieval)\
v1.0 --- MCP server + AI investigative agent
