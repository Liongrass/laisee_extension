# Laisee — Digital Red Envelopes for LNbits

A **laisee** is a digital red envelope powered by Lightning. Create one and share the QR code. The same QR code serves two purposes in sequence:

1. **Unfunded** — the QR encodes an LNURL-pay. The first person to scan it funds the envelope with sats.
2. **Funded** — the moment the payment settles, the QR becomes an LNURL-withdraw. Anyone who scans it can pull the sats out.
3. **Withdrawn** — once redeemed, the envelope is spent.

The QR code never changes. The protocol underneath it does.

## States

| State | Meaning |
|-------|---------|
| 🟠 Unfunded | Waiting for the first payment |
| 🟢 Funded | Payment received; ready to withdraw |
| ⚫ Withdrawn | Sats have been claimed |

## Usage

1. Install the extension in LNbits.
2. Click **New Laisee**, pick a wallet, give it a title, and set a sat amount (or a min/max range).
3. Click the **visibility** icon on any row to see its QR code and LNURL.
4. Share the QR. The sender scans and pays; the recipient scans and withdraws.

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/laisee/api/v1/laisees` | Invoice key | List all laisees |
| `POST` | `/laisee/api/v1/laisees` | Admin key | Create a laisee |
| `DELETE` | `/laisee/api/v1/laisees/{id}` | Admin key | Delete a laisee |

Full schema is available in the Swagger docs at `/docs#/laisee`.

## Requirements

- LNbits 1.0.0 or later
