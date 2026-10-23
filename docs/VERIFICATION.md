# Verification record

Updated 23 October 2026. This record describes the exported Neutral Core source at `3681051eda55d303e8a1de3f4eff2ee3f586b38b`, restored into a clean clone and built on macOS 27.0.1, Apple silicon, Python 3.13.16. The shared data engine is unchanged from public `pip-tables` commit `9af81fa3ef9b1bdcd4bddb251a3a557e0305182d`; `scripts/verify_core.py` confirmed both pinned file hashes.

The clean-clone run passed all 14 unit and offscreen Qt tests, `pip check`, the synthetic source smoke, a frozen application smoke, and strict deep code-signature verification. The frozen smoke verified 4 rows, 3 non-null values, decimal totals `0.30` and `2.05`, CSV export, and project reopen. The package inventory found 83 Mach-O files and 170 included licence files, with no unexpected absolute or relative native dependencies. The bundle uses an ad-hoc signature; it has no publisher identity or notarization.

An independent source and bounded package audit found no high- or medium-severity issue within the declared offline, local analysis, import, persistence, and CSV-export scope. This does not establish security isolation from malicious files, arbitrary SQL resource safety beyond the documented engine bounds, or acceptance on every macOS system.

| Primary variant | Repository | Scope |
| --- | --- | --- |
| Neutral Core | `Ghostzy0/pip-tables-replica` | Separate, original partial recreation of the observed Julius conversation-to-artifact workflow; deterministic prompts and manual SQL. |
| Neutral Plus | `Ghostzy0/pip-tables` | Enhanced neutral edition of the custom local SQL workbench. |
| Pip Core | `Ghostzy0/pip-tables` | Pip-themed edition of the custom local SQL workbench. |
| Pip Plus | `Ghostzy0/pip-tables` | Enhanced Pip-themed edition of the custom local SQL workbench. |

The existing Neutral Workbench Core remains for source compatibility. It is the SQL workbench baseline, not the separate conversation-workflow replica. Tables Replica is partial workflow parity: it does not provide arbitrary natural-language analysis, a hosted model, an account, or full Julius product or layout equivalence.

The final native frozen package at `3681051` was opened on the same Mac. New project, selected synthetic CSV import, CmdReturn supported regional sum/bar chart, and native CSV save passed. The saved CSV contained North 555.75, South 419.75 and West 408.75 exactly. The first save automation supplied an absolute name while the native panel was at the read-only volume root; it failed safely and retained the result. Selecting the intended folder and a simple filename then exported successfully. The exact owned app was quit and verified absent. The actual native screenshot uses only original app UI and synthetic data. Native GUI acceptance is limited to this bounded workflow; VoiceOver, macOS motion preference behavior, second Mac, notarization and energy remain unverified.
