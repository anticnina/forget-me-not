# ✿ Forget Me Not - Plant Your Memories ✿

Forget-Me-Not is a desktop social memory-mapping application built with Python and PyQt6. It allows you to pin your favorite life moments to real-world locations, create collaborative maps with friends and explore the shared stories of the people you care about.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue)

---
## 🌟 Key Features

### 📍 Interactive Memory Mapping

* **Plant a Flower (lat. *Myosotis* / engl. *Forget-me-not*):** Click anywhere on the interactive world map to "plant" a memory.
* **Rich Details:** Attach a title, a heartfelt description, and a photo to capture the exact vibe of that moment.

### 🗺️ Flexible Map Management

* **Infinite Canvases:** Create as many maps as you want (e.g., *"Summer '25 Roadtrip"*, *"Best Coffee Spots"*).
* **Seamless Switching:** Easily hop between your different maps using the intuitive sidebar navigation.

### 🔒 Smart Privacy & Collaboration

* 🌐 **Public Maps:** Proudly display your adventures on your profile for all your friends to see.
* 🔒 **Private Maps:** Keep your personal journals secure and strictly invite-only.
* 🤝 **Shared Maps:** Create collaborative spaces where you and your friends can all plant memories together.
  <img width="2402" height="1618" alt="my maps" src="https://github.com/user-attachments/assets/db8b8796-c4cd-4f30-a638-7576b0734e29" />


### 👥 Social & Profiles

* **Connect:** Send and accept friend requests to build your inner circle.
* **Explore:** Visit friends' profiles to browse their bios, profile pictures, and public maps.
* **Friends Tab:** Browse all maps belonging to your friends directly from the sidebar — each entry shows the friend's profile picture so you always know whose map it is.

### 📰 Friends Feed

* **Stay in the loop:** The feed is the first thing you see after logging in — a scrollable timeline of every memory your friends have recently planted.
* **Rich cards:** Each post shows the friend's avatar, their username, the map it was posted on, the pin name, description, and photo.
* **Jump to the memory:** Click any feed card to open that map and pan directly to the exact pin, with its popup open.
* **Always accessible:** The **📰 Feed** button in the top bar brings you back to the feed from anywhere in the app.
<img width="2400" height="1614" alt="feed" src="https://github.com/user-attachments/assets/91e48e38-a7a1-4a30-ab4f-effe56cb9051" />

### ⚡ Live Synchronization

* **Real-time Updates:** Pins auto-refresh every 5 seconds, ensuring you see your friends' new memories the moment they plant them.

---

## Tech stack

| Layer | Technology |
|---|---|
| UI | PyQt6 + QWebEngineView |
| Map rendering | Leaflet.js 1.9.4 (bundled locally) |
| Database | PostgreSQL via psycopg2 |
| Auth | bcrypt password hashing |
| Font | Nunito (OFL licensed, bundled) |

---

## Prerequisites

- Python 3.10 or newer
- PostgreSQL 14 or newer
- pgAdmin 4 (optional but recommended for DB setup)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/anticnina/forget-me-not.git
cd forget-me-not
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` includes:
- `PyQt6` and `PyQt6-WebEngine` — UI and embedded map browser
- `psycopg2-binary` — PostgreSQL driver
- `bcrypt` — password hashing
- `Pillow` — image handling

### 4. Set up PostgreSQL

Create a database named `forget_me_not`:

```sql
CREATE DATABASE forget_me_not;
```

Then run the schema. In pgAdmin 4, open the Query Tool against `forget_me_not` and paste the contents of `database/schema.sql`, then press **F5**.

Or from the command line:

```bash
psql -U postgres -d forget_me_not -f database/schema.sql
```

### 5. Configure the database connection

Copy the example config and fill in your credentials:

```bash
cp config.ini.example config.ini
```

Edit `config.ini`:

```ini
[database]
host = localhost
port = 5432
dbname = forget_me_not
user = postgres
password = your_password_here
```

> **Important:** `config.ini` is listed in `.gitignore` and will never be committed. Never share it publicly — it contains your database password.

### 6. Run the app

```bash
python main.py
```

---

## Project structure

```
forget-me-not/
├── main.py                  # Entry point — boots Qt, loads fonts, opens login
├── config.ini               # Your local DB credentials (git-ignored)
├── config.ini.example       # Safe template to commit
├── requirements.txt
│
├── database/
│   ├── connection.py        # Singleton psycopg2 connection, execute() helper
│   └── schema.sql           # Full DDL — run once to create all tables
│
├── models/
│   ├── user.py              # User dataclass + CRUD (create, login, update profile)
│   ├── map_model.py         # Map CRUD, privacy, collaborators, access checks
│   ├── pin.py               # Pin CRUD + FeedItem + get_feed_for_user()
│   ├── friendship.py        # Friend requests, accept/decline, friend list
│   └── map_invitation.py    # Private map invite flow
│
├── ui/
│   ├── login_window.py      # Login dialog
│   ├── signup_window.py     # Sign-up dialog with profile photo
│   ├── main_window.py       # Main window — sidebar, feed/map stack, top bar
│   ├── map_view.py          # Leaflet map widget + pin dialog launcher
│   ├── feed_panel.py        # Friends feed — scrollable post cards
│   ├── friends_panel.py     # Search users, send/manage friend requests
│   ├── profile_window.py    # View/edit own profile; view friends' profiles
│   └── pin_dialog.py        # Add-pin form (name, description, photo)
│
├── utils/
│   ├── flower.py            # Renders the 🌸 emoji with a blue hue filter
│   ├── avatar.py            # Circular profile picture clipping with border
│   └── auth.py              # bcrypt helpers
│
└── assets/
    ├── leaflet/             # Leaflet.js + CSS (bundled, no CDN required)
    ├── fonts/               # Nunito font family (OFL licensed)
    └── _map.html            # Generated at runtime — do not edit manually
```

---

## Database schema overview

```
users
  └─< maps (creator_id)
        └─< pins (map_id)
        └─< map_collaborators (map_id ↔ user_id)

users
  └─< friendships (user_id1, user_id2)
  └─< map_invitations (sender_id, recipient_id)
```

Key design decisions:
- Friendships are stored as a single row with `user_id1 < user_id2` to avoid duplicates
- `map_collaborators` tracks who has been explicitly invited to a private map; only collaborators and the owner can add pins
- Public maps are viewable by everyone but still write-protected

---

## Pin permissions

| User | Can view | Can add pins |
|---|---|---|
| Map owner | ✅ | ✅ |
| Invited collaborator | ✅ | ✅ |
| Friend (public map) | ✅ | ❌ |
| Anyone else | ❌ | ❌ |

---

## Troubleshooting

**"Could not connect to PostgreSQL"** on startup
→ Make sure PostgreSQL is running and `config.ini` has the correct credentials.

**Map tiles don't load**
→ The app needs internet access to fetch OpenStreetMap tiles. The Leaflet library itself is bundled and works offline.

**Blank map panel**
→ Select a map from the left sidebar first.

**Profile photos don't appear after moving files**
→ Photos are stored by their original file path. If you move the source image, the path breaks. A future version will copy images into the app's data folder.

---

## License

The application code is released under the [MIT License](LICENSE).

The Nunito font (`assets/fonts/`) is licensed under the [SIL Open Font License 1.1](https://scripts.sil.org/OFL).

Leaflet.js (`assets/leaflet/`) is licensed under [BSD 2-Clause](https://leafletjs.com/license).

Map tiles are © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).
