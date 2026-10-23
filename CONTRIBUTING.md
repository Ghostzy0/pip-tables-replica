# Contributing

Start with a small issue and a synthetic reproduction. Keep the accountless local core and original/reference licence boundaries. Never submit personal datasets, tokens, reference recordings, proprietary assets or copied private motion code.

Use Python 3.13, install requirements-lock.txt in a virtual environment, run `python -m pytest -q` and the smoke check. Both `--edition baseline` and `--edition pip` must remain runnable with identical engine semantics. For UI work, capture actual app renders in the changed states and test keyboard/focus, light/dark and a short window. Headless tests do not replace macOS package testing. Do not label an unsigned build notarised.

Describe the problem, resulting behaviour and actual validation in a focused PR. Include licence provenance for dependencies/assets. A reviewer must examine data correctness/security and the final packaged head before release; a green source test alone is insufficient. Versioned changes belong in CHANGELOG.md. CI must stay read-only and use pinned Actions. No automatic remote-script execution or paid-provider fallback.
