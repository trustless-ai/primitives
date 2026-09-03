#!/usr/bin/env python3
"""Generate primitives.json (source of truth) + README.md (rendered registry) for trustless-ai.
Every entry was verified 2026-09-03: on-chain via eth_getCode, recompute recipes via the conformance
dir, repos via the org listing. Don't trust the list — recompute it."""
import json, pathlib
DATE = "2026-09-03"

live_onchain = [
  ("agent-market-escrow","AgentMarketEscrow","On-chain escrow for agent services — list, buy, settle.",
   "mainnet","0x82feaa28527adddfba29b5587c7b58d3e1e2c739"),
  ("mcp-entitlement-registry","MCPEntitlementRegistry","Buy an MCP capability that's carried by the agent NFT.",
   "mainnet","0x6374556D1c19924584644BD48ebecF444e43Ed9F"),
  ("truth-anchor","TruthAnchor (verify showcase L3)","On-chain anchor for the /verify showcase proof.",
   "mainnet","0x1e2A118a2bf1C240aE6fDe187c07f905D360f094"),
  ("genesis-agent-registry","GenesisAgentRegistry","Mint-your-agent registry (used by ai.verticecriativo.pt).",
   "mainnet","0x8b5AF3A59f81c7e16617E8Eb824BC6FfB792A2C3"),
  ("pq-binding-anchor","PqBindingAnchor (wallet PQ key binding)","First-write-immutable bind of a PQ key to a wallet.",
   "sepolia","0x0E6A09577f22A38239d4916C092E149BfB4AB57d"),
]

recompute_primitives = [
  "pq-key-binding-v0","pq-key-binding-v1","pq-key-binding-v1-profile","pq-recovery-classes-v0",
  "captured-admission-v0","captured-admission-v0-review-profile","captured-admission-v0-review-profile-deadline",
  "companion-envelope-v0","convention-hash-v0","provenance-anchor-v0","storage-root-v0",
  "encode-json-utf8-lf-v0","erc-8309-envelope-v0","erc8275-win-rate-bps-v0","communication-chain-v0",
  "chronicle-checkpoint-continuity-v0","crc-claim-v0","aggregate-budget-v0","dex-calldata-v0",
  "ens-write-v0","id-write-v0","nft-fulfill-v0","deils-leg2-reveal-v0","tee-inference-v0",
  "tee-inference-enclave-v0","serializer-bindings",
]

repos = [
  ("verify-layer","verify-don't-trust layer — prove account/storage state via eth_getProof vs stateRoot."),
  ("recompute-kit","the toolkit: recompute primitives + recipes + conformance vectors + MCP."),
  ("agent-sdk","off-chain SDK — typed contract clients + deploy/test kit for the agent ERCs."),
  ("ccip-router","the coordination layer CCIP-Read was missing — peer sync, dedup, mesh."),
  ("zkIE","Zero-Knowledge Inference Engine (prototype)."),
  ("recompute-lens","human surface over recompute-kit — watch an off-chain claim recompute."),
  ("eip7702-rescue","forensic MCP + hardened delegate for atomic EIP-7702 asset rescue."),
  ("pq-agent-binding","recomputable post-quantum key binding for on-chain AI agents."),
  ("agent-ercs","ERCs + base implementations for the trustless-AI agent stack."),
  ("cross-reference-console","multi-operator mutual-recompute surface — LIVE at trustless-ai.eth."),
]

notes = [
  ("collapsed-state-note","'A written rule has no failure mode' — collapsed states + the five tiers."),
  ("observation-conditions-note","'A reading is incomplete without the conditions that produced it.'"),
  ("composed-attestation-note","four independent commitments over one event — the seam rules."),
]

# ERCs we author / co-author / co-maintain (attribution kept precise).
ercs = [
  ("ERC-8299","WYRIWE — what-you-run-is-what-you-explain (input provenance).","co-author (TMerlini+Vincent+Fede+Jimmy+Damon)","ethereum/ERCs#1810"),
  ("ERC-8354","Confidential Agent Policy Verdicts (ZK allow/deny).","co-maintainer; expiry-bound circuit PR ethereum/ERCs#1989","ethereum/ERCs (merged #1919)"),
  ("ERC-8373","Post-Quantum Anchored Key Binding.","author","assets/erc-8373 (ethereum/ERCs)"),
  ("ERC-8294","VNI — Verifiable Network Inference.","co-author (Tiago)","ethereum/ERCs"),
]

entries = []
for i,(id_,name,what,chain,addr) in enumerate(live_onchain):
  entries.append({"id":id_,"name":name,"what":what,"status":"LIVE","chain":chain,
    "proof":{"type":"contract","address":addr,"chain":chain},
    "verify":f"eth_getCode {addr} on {chain} (non-empty)","verified_at":DATE})
for p in recompute_primitives:
  entries.append({"id":f"recompute:{p}","name":p,"what":"recomputable primitive (conformance vectors).",
    "status":"SHIPPED","proof":{"type":"recompute-recipe","ref":f"trustless-ai/recompute-kit/conformance/{p}"},
    "verify":"run the recompute-kit conformance suite for this recipe","verified_at":DATE})
for r,desc in repos:
  entries.append({"id":f"repo:{r}","name":r,"what":desc,
    "status":"LIVE" if r=="cross-reference-console" else "SHIPPED",
    "proof":{"type":"repo","ref":f"github.com/trustless-ai/{r}"},
    "verify":"open the repo / run its suite","verified_at":DATE})
for n,desc in notes:
  entries.append({"id":f"note:{n}","name":n,"what":desc,"status":"PUBLISHED",
    "proof":{"type":"repo","ref":f"github.com/trustless-ai/{n}"},"verify":"read it (CC0)","verified_at":DATE})
for num,name,role,ref in ercs:
  entries.append({"id":num.lower(),"name":f"{num} — {name}","what":f"{role}.","status":"DRAFT",
    "proof":{"type":"erc","ref":ref},"verify":"open the ERC PR / assets","verified_at":DATE})

out = {"schema":"trustless-ai.primitives.v0","updated":DATE,
  "note":"Discovery/INDEX surface — NOT a source of truth. Authority is the referenced contract bytes "
         "(eth_getCode), repo state, or conformance package; this file only points at them. A mismatch "
         "means the ENTRY is stale, not that the registry is truth — run check.py to detect drift. "
         "Status: LIVE=deployed/live, SHIPPED=code+vectors verifiable, PUBLISHED=note (CC0), DRAFT=spec in the ERC process.",
  "count":len(entries),"primitives":entries}

D = pathlib.Path("/private/tmp/claude-501/-Users-merliniferrao/9fb6bccd-50bf-4299-b2d9-6b045274c6fe/scratchpad/primitives")
(D/"primitives.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")

# ---- render README ----
def grp(s): return [e for e in entries if e["status"]==s]
L=[]
L.append("# trustless-ai · primitives registry\n")
L.append("What's **already built** — so nobody re-explains or reinvents it. `primitives.json` is the "
         "**index**, verified " + DATE + ".\n")
L.append("> **Index, not authority.** This registry only *points at* proofs; it is never itself the source of "
         "truth. Authority stays with the referenced **contract bytes** (`eth_getCode`), **repo state**, or "
         "**conformance package**. A mismatch means the *entry* is stale — not that the registry is truth. "
         "Run [`check.py`](check.py) (CI on every push) to recompute every entry against its authority and "
         "fail on drift. *(Rule sharpened by Pavlo in the WG.)*\n")
L.append("Status: 🟢 **LIVE** (deployed/live) · 🟡 **SHIPPED** (code + vectors, verifiable) · "
         "📄 **PUBLISHED** (note, CC0) · 🔵 **DRAFT** (spec, in the ERC process).\n")
L.append("## 🟢 LIVE — on-chain (eth_getCode-verified)")
for e in grp("LIVE"):
  if e["proof"]["type"]=="contract":
    L.append(f"- **{e['name']}** — {e['what']} · `{e['proof']['address']}` ({e['chain']})")
L.append("\n## 🟢 LIVE — services")
for e in grp("LIVE"):
  if e["proof"]["type"]=="repo":
    L.append(f"- **{e['name']}** — {e['what']} · {e['proof']['ref']}")
L.append(f"\n## 🟡 SHIPPED — recompute primitives ({len(recompute_primitives)}) · `recompute-kit/conformance/`")
L.append("Each is a recomputable recipe with conformance vectors — run the suite to check any of them:")
L.append("`" + "`, `".join(recompute_primitives) + "`")
L.append("\n## 🟡 SHIPPED — tools & components")
for e in grp("SHIPPED"):
  if e["proof"]["type"]=="repo":
    L.append(f"- **{e['name']}** — {e['what']} · {e['proof']['ref']}")
L.append("\n## 📄 PUBLISHED — notes (CC0)")
for e in grp("PUBLISHED"):
  L.append(f"- **{e['name']}** — {e['what']} · {e['proof']['ref']}")
L.append("\n## 🔵 DRAFT — ERCs (in the ERC process)")
for e in grp("DRAFT"):
  L.append(f"- **{e['name']}** — {e['what']} · {e['proof']['ref']}")
L.append("\n## Detect drift — `check.py`")
L.append("Recomputes every entry against its authority and exits non-zero on any mismatch, so a stale index "
         "is *detectable*, never load-bearing:")
L.append("- **contract** → `eth_getCode` on the named chain (needs a trusted RPC: `ALCHEMY_KEY` or "
         "`RPC_URL_MAINNET`/`RPC_URL_SEPOLIA` — we don't trust arbitrary public RPCs, one returned a false "
         "empty for a live contract)")
L.append("- **repo / note** → the repository resolves (`gh api`)")
L.append("- **recompute-recipe** → the conformance package exists in `recompute-kit/conformance/`")
L.append("- **erc** → index-only here; verify at the ERC PR")
L.append("```\npython3 check.py    # ✅ PASS / ❌ STALE / ⚠️ SKIP / 📄 INDEX ; exit 1 on drift\n```")
L.append(f"\n---\n{len(entries)} entries. Authority > index, always. CC0.")
(D/"README.md").write_text("\n".join(L)+"\n")
print("wrote primitives.json + README.md ·", len(entries), "entries")
print("  LIVE:",len(grp("LIVE")),"SHIPPED:",len(grp("SHIPPED")),"PUBLISHED:",len(grp("PUBLISHED")),"DRAFT:",len(grp("DRAFT")))
