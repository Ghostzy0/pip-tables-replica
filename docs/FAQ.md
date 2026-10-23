# Questions and first workflow

What does this recreate? A bounded observed file/conversation/chart/CSV-artifact workflow and layout structure, written originally. It is a partial local prototype, not Julius code or full AI equivalence. Deterministic question rules and visible SQL do the work.

How do I reproduce the sample? Import examples/orders.csv, ask count rows (12), count amount (11), sum amount (1384.25), then sum amount by region bar chart (North 555.75,South 419.75,West 408.75). Open View/Export CSV; choose a new filename. Reopen the project to retain conversation and data.

Where are my files? Only selected/pasted data enters a plaintext project folder on your Mac. No app server, provider, account or analytics. Source files stay unchanged. Back up the whole closed folder. Source setup downloads packages from PyPI; no runtime downloads.

Can it answer arbitrary questions? No. Supported rules require exact column names; SQL: allows validated read-only SQL over imported tables. Models/forecasting/Python notebooks/remote databases/sharing are absent. Errors keep prior artifacts.

How does the custom app differ? Pip Tables is a separate data workbench with profiles, SQL recipes/filter/sort/history, neutral/Pip themes and Plus inspection/pages. It does not claim to be the faithful conversation replica. Both use the pinned engine recorded in SHARED-CORE.json.

Is it safe to install? This experimental source is MIT with dependency licences retained. Packages are locally ad-hoc signed and not notarised. Read exact release evidence/checksums; source setup is available. Do not disable OS security globally. Native accessibility/second-host acceptance is still pending unless the release notes record it.
