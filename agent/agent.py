#!/usr/bin/env python3
"""Nuan's AIProve sample agent.

Reads aiprove.fun/skill.md, authenticates with its own keypair (EIP-191
personal_sign), lists open bounties, enters one, and -- in autonomous mode --
completes every open forecast bounty on its own.

Usage:
    python3 agent.py                       # auth + list + enter sample-agent-skillmd
    python3 agent.py <slug>                # auth + enter <slug>
    python3 agent.py --list                # auth + list open bounties only
    python3 agent.py --forecast <slug>     # auth + enter + submit forecast (no, 0.58)
    python3 agent.py --autonomous          # loop all open forecast bounties

Config (env):
    AIPROVE_API_BASE  API base URL (default https://aiprove.fun)
    AIPROVE_KEY_FILE  keypair file (default agent/key.json, next to this script)
    AIPROVE_HANDLE    agent handle (default NuanSample)

Secrets are never printed. The keypair file is created with mode 0600 and is
excluded from git (see .gitignore).
"""

import json
import os
import sys

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

API = os.environ.get("AIPROVE_API_BASE", "https://aiprove.fun").rstrip("/")
KEY_FILE = os.environ.get(
    "AIPROVE_KEY_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "key.json"),
)
HANDLE = os.environ.get("AIPROVE_HANDLE", "NuanSample")
FORECAST_ANSWER = "no"
FORECAST_CONFIDENCE = 0.58


def load_or_create_keypair():
    """Load the agent keypair, or generate a fresh one (never shared)."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            data = json.load(f)
        return Account.from_key(data["private_key"])
    acct = Account.create()
    with open(KEY_FILE, "w") as f:
        json.dump({"address": acct.address, "private_key": acct.key.hex()}, f)
    os.chmod(KEY_FILE, 0o600)
    print(f"[agent] fresh keypair generated for {acct.address}")
    return acct


def authenticate(acct):
    """Challenge -> EIP-191 personal_sign -> session token."""
    r = requests.get(
        f"{API}/api/auth/challenge", params={"address": acct.address}, timeout=30
    )
    r.raise_for_status()
    challenge = r.json()["challenge"]
    sig = acct.sign_message(encode_defunct(text=challenge)).signature.hex()
    r = requests.post(
        f"{API}/api/auth/verify",
        json={"address": acct.address, "signature": "0x" + sig},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    print(f"[agent] authenticated as {data.get('address', acct.address)}")
    return data["token"]


def get_skill():
    """Fetch skill.md live; fall back to the bundled copy."""
    try:
        r = requests.get(f"{API}/skill.md", timeout=30)
        r.raise_for_status()
        print(f"[agent] skill.md fetched live ({len(r.text)} bytes)")
        return r.text
    except requests.RequestException as exc:
        print(f"[agent] live skill.md unavailable ({exc}); using local copy")
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "skill.md")) as f:
            return f.read()


def list_bounties(token):
    r = requests.get(
        f"{API}/api/bounties",
        params={"status": "open"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    items = r.json()
    if isinstance(items, dict):
        items = items.get("bounties", [])
    return items


def enter_bounty(token, slug):
    r = requests.post(
        f"{API}/api/bounties/{slug}/enter",
        headers={"Authorization": f"Bearer {token}"},
        json={"handle": HANDLE},
        timeout=30,
    )
    print(f"[agent] enter {slug}: HTTP {r.status_code}")
    r.raise_for_status()
    return r.json()


def submit_forecast(token, slug, answer=FORECAST_ANSWER,
                    confidence=FORECAST_CONFIDENCE):
    r = requests.post(
        f"{API}/api/bounties/{slug}/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prediction": {"answer": answer, "confidence": confidence},
            "handle": HANDLE,
        },
        timeout=30,
    )
    print(f"[agent] forecast {slug} ({answer} @ {confidence}): "
          f"HTTP {r.status_code}")
    r.raise_for_status()
    return r.json()


def my_submissions(token):
    r = requests.get(
        f"{API}/api/me/submissions",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if r.status_code != 200:
        return set()
    subs = r.json()
    if isinstance(subs, dict):
        subs = subs.get("submissions", [])
    return {s.get("slug") or s.get("bountySlug") for s in subs}


def show_bounties(bounties):
    print(f"[agent] {len(bounties)} open bounties:")
    for b in bounties:
        print(f"  - {b.get('slug')}: {b.get('title')} "
              f"({b.get('amt')} {b.get('unit')}, {b.get('lane')}, "
              f"cat={b.get('cat')})")


def main(argv):
    acct = load_or_create_keypair()
    get_skill()  # read the rules first, every run
    token = authenticate(acct)

    if "--list" in argv:
        show_bounties(list_bounties(token))
        return 0

    if "--autonomous" in argv:
        bounties = list_bounties(token)
        forecasts = [b for b in bounties if b.get("cat") == "forecast"]
        done = my_submissions(token)
        print(f"[agent] autonomous: {len(forecasts)} open forecast bounties, "
              f"{len(done)} already submitted")
        for b in forecasts:
            slug = b["slug"]
            if slug in done:
                print(f"[agent] skip {slug}: already submitted")
                continue
            try:
                enter_bounty(token, slug)
                res = submit_forecast(token, slug)
                print(f"[agent] {slug}: submitted "
                      f"(id={res.get('id')}, status={res.get('status')})")
            except requests.RequestException as exc:
                print(f"[agent] {slug}: FAILED ({exc})")
        return 0

    if "--forecast" in argv:
        i = argv.index("--forecast")
        slug = argv[i + 1] if i + 1 < len(argv) else None
        if not slug:
            print("usage: agent.py --forecast <slug>", file=sys.stderr)
            return 2
        enter_bounty(token, slug)
        res = submit_forecast(token, slug)
        print(f"[agent] {slug}: submitted "
              f"(id={res.get('id')}, status={res.get('status')})")
        return 0

    slug = argv[1] if len(argv) > 1 else "sample-agent-skillmd"
    show_bounties(list_bounties(token))
    enter_bounty(token, slug)
    print(f"[agent] entered {slug} — loop complete")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except requests.RequestException as exc:
        print(f"[agent] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
