from lnbits.db import Connection


async def m001_initial(db: Connection):
    """Initial laisee table."""
    await db.execute(f"""
        CREATE TABLE laisee.laisees (
            id TEXT PRIMARY KEY,
            wallet TEXT NOT NULL,
            title TEXT NOT NULL,
            min_sats {db.big_int} NOT NULL DEFAULT 1,
            max_sats {db.big_int} NOT NULL DEFAULT 1,
            unique_hash TEXT UNIQUE NOT NULL,
            k1 TEXT NOT NULL,
            is_paid BOOLEAN NOT NULL DEFAULT FALSE,
            is_withdrawn BOOLEAN NOT NULL DEFAULT FALSE,
            payment_hash TEXT,
            paid_amount {db.big_int} NOT NULL DEFAULT 0,
            memo TEXT,
            created_at TIMESTAMP DEFAULT {db.timestamp_column_default},
            paid_at TIMESTAMP,
            withdrawn_at TIMESTAMP
        );
    """)


async def m002_add_comment(db: Connection):
    """Add comment support: allow_comment flag and comment storage."""
    await db.execute(
        "ALTER TABLE laisee.laisees ADD COLUMN allow_comment BOOLEAN NOT NULL DEFAULT FALSE"
    )
    await db.execute("ALTER TABLE laisee.laisees ADD COLUMN comment TEXT")
