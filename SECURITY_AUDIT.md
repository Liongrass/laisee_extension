# Laisee Extension — Security Audit (2026-09-04)

Adversarial audit of `laisee` v0.7 against a live Bitcoin+Lightning regtest stack
(bitcoind + litd×2 + lnd + LNbits×4). All findings were **reproduced live before
patching** and **re-attacked after patching**; the full 25-assertion integration
suite passes with the fixes applied.

## Severity summary

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| 1 | Multi-funder race → silent over-collection | High | Fixed |
| 2 | Read-only invoice key leaks the claim credential | High | Fixed |
| 3 | Wallet ownership bypass on create | High | Fixed |
| 4 | HTTP 500 on malformed invoice | Low | Fixed |
| 5 | Asymmetric ±1 sat claim tolerance admits over-claims | Low | Fixed |

---

## 1. Multi-funder race → silent over-collection (High)

**Root cause.** `pay-cb` minted a brand-new BOLT11 on **every call** while the
envelope was unfunded. The only guard was `is_paid`, which flips asynchronously
(invoice-listener task) after a payment settles. Lightning cannot recall an issued
invoice, so every invoice ever minted stays payable indefinitely.

**Exploit (executed).**
1. Create envelope (10–1000 sats).
2. Call `pay-cb` twice → two distinct invoices (100 sats, 500 sats).
3. Pay **both** → both `SUCCEEDED`.
4. Owner wallet credited **+600**; envelope row shows `paid_amount=100` and only
   ever offers a 100-sat withdrawal.
5. The extra 500 sats are an unattributed donation — no error to the payer, no
   refund path, no UI signal. A stale invoice minted earlier remains payable even
   *after* the envelope is fully funded.

An operator sharing the QR publicly over-collects unboundedly; every funder after
the first silently loses their sats.

**Fix.** Atomic single-invoice binding:
- `pending_payment_hash` + `pending_created_at` columns (migrations m003/m004).
- `bind_laisee_funding_invoice()` — conditional `UPDATE` that only succeeds while
  unfunded and no live pending invoice exists (or the previous one expired).
- `pay-cb` refuses with `"already being funded"` while a pending invoice is live.
- `clear_laisee_pending_invoice()` releases the slot on settle; a 1-hour timeout
  (matching LN invoice expiry) releases abandoned invoices.

**Trade-off.** An abandoned funding invoice blocks new funding attempts for up to
1 hour — the cost of closing the race.

## 2. Read-only invoice key leaks the claim credential (High)

**Root cause.** `GET /laisees` and `GET /laisees/{id}` accept LNbits' **invoice
key** (the "read-only, safe to share" credential) and returned the full `Laisee`
model, including `unique_hash` and `k1`. Together those two fields **are** the
LNURL-withdraw bearer link: `GET /lnurl/<hash>` + `withdraw-cb/<hash>?k1=<k1>`
pays out with no other auth — by design, since the claim link is a QR handed to
the recipient.

**Exploit (executed).**
1. Create + fund an envelope with the admin key.
2. `GET /laisees/{id}` with the **invoice key only** → response includes
   `unique_hash` + `k1`.
3. Hit `withdraw-cb` with those values → `{"status":"OK"}`, 100 sats moved out.

This breaks LNbits' security contract: the invoice key is designed to be shared
(mobile wallet pairing QR codes, dashboards, integrations) precisely because it
cannot spend. Laisee silently re-grants spend power over funded envelopes.

**Caveat on preconditions.** How an attacker obtains the invoice key in the first
place is unclear — the owner must share it; no escalation path from invoice key →
admin key was found, and no unauthenticated leaks. Severity depends on whether you
treat the invoice key as a shared credential (its documented purpose).

**Fix.** `_redact_claim_fields()` strips `unique_hash`/`k1`/`lnurl`/`lnurl_url`
from list/detail responses unless the caller presented the **admin key**.

## 3. Wallet ownership bypass on create (High)

**Root cause.** `CreateLaiseeData.wallet` was used verbatim with no check that it
belongs to the authenticated user. The wallet ID controls both money-moving calls:
`create_invoice(wallet_id=…)` at funding and `pay_invoice(wallet_id=…)` at claim.

**Exploit (executed end-to-end on a single-instance multi-user setup).**
1. Fund victim's wallet with 5000 sats.
2. Attacker creates an envelope with `wallet=<victim's wallet id>` → **201 accepted**.
3. Anyone funds the envelope → +1000 sats land in the **victim's** wallet
   (unexplained credit).
4. Attacker claims via the LNURL-withdraw link → **-1000 sats paid out of the
   victim's balance**. Victim never touched the extension.

**Fix.** `POST /laisees` now rejects with 403 `"Cannot create a laisee for another
wallet."` when `data.wallet` ≠ the authenticated wallet.

## 4. HTTP 500 on malformed invoice (Low)

**Root cause.** `decode_bolt11(pr)` was called unguarded in `withdraw-cb`. `pr` is
attacker-controlled, unauthenticated input; `decode_bolt11` raises on bad input,
and the exception propagated to LNbits' generic middleware → HTTP 500
`{"detail":"Unexpected error! ID: …"}`.

**Why it matters.** (a) Violates the LNURL protocol — all failure modes must be
`{"status":"ERROR","reason":…}` with HTTP 200; wallets see an opaque crash instead
of a useful message. (b) Free log-spam / minor DoS: each hit logs a full traceback
plus a unique exception ID.

**Fix.** Wrapped in `try/except` → `LnurlErrorResponse(reason="Invalid invoice.")`.
Verified: junk string, truncated invoice, empty, and emoji inputs all return the
clean error with HTTP 200, zero 500s in logs.

## 5. Asymmetric ±1 sat claim tolerance admits over-claims (Low)

**Root cause.** `abs(amount_msat - expected) > 1000` rejects — i.e. an invoice up
to **1 sat above** the funded amount passed the extension's own validation. Only
LNbits **core's** `max_sat=paid_amount` parameter caught the over-claim attempt
downstream — defense by accident, in different code.

**Why it matters.** If `max_sat` handling ever changed (or the call site were
refactored), every envelope would pay out 1 sat more than funded — a slow drain.
Worse, the over-claim passed validation, hit the atomic claim (`is_withdrawn=TRUE`),
*then* failed in core, forcing a claim revert — needless DB churn and a race window.
Under-tolerance is legitimate (routing-fee rounding shaves a sat); over-tolerance
never is.

**Fix.** `amount > expected` rejected outright; tolerance kept only on the under
side (`expected - amount > 1000` rejects). Verified: 101 sats rejected *before* the
atomic claim (envelope stays claimable), 99 accepted, 98 rejected.

---

## Verified NOT vulnerable

- **Concurrent double-withdraw** — 6 parallel claims over distinct invoices →
  exactly 1 `OK`, 5 `ERROR`. The atomic `UPDATE … WHERE is_withdrawn = FALSE`
  invariant holds. Now covered by a dedicated regression test.
- Wrong k1 rejected; replay-after-spend rejected; LNURL retires after claim.
- Negative/zero/over-max funding amounts rejected.
- Revert-on-failure correctly re-opens the envelope after a failed claim payment.
- Semgrep (owasp-top-ten, security-audit, python) — all clean; these are logic
  flaws static analysis cannot see.

## Regression coverage

- New test: 6-way concurrent-claim race → exactly one winner.
- Happy path (create → fund → withdraw) re-verified after every change.
- Full 25-assertion integration suite: **25/25 passing**.
