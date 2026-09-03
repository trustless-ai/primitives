# trustless-ai · primitives registry

What's **already built** — so nobody re-explains or reinvents it. **Don't trust this list — recompute it:** `eth_getCode` the address, open the repo, run the conformance recipe. Source of truth: `primitives.json`. Every entry verified 2026-09-03.

Status: 🟢 **LIVE** (deployed/live) · 🟡 **SHIPPED** (code + vectors, verifiable) · 📄 **PUBLISHED** (note, CC0) · 🔵 **DRAFT** (spec, in the ERC process).

## 🟢 LIVE — on-chain (eth_getCode-verified)
- **AgentMarketEscrow** — On-chain escrow for agent services — list, buy, settle. · `0x82feaa28527adddfba29b5587c7b58d3e1e2c739` (mainnet)
- **MCPEntitlementRegistry** — Buy an MCP capability that's carried by the agent NFT. · `0x6374556D1c19924584644BD48ebecF444e43Ed9F` (mainnet)
- **TruthAnchor (verify showcase L3)** — On-chain anchor for the /verify showcase proof. · `0x1e2A118a2bf1C240aE6fDe187c07f905D360f094` (mainnet)
- **GenesisAgentRegistry** — Mint-your-agent registry (used by ai.verticecriativo.pt). · `0x8b5AF3A59f81c7e16617E8Eb824BC6FfB792A2C3` (mainnet)
- **PqBindingAnchor (wallet PQ key binding)** — First-write-immutable bind of a PQ key to a wallet. · `0x0E6A09577f22A38239d4916C092E149BfB4AB57d` (sepolia)

## 🟢 LIVE — services
- **cross-reference-console** — multi-operator mutual-recompute surface — LIVE at trustless-ai.eth. · github.com/trustless-ai/cross-reference-console

## 🟡 SHIPPED — recompute primitives (26) · `recompute-kit/conformance/`
Each is a recomputable recipe with conformance vectors — run the suite to check any of them:
`pq-key-binding-v0`, `pq-key-binding-v1`, `pq-key-binding-v1-profile`, `pq-recovery-classes-v0`, `captured-admission-v0`, `captured-admission-v0-review-profile`, `captured-admission-v0-review-profile-deadline`, `companion-envelope-v0`, `convention-hash-v0`, `provenance-anchor-v0`, `storage-root-v0`, `encode-json-utf8-lf-v0`, `erc-8309-envelope-v0`, `erc8275-win-rate-bps-v0`, `communication-chain-v0`, `chronicle-checkpoint-continuity-v0`, `crc-claim-v0`, `aggregate-budget-v0`, `dex-calldata-v0`, `ens-write-v0`, `id-write-v0`, `nft-fulfill-v0`, `deils-leg2-reveal-v0`, `tee-inference-v0`, `tee-inference-enclave-v0`, `serializer-bindings`

## 🟡 SHIPPED — tools & components
- **verify-layer** — verify-don't-trust layer — prove account/storage state via eth_getProof vs stateRoot. · github.com/trustless-ai/verify-layer
- **recompute-kit** — the toolkit: recompute primitives + recipes + conformance vectors + MCP. · github.com/trustless-ai/recompute-kit
- **agent-sdk** — off-chain SDK — typed contract clients + deploy/test kit for the agent ERCs. · github.com/trustless-ai/agent-sdk
- **ccip-router** — the coordination layer CCIP-Read was missing — peer sync, dedup, mesh. · github.com/trustless-ai/ccip-router
- **zkIE** — Zero-Knowledge Inference Engine (prototype). · github.com/trustless-ai/zkIE
- **recompute-lens** — human surface over recompute-kit — watch an off-chain claim recompute. · github.com/trustless-ai/recompute-lens
- **eip7702-rescue** — forensic MCP + hardened delegate for atomic EIP-7702 asset rescue. · github.com/trustless-ai/eip7702-rescue
- **pq-agent-binding** — recomputable post-quantum key binding for on-chain AI agents. · github.com/trustless-ai/pq-agent-binding
- **agent-ercs** — ERCs + base implementations for the trustless-AI agent stack. · github.com/trustless-ai/agent-ercs

## 📄 PUBLISHED — notes (CC0)
- **collapsed-state-note** — 'A written rule has no failure mode' — collapsed states + the five tiers. · github.com/trustless-ai/collapsed-state-note
- **observation-conditions-note** — 'A reading is incomplete without the conditions that produced it.' · github.com/trustless-ai/observation-conditions-note
- **composed-attestation-note** — four independent commitments over one event — the seam rules. · github.com/trustless-ai/composed-attestation-note

## 🔵 DRAFT — ERCs (in the ERC process)
- **ERC-8299 — WYRIWE — what-you-run-is-what-you-explain (input provenance).** — co-author (TMerlini+Vincent+Fede+Jimmy+Damon). · ethereum/ERCs#1810
- **ERC-8354 — Confidential Agent Policy Verdicts (ZK allow/deny).** — co-maintainer; expiry-bound circuit PR ethereum/ERCs#1989. · ethereum/ERCs (merged #1919)
- **ERC-8373 — Post-Quantum Anchored Key Binding.** — author. · assets/erc-8373 (ethereum/ERCs)
- **ERC-8294 — VNI — Verifiable Network Inference.** — co-author (Tiago). · ethereum/ERCs

---
48 entries. Re-verify: on-chain = `eth_getCode`; recipes = recompute-kit conformance; repos = open them. CC0.
