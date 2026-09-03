#!/usr/bin/env python3
"""Recompute every primitives.json entry against its AUTHORITY and report drift.

primitives.json is the discovery/index surface — NOT a source of truth. Authority is:
  • contract        → the on-chain bytecode (eth_getCode on the named chain)
  • repo / note     → the repository state (github.com/trustless-ai/<name>)
  • recompute-recipe→ the conformance package (recompute-kit/conformance/<name>)
  • erc             → the ERC PR / assets (index-only here; author verifies at the PR)

A mismatch means the ENTRY is stale, not that the registry is truth. Exit 1 if any entry
drifts, so CI catches a stale index before anyone trusts it.

Env: ALCHEMY_KEY (or ~/.claude/alchemy_key) for eth_getCode; `gh` for GitHub authority checks.
"""
import json, os, sys, subprocess, urllib.request, pathlib

HERE = pathlib.Path(__file__).parent
REG = json.loads((HERE / "primitives.json").read_text())

def alchemy_key():
    k = os.environ.get("ALCHEMY_KEY")
    if k: return k.strip()
    p = pathlib.Path.home() / ".claude" / "alchemy_key"
    return p.read_text().strip() if p.exists() else None

KEY = alchemy_key()
NET = {"mainnet": "eth-mainnet", "sepolia": "eth-sepolia"}
# We do NOT fall back to arbitrary public RPCs: they lie (an untrusted node returned "0 bytes"
# for a contract that has 3371) and a false STALE is worse than an honest SKIP. On-chain
# authority needs a trusted RPC (ALCHEMY_KEY) — or the verify-layer eth_getProof path.
RPC = os.environ.get("RPC_URL_MAINNET"), os.environ.get("RPC_URL_SEPOLIA")

def _rpc_url(chain):
    if chain == "mainnet" and RPC[0]: return RPC[0]
    if chain == "sepolia" and RPC[1]: return RPC[1]
    if KEY and chain in NET: return f"https://{NET[chain]}.g.alchemy.com/v2/{KEY}"
    return None

def eth_getcode(addr, chain):
    url = _rpc_url(chain)
    if not url: return None, f"no trusted RPC for {chain} (set ALCHEMY_KEY or RPC_URL_{chain.upper()})"
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getCode","params":[addr,"latest"]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=20).read())
        code = r.get("result")
        if not isinstance(code, str): return None, f"bad result {r.get('error')}"
        return (code != "0x" and len(code) > 2), f"{(len(code)-2)//2} bytes on {chain}"
    except Exception as e:
        return None, f"rpc error: {e}"

def gh_exists(path):
    """gh api <path> → True if 200, False if 404, None on other error."""
    try:
        p = subprocess.run(["gh","api",path,"--silent"], capture_output=True, text=True, timeout=25)
        if p.returncode == 0: return True, "200"
        if "404" in (p.stderr or ""): return False, "404"
        return None, (p.stderr or "").strip()[:60]
    except Exception as e:
        return None, str(e)[:60]

def ref_repo(ref):  # "github.com/trustless-ai/verify-layer" -> "repos/trustless-ai/verify-layer"
    tail = ref.split("github.com/",1)[-1].strip("/")
    return "repos/" + tail

def check(e):
    pf = e.get("proof",{}); t = pf.get("type")
    if t == "contract":
        ok, detail = eth_getcode(pf["address"], pf.get("chain") or e.get("chain"))
        return ("PASS" if ok else "STALE" if ok is False else "SKIP"), detail
    if t == "recompute-recipe":
        # ref: trustless-ai/recompute-kit/conformance/<name>
        tail = pf["ref"].split("recompute-kit/",1)[-1]  # conformance/<name>
        ok, detail = gh_exists(f"repos/trustless-ai/recompute-kit/contents/{tail}")
        return ("PASS" if ok else "STALE" if ok is False else "SKIP"), f"recompute-kit/{tail} {detail}"
    if t == "repo":
        ok, detail = gh_exists(ref_repo(pf["ref"]))
        return ("PASS" if ok else "STALE" if ok is False else "SKIP"), f"{pf['ref']} {detail}"
    if t == "erc":
        return "INDEX", f"{pf['ref']} (verify at the ERC PR)"
    return "SKIP", f"unknown proof type {t}"

def main():
    rows, counts = [], {}
    for e in REG["primitives"]:
        state, detail = check(e)
        counts[state] = counts.get(state,0)+1
        rows.append((state, e["name"], detail))
    icon = {"PASS":"✅","STALE":"❌","SKIP":"⚠️","INDEX":"📄"}
    for state, name, detail in rows:
        print(f"{icon.get(state,'?')} {state:5} {name[:44]:44} {detail}")
    print("\n" + "  ".join(f"{k}:{v}" for k,v in sorted(counts.items())))
    stale = counts.get("STALE",0)
    if stale:
        print(f"\n{stale} STALE entr{'y' if stale==1 else 'ies'} — the INDEX drifted from AUTHORITY. Fix primitives.json.")
        return 1
    print("\nNo drift: every checkable entry recomputes against its authority.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
