-- =============================================================
-- Forget Me Not — PostgreSQL DDL
-- Run in pgAdmin 4 Query Tool against the "forget_me_not" DB.
-- =============================================================

-- ── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id               SERIAL PRIMARY KEY,
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    username         VARCHAR(50)  UNIQUE NOT NULL,
    password_hash    TEXT         NOT NULL,
    profile_pic_path TEXT,
    bio              TEXT,
    created_at       TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Friendships ───────────────────────────────────────────────
-- user_id1 < user_id2 is enforced so every pair has exactly one row.
-- The sender is tracked via the 'requester_id' column so we know
-- who initiated the request without duplicating the row.
CREATE TABLE IF NOT EXISTS friendships (
    user_id1     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_id2     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status       VARCHAR(20) NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'accepted', 'declined')),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id1, user_id2),
    CHECK (user_id1 < user_id2)
);

-- ── Maps ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS maps (
    id          SERIAL PRIMARY KEY,
    creator_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    is_private  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Map Collaborators (Many-to-Many) ─────────────────────────
-- Stores users who were explicitly invited to a private map.
CREATE TABLE IF NOT EXISTS map_collaborators (
    map_id    INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (map_id, user_id)
);

-- ── Pins (Forget-me-not flower markers) ──────────────────────
CREATE TABLE IF NOT EXISTS pins (
    id          SERIAL PRIMARY KEY,
    map_id      INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
    creator_id  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    person_name VARCHAR(200) NOT NULL,
    description TEXT,
    image_path  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Map Invitations ──────────────────────────────────────────
-- A user sends a map invitation to a friend.
-- On acceptance a shared private map is auto-created and both become members.
CREATE TABLE IF NOT EXISTS map_invitations (
    id           SERIAL PRIMARY KEY,
    sender_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status       VARCHAR(20) NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'accepted', 'declined')),
    map_id       INTEGER REFERENCES maps(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_friendships_user2    ON friendships(user_id2);
CREATE INDEX IF NOT EXISTS idx_maps_creator         ON maps(creator_id);
CREATE INDEX IF NOT EXISTS idx_map_collab_user      ON map_collaborators(user_id);
CREATE INDEX IF NOT EXISTS idx_pins_map             ON pins(map_id);
CREATE INDEX IF NOT EXISTS idx_pins_creator         ON pins(creator_id);
CREATE INDEX IF NOT EXISTS idx_map_inv_recipient    ON map_invitations(recipient_id);
CREATE INDEX IF NOT EXISTS idx_map_inv_sender       ON map_invitations(sender_id);
