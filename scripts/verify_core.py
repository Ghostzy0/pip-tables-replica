"""Check the unmodified public shared-engine pin before build/review."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
pin=json.loads((root/'SHARED-CORE.json').read_text())
for name,expected in pin['files'].items():
    actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
    if actual!=expected: raise SystemExit('Shared core mismatch: '+name)
print('Shared core verified: '+pin['commit'])
