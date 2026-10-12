"""Fetch the recorded source snapshot; fail if a live source has changed."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote

ROOT=Path(__file__).resolve().parent
for source in json.loads((ROOT/'data/source_manifest.json').read_text()):
    destination=ROOT/'data'/f"{source['name']}.csv"
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest()==source['sha256']:
        print(f"Verified {destination.name}")
        continue
    with urlopen(quote(source['url'],safe=':/?&='),timeout=60) as response: content=response.read()
    if hashlib.sha256(content).hexdigest()!=source['sha256']:
        raise RuntimeError(f"{source['name']} changed: retain this snapshot or explicitly review a new release before rerunning.")
    destination.write_bytes(content)
    print(f"Downloaded and verified {destination.name}")
