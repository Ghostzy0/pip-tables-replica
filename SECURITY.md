# Security

Use synthetic data when reporting issues. Do not post private datasets, project folders, credentials or full paths. If private reporting is enabled for this repository, use GitHub's private vulnerability report; otherwise contact the maintainer through an existing verified channel before sharing details. No response-time promise is made.

SQL uses read-only DuckDB connections with external access and automatic extensions disabled. Imports read explicit local files and use defusedxml for workbook XML. Resource limits and safe spreadsheet text reduce common risks; this is not an OS/process sandbox against parser or native-library exploits. Install updates only from reviewed source/releases. Projects store plaintext snapshots and query history locally; keep sensitive projects in appropriately protected storage. No telemetry or network service runs in core.

Exports create new files atomically and never replace existing files. Original inputs are protected across path and hardlink aliases. Dependency licences/source are recorded in THIRD-PARTY-NOTICES. No signing certificate, secret key, account session or model is included in this source.
