# ER-Modell — Momentum (Stand M6)

Alle Tabellen entsprechen dem SQLAlchemy-Schema in `models.py`.

---

## Entity: User

| Typ | Feld | Constraint | Hinweis |
|---|---|---|---|
| int | id | PK | |
| string(120) | email | UK, idx | lower-cased beim Schreiben |
| string(255) | password_hash | NOT NULL | pbkdf2:sha256 |
| string(80) | name | NOT NULL | |
| int | age | | nullable |
| string(80) | city | | nullable; Distanz-Filter via ILIKE |
| text | bio | | nullable |
| bool | notify_email | NOT NULL | default True; E-Mail-Notification an/aus (FA-10 AK2) |
| datetime | created_at | | |

Property (kein DB-Feld): `photo_url` → primäres Foto aus `Photo`; Fallback auf neuestes.

Property (kein DB-Feld): `streak` → längste Kette aufeinanderfolgender Tage mit
Check-in, die heute oder gestern endet; eine Lücke setzt sie zurück (FA-08). Berechnet
aus `Checkin.checkin_date`, daher kein gespeicherter Zähler.

---

## Entity: Goal

| Typ | Feld | Constraint | Hinweis |
|---|---|---|---|
| int | id | PK | |
| int | user_id | FK → User, idx | NOT NULL; cascade delete |
| string(40) | goal_category | NOT NULL | Lernen / Projekt / Sport / Gewohnheit |
| string(280) | goal_text | NOT NULL | freier Text |
| string(40) | frequency | | nullable; Freitext |
| string(20) | preferred_checkin_time | | nullable; z.B. "08:00" |
| datetime | created_at | | |

Beziehung: n Goal → 1 User · 1 Goal → n Checkin (nullable)

---

## Entity: Photo

| Typ | Feld | Constraint | Hinweis |
|---|---|---|---|
| int | id | PK | |
| int | user_id | FK → User, idx | NOT NULL; cascade delete |
| string(300) | url | NOT NULL | relativ (static/uploads/…) oder extern |
| bool | is_primary | NOT NULL | default False |
| datetime | uploaded_at | | |

Beziehung: n Photo → 1 User. Nur ein Foto je User sollte `is_primary=True` haben.

---

## Entity: Connection

| Typ | Feld | Constraint | Hinweis |
|---|---|---|---|
| int | id | PK | |
| int | user1_id | FK → User | Initiator der Anfrage |
| int | user2_id | FK → User | Empfänger der Anfrage |
| string(20) | status | NOT NULL | `requested` \| `active` |
| datetime | created_at | | |
| datetime | updated_at | | onupdate |

Constraints: UniqueConstraint(user1_id, user2_id)  
Indexes: (user1_id, status) · (user2_id, status)

Beziehung: n Connection → 1 User (als user1) · n Connection → 1 User (als user2)  
1 Connection → n Message (cascade delete)

---

## Entity: Message

| Typ | Feld | Constraint | Hinweis |
|---|---|---|---|
| int | id | PK | |
| int | connection_id | FK → Connection, idx | NOT NULL; cascade delete |
| int | sender_id | FK → User, idx | NOT NULL |
| text | text | NOT NULL | |
| datetime | sent_at | idx | default utcnow |

Index: (connection_id, sent_at) für chronologischen Abruf.

Beziehung: n Message → 1 Connection · n Message → 1 User (sender)

---

## Entity: Checkin

| Typ | Feld | Constraint | Hinweis |
|---|---|---|---|
| int | id | PK | |
| int | user_id | FK → User, idx | NOT NULL |
| int | goal_id | FK → Goal, idx | nullable — Checkin muss keinem Goal zugeordnet sein |
| date | checkin_date | NOT NULL | |
| text | note | | nullable |
| datetime | created_at | | |

Index: (user_id, checkin_date) für Streak-Berechnung.

Beziehung: n Checkin → 1 User · n Checkin → 0..1 Goal

---

## Beziehungsübersicht

```
User ─────1:n──── Goal
User ─────1:n──── Photo
User ─────1:n──── Checkin
User ─────1:n──── Connection  (als user1, Initiator)
User ─────1:n──── Connection  (als user2, Empfänger)
User ─────1:n──── Message     (als sender)
Goal ─────1:n──── Checkin     (nullable FK)
Connection ──1:n── Message
```

---

## Domain-Helfer (models.py, kein DB-Feld)

### `match_score(user_a, user_b) → int`

Berechnet die Übereinstimmung zwischen zwei Nutzern auf Basis ihrer Goals.

| Kriterium | Punkte |
|---|---|
| ≥ 1 gemeinsame `goal_category` | +2 |
| ≥ 1 gemeinsame `frequency` | +1 |
| ≥ 1 gemeinsamer `preferred_checkin_time` | +1 |
| **Maximum** | **4** |

Vergleich per Mengenüberschneidung (Set-Intersection) aller Goals beider Nutzer.

### `Connection.between(user_a_id, user_b_id) → Connection | None`

Findet die Connection zwischen zwei Nutzern unabhängig davon, wer `user1` (Initiator) und wer `user2` (Empfänger) ist. Gibt `None` zurück, wenn keine Verbindung existiert.

### `Connection.active_for(user_id) → list[Connection]`

Alle aktiven Partnerschaften eines Nutzers, nach letzter Aktivität sortiert — Datenbasis für die Partner-/Chat-Liste auf dem Profil.

### `Connection.involves(user_id) → bool` · `Connection.partner_of(user) → User`

`involves` ist das Zugriffs-Gate für den Chat (nur die beiden Partner, NFA-03 / FA-07 AK3). `partner_of` liefert den jeweils anderen Partner relativ zum angemeldeten Nutzer.

### `due_reminders(user, *, now=None) → list[Goal]`

Liefert die Goals, deren Check-in heute fällig und noch nicht erledigt ist (FA-09). Der „Schedule" ist die `frequency` + `preferred_checkin_time` des Goals (kein separates Entity). Ein Goal ist fällig, wenn eine Check-in-Zeit gesetzt ist, die aktuelle Uhrzeit sie überschritten hat und für das Goal heute kein `Checkin` existiert. `now` ist injizierbar (deterministisch testbar). In-App-Trigger ohne Hintergrundjob.

## KI-Coach & E-Mail (kein DB-Feld)

`coach.py` (FA-11): `sharpen_goal()`/`motivational_message()` über die Anthropic-API mit lokalem Offline-Fallback; die Prompts enthalten nur Ziel-Text bzw. Streak-Zahl (NFA-09). `mailer.py` (FA-10): `notify(user, …)` sendet nur, wenn `user.notify_email` gesetzt ist; ohne `MAIL_SERVER` wird nur geloggt.
