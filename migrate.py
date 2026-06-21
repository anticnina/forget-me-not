"""Apply schema additions to an existing forget_me_not database."""
import psycopg2

DDL = """
CREATE TABLE IF NOT EXISTS map_invitations (
    id           SERIAL PRIMARY KEY,
    sender_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status       VARCHAR(20) NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'accepted', 'declined')),
    map_id       INTEGER REFERENCES maps(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_map_inv_recipient ON map_invitations(recipient_id);
CREATE INDEX IF NOT EXISTS idx_map_inv_sender    ON map_invitations(sender_id);
"""

conn = psycopg2.connect(
    host="localhost", port=5432, dbname="forget_me_not",
    user="postgres", password="postgres"
)
conn.autocommit = True
cur = conn.cursor()
cur.execute(DDL)
cur.close()
conn.close()
print("Migration complete — map_invitations table is ready.")
