# PROJECT.md — Engineering-Audit-Trail

## 1. Projektzusammenfassung

**GrindMate** ist eine Accountability-Partner-Web-App (Flask/Python): Nutzer legen
ein Zielprofil an, finden über eine parametrische Suche und einen Match-Algorithmus
passende Partner, verbinden sich, chatten 1:1 und halten sich per Check-in
gegenseitig auf Kurs. Geplante Sonderfunktionen: Check-in-Schedule/Erinnerungen,
E-Mail-Notification und ein KI-Coach.

Quelle der Wahrheit für den Funktionsumfang ist `doc/anforderungskatalog.md`
(FA-01…FA-16, NFA-01…NFA-09, MoSCoW-priorisiert). Die Meilensteine unten
referenzieren diese IDs.

## 2. Rahmen & Termine

Blockwoche FS2026 mit tageweisen Zielen (Tag 1–3), Hack-Werkstatt Do/Fr,
anschließend Abgabe am `04.07.2026`. Datumsangaben unten
sind entsprechend als Richtwerte zu lesen.

Benotung: 4.0 = alle Grundfunktionen + 3 Sonderfunktionen + 3 Artefakte
(Git-Release, Video-Demo, Tagebuch). Richtung 6.0 = exzellentes UX + Zusatz­
funktionen; Front- und Backend werden bewertet.

## 3. Meilenstein-Checkliste

- [x] **M0** — Setup & vertikaler Durchstich (Login + persönliches Profil)
- [x] **M1** — Startseite & Registrierung (User selbst anlegen)
- [x] **M2** — Profil bearbeiten, Foto-Upload, Fremdprofil-Ansicht (View)
- [x] **M3** — Vollständiges Datenmodell (Connection, Message, Checkin)
- [x] **M4** — Suche, Match-Algorithmus & Verbindung
- [x] **M5** — 1:1-Chat & Check-in
- [x] **M6** — Sonderfunktionen: Check-in-Schedule, E-Mail-Notification, KI-Coach
- [x] **M7** — UX-Politur & Zusatzfunktionen (Richtung 6.0)
- [ ] **M8** — Testlauf, Test-Prozeduren, Bug-Liste, MySQL-Integration
- [ ] **M9** — Abgabe (Git-Release, Video-Demo, Tagebuch)

Nach **M5** sind alle Grundfunktionen erfüllt, nach **M6** die drei
Sonderfunktionen — zusammen mit den Artefakten aus **M9** ist damit die 4.0
abgedeckt. M7/M8 zielen auf die Note Richtung 6.0.

---

## 4. Meilenstein-Einträge

### M0 — Setup & vertikaler Durchstich · erledigt

- **Datum:** Tag 1 (Richtwert; Block-Datum bestätigen)
- **Ziel:** Lauffähiges Flask-Grundgerüst mit Login und Anzeige des persönlichen
  Profils; kompletter Durchstich Controller → Entities → Datenbank.
- **Was geändert wurde:** App-Factory `create_app()` in `__init__.py` (DB, Login,
  Blueprint-Registrierung, `create_all`); `User`-Entity in `models.py`; `LoginForm`
  in `forms.py`; Auth-Controller `auth.py` (Login/Logout); `views.py` mit
  `/profile`; `seed.py` mit CLI `flask seed` und 10 Dummy-Profilen; Templates
  `base`, `login`, `profile`; UI-Identität in `static/style.css`. SQLite als
  Entwicklungs-DB.
- **How to run:** `flask --app main seed` dann `flask --app main run --debug`.
- **How to test:** Login mit Demo-Account → Profil zeigt DB-Daten; `/profile` ohne
  Login leitet auf den Login um.
- **Deckt ab:** FA-01 (Login), FA-03 (teilweise), NFA-01, NFA-02, NFA-07, NFA-08.
- **Known issues / Entscheidungen:** App-Package liegt im Repo-Root (passt zum
  Dozenten-Starter); Passwort-Hashing auf `pbkdf2:sha256` umgestellt, weil
  `scrypt` auf manchen macOS-Python-Builds fehlt.
- **Next steps:** Registrierung und Startseite (→ M1).

### M1 — Startseite & Registrierung · erledigt

- **Datum:** Tag 1–2 (Richtwert)
- **Ziel:** Eigenständige Startseite mit klaren CTAs; Nutzer können selbst Konten
  inklusive Profil anlegen.
- **Was geändert wurde:** `views.index` rendert die Landing-Page (`landing.html`)
  bzw. leitet eingeloggte Nutzer aufs Profil; `RegistrationForm` in `forms.py`
  (E-Mail eindeutig, Passwort min. 8 Zeichen + Bestätigung, Zielkategorie als
  Auswahl); `auth.register` legt User mit Profilfeldern an, loggt ein und leitet
  aufs Profil; Default-Avatar aus der E-Mail; Templates `landing.html`,
  `register.html`, Verlinkung von der Login-Seite, Gäste-Navigation.
- **How to run:** Server starten, `/` öffnen → „Konto erstellen".
- **How to test:** Registrierung mit neuer E-Mail legt Account an und loggt ein;
  doppelte E-Mail und Passwort-Mismatch werden am Feld abgewiesen; Login mit dem
  neuen Account funktioniert.
- **Deckt ab:** FA-01 (vollständig, AK1–AK3), FA-02 (Anlegen, teilweise),
  NFA-04, NFA-08.
- **Known issues / Entscheidungen:** Profil-Bearbeitung und Foto-Upload noch offen
  (→ M2). Standard-Avatar extern geladen (Internet nötig).
- **Next steps:** Profilbearbeitung, Foto-Upload, Fremdprofil-Ansicht (→ M2).

### M2 — Profil bearbeiten, Foto-Upload, Fremdprofil-Ansicht · erledigt

- **Datum:** 30.06.2026
- **Ziel:** Vollständige Erfüllung von „View": eigenes Profil bearbeiten, Foto
  hochladen und Profile anderer Nutzer ansehen.
- **Was geändert wurde:** `EditProfileForm` in `forms.py` (alle Profilfelder +
  `FileField` mit `FileAllowed`); Route `GET/POST /profile/edit` und
  `GET /u/<int:user_id>` in `views.py`; Templates `edit_profile.html` und
  `user_profile.html` (neu); `profile.html` mit „Profil bearbeiten"-Button;
  `__init__.py` mit `UPLOAD_FOLDER` (`static/uploads/`) und
  `MAX_CONTENT_LENGTH` (5 MB); `conftest.py` (Root) + `tests/conftest.py` +
  `tests/test_m2.py` (4 Tests).
- **How to run:** `flask --app main run --debug` → Profil aufrufen →
  „Profil bearbeiten" → Formular ausfüllen und optional Foto hochladen.
  Fremdprofil: `/u/<id>` (eingeloggt).
- **How to test:** `pytest tests/test_m2.py -v` → 4 passed.
- **Deckt ab:** FA-02 (AK1–AK3), FA-03 (AK1–AK2).
- **Known issues / Entscheidungen:** Fotos lokal in `static/uploads/`
  gespeichert (kein CDN). Kein Bildresizing (Pillow nicht installiert) — bei
  Bedarf in M7 nachrüsten. `/u/<id>` ist login-required (passend zur
  späteren Match-Logik).
- **Next steps:** Vollständiges Datenmodell (Connection, Message, Checkin) → M3.
  `Goal`-Entity wurde vorgezogen und als Teil dieses Features umgesetzt.

### M2.5 — Mehrere Commitments pro User · erledigt

- **Datum:** 30.06.2026
- **Ziel:** User kann beliebig viele Commitments anlegen, bearbeiten und löschen.
- **Was geändert wurde:** `Goal`-Entity in `models.py` (1:n zu User;
  `goal_category`, `goal_text`, `frequency`, `preferred_checkin_time`); diese
  Felder von `User` entfernt (Clean Slate); `GoalForm` in `forms.py`;
  Registrierung legt erstes `Goal` via Relationship an (`auth.py`); Routen
  `GET/POST /goals/new` und `POST /goals/<id>/delete` (403 bei fremdem Goal)
  in `views.py`; `goal_form.html` (neu); `profile.html` und `user_profile.html`
  mit Goal-Liste; `CSRFProtect` in `__init__.py` (macht `csrf_token()` in
  Templates verfügbar); `seed.py` mit separaten Goal-Objekten; `test_goals.py`
  (4 Tests).
- **How to run:** Schema-Reset (`flask --app main seed` nach DB-Löschung) →
  Profil → „+ Hinzufügen" → neues Commitment. Löschen per ✕-Button.
- **How to test:** `pytest tests/ -v` → 8 passed (test_m2 + test_goals).
- **Deckt ab:** Userwunsch mehrere Ziele; Datenbasis für Match-Algorithmus (M4).
- **Known issues / Entscheidungen:** Kein Edit einzelner Goals (nur Löschen +
  neu anlegen) — reicht für MVP; Edit-Route optional in M7.
- **Next steps:** Vollständiges Datenmodell (Connection, Message, Checkin) → M3.

### M3 — Vollständiges Datenmodell · erledigt

- **Datum:** 30.06.2026
- **Ziel:** ER-Modell um alle verbleibenden Grundfunktions-Entities erweitern;
  Foto-Ablage sauber in eine eigene Entity überführen.
- **Was geändert wurde:**
  - `Photo`-Entity (neu): 1:n zu User, Felder `url`, `is_primary`, `uploaded_at`;
    ersetzt die `photo_url`-Spalte auf `User` vollständig (Clean-Slate-Regel).
    `User.photo_url` bleibt als Python-Property erhalten, sodass Templates
    unverändert bleiben.
  - `Connection`-Entity (neu): zwei User-FKs (`user1_id` Initiator, `user2_id`
    Empfänger), Status `requested`/`active`, `UniqueConstraint` auf dem Paar,
    zusammengesetzte Indizes auf `(user1_id, status)` und `(user2_id, status)`.
  - `Message`-Entity (neu): FK auf Connection und sender (User), `text`, `sent_at`
    (indiziert), zusammengesetzter Index `(connection_id, sent_at)`.
  - `Checkin`-Entity (neu): User-FK (mandatory), Goal-FK (nullable), `checkin_date`
    (Date), `note`, zusammengesetzter Index `(user_id, checkin_date)`.
  - `User`: `photo_url`-Spalte entfernt; Relationships auf `Photo`, `Checkin`,
    `connections_sent`, `connections_received`, `messages_sent` ergänzt.
  - `Goal`: Relationship auf `Checkin` ergänzt.
  - `views.py`: `edit_profile` legt beim Foto-Upload ein `Photo`-Objekt an statt
    direkt `user.photo_url` zu setzen; alte primäre Fotos werden dabei demarkiert.
  - `seed.py`: `photo_url` aus User-Dicts entfernt, stattdessen `Photo`-Objekte;
    Demo-Daten für 4 Connections (3 aktiv, 1 angefragt), 9 Messages auf aktiven
    Connections, Checkins für 6 User über die letzten 7 Tage.
  - `tests/conftest.py`: `test_user`-Fixture erstellt Photo-Objekt statt
    `photo_url`-Kwarg.
  - `tests/test_goals.py`: `photo_url`-Kwarg beim Hilfs-User entfernt.
  - `tests/test_m3.py` (neu): 5 Tests.
- **How to run:** Schema-Reset nötig (neue Tabellen): `rm instance/app.db` →
  `flask --app main seed` → `flask --app main run --debug`.
- **How to test:** `pytest tests/ -v` → 13 passed (test_goals 4 + test_m2 4 +
  test_m3 5).
- **Deckt ab:** NFA-01 (Datenbasis für Match, Chat, Check-in vollständig).
- **Known issues / Entscheidungen:** Foto-Upload speichert weiterhin lokal in
  `static/uploads/`; `photo_url`-Property gibt das primäre Foto zurück, bei keinem
  primären das neueste. Goal-FK auf Checkin ist nullable — ein Check-in muss keinem
  konkreten Ziel zugeordnet sein. Migrationen weiterhin aufgeschoben (Prototyp-Phase).
- **Next steps:** Suche, Match-Algorithmus & Verbindung → M4.

### M4 — Suche, Match-Algorithmus & Verbindung · erledigt

- **Datum:** 30.06.2026
- **Ziel:** Partner finden, bewerten und verbinden.
- **Was geändert wurde:**
  - `match_score(user_a, user_b)` in `models.py`: Domain-Funktion auf Modulebene.
    Score 0–4: +2 Kategorie-Überlappung, +1 Frequenz-Überlappung, +1 Check-in-Zeit-Überlappung.
  - `Connection.between(user_a_id, user_b_id)` in `models.py`: findet eine
    Connection unabhängig von der Richtung (user1/user2).
  - `SearchForm` in `forms.py`: SelectField für Kategorie + Frequenz, StringField
    für Stadt/Ort; CSRF deaktiviert (GET-Formular).
  - `FREQUENCY_CHOICES` in `forms.py`: gemeinsame Frequenz-Auswahl.
  - Neue Routen in `views.py`: `GET /search`, `POST /connect/<user_id>`,
    `POST /connections/<conn_id>/accept`, `POST /connections/<conn_id>/decline`.
  - `profile()` gibt jetzt `pending_requests` (eingehende Anfragen) mit.
  - `user_profile()` gibt `connection` (aktueller Verbindungsstatus) mit.
  - `templates/search.html` (neu): Suchformular + scorierte Ergebnisliste +
    Verbinden/Annehmen/Ablehnen-Buttons, Leer-Meldung.
  - `templates/profile.html`: Abschnitt für eingehende Verbindungsanfragen.
  - `templates/user_profile.html`: Verbindungsstatus und Aktionsbuttons.
  - `templates/base.html`: Nav um „Suche"- und „Profil"-Links erweitert.
  - `static/style.css`: `.avatar-sm`, `.score-badge`, `.pill-success`,
    `.nav-link-text`.
  - `tests/test_m4.py` (neu): 9 Tests.
- **How to run:** `flask --app main seed` → `flask --app main run --debug` →
  einloggen → „Suche" in der Nav → Filter setzen → Verbinden-Button.
- **How to test:** `pytest tests/ -v` → 22 passed (4 + 4 + 5 + 9).
- **Deckt ab:** FA-04 (AK1–AK3), FA-05 (AK1–AK3), FA-06 (AK1–AK2), NFA-05.
- **Known issues / Entscheidungen:** „Distanz" ist City-Substring-Match (kein
  Geocoding). Frequenz-Filter exakter Match auf SelectField-Werte — Nutzer mit
  Freitext-Frequenz erscheinen ggf. nicht. Chat-Route (M5) noch offen; die
  `active`-Connection ist die Voraussetzung dafür.
- **Next steps:** 1:1-Chat & Check-in → M5.

### M5 — 1:1-Chat & Check-in · erledigt

- **Datum:** 30.06.2026
- **Ziel:** Kommunikation und der wiederkehrende Kern-Loop.
- **Was geändert wurde:**
  - `User.streak`-**Spalte entfernt**, ersetzt durch eine berechnete Property
    (Clean-Slate): längste Kette aufeinanderfolgender Tage mit Check-in, die heute
    oder gestern endet. Ein neuer Check-in verlängert die Kette (FA-08 AK1), eine
    Lücke setzt sie zurück (FA-08 AK2). Templates bleiben unverändert (nutzen
    weiterhin `user.streak`), analog zur `photo_url`-Property.
  - `Connection`-Helfer in `models.py`: `active_for(user_id)` (aktive
    Partnerschaften), `involves(user_id)` (Zugriffs-Gate) und `partner_of(user)`
    (anderer Partner).
  - `MessageForm` und `CheckinForm` in `forms.py` (CheckinForm: optionales Ziel
    als SelectField, dessen Choices pro Request im Controller gesetzt werden).
  - Routen in `views.py`: `GET/POST /chat/<conn_id>` (Verlauf + Senden in einer
    Route; 403 für Nicht-Partner, 404 solange die Verbindung nur `requested` ist)
    und `POST /checkin` (Check-in für heute, dedupliziert pro Tag und Ziel).
    `profile()` gibt jetzt aktive Partner, das Check-in-Formular und den
    „heute-schon-eingecheckt"-Status mit.
  - `templates/chat.html` (neu): Partner-Kopf, chronologische Sprechblasen mit
    Zeitstempel (eigene rechts, fremde links), Sende-Formular.
  - `templates/profile.html`: Check-in-Karte und „Meine Partner"-Liste (verlinkt
    je Partner direkt in den Chat).
  - `static/style.css`: Chat-, Partner- und Check-in-Stile.
  - `auth.register`: `streak=0` entfernt (Spalte existiert nicht mehr).
  - `seed.py`: erzeugt aus dem `streak`-Wert je Dummy eine Reihe
    aufeinanderfolgender Check-ins (statt der bisherigen verstreuten Tage), damit
    der berechnete Streak dem gewünschten Demo-Wert entspricht.
  - `tests/test_m5.py` (neu): 5 Tests.
- **How to run:** Schema-Reset nötig (User-Tabelle ohne `streak`-Spalte):
  `instance/app.db` löschen → `flask --app main seed` → `flask --app main run --debug`.
  Profil → „Heute einchecken" bzw. „Meine Partner" → Chat. (Eine vorhandene alte
  DB läuft weiter, die zusätzliche `streak`-Spalte wird ignoriert — für korrekte
  Demo-Streaks aber zurücksetzen.)
- **How to test:** `pytest tests/ -v` → 27 passed (4 + 4 + 5 + 9 + 5).
- **Deckt ab:** FA-07 (AK1–AK3), FA-08 (AK1–AK2), NFA-03 (AK1).
- **Known issues / Entscheidungen:** Streak zählt Kalendertage, nicht
  frequenz-abhängige „geplante" Tage — bewusste MVP-Vereinfachung (frequenz-genaue
  Auswertung optional in M7). Chat ohne Live-Update (Reload nötig); Gesendet-/
  Gelesen-/Online-Status ist FA-16 (→ M7). Check-in ist pro Tag und Ziel
  idempotent; ein „Allgemein"-Check-in (ohne Ziel) ist möglich.
- **Next steps:** Sonderfunktionen (Check-in-Schedule, E-Mail, KI-Coach) → M6.

### M6 — Sonderfunktionen · erledigt

- **Datum:** 30.06.2026
- **Ziel:** Die drei committeten Sonderfunktionen für die 4.0 (Erinnerungen,
  E-Mail-Notification, KI-Coach), datensparsam.
- **Was geändert wurde:**
  - `User.notify_email` (Boolean, default `True`) in `models.py`: Ein/Aus-Schalter
    für E-Mail-Benachrichtigungen (FA-10 AK2).
  - `due_reminders(user, *, now=None)` in `models.py` (FA-09): liefert Goals, deren
    Check-in heute fällig und noch nicht erledigt ist. Der „Schedule" ist die
    bestehende `frequency` + `preferred_checkin_time` des Goals (FA-09 AK1, kein
    neues Entity / kein Hintergrundjob); ein Goal ist fällig, wenn eine
    Check-in-Zeit gesetzt ist, diese heute überschritten wurde und kein Check-in
    für das Goal existiert (FA-09 AK2). `now` ist injizierbar → deterministisch
    testbar. Helfer `_parse_time()` für „HH:MM".
  - `mailer.py` (neu): `send_email()` nutzt echtes SMTP, wenn `MAIL_SERVER`
    gesetzt ist, sonst nur Log (App läuft ohne Mailserver). Unter `TESTING`
    landet die Mail in einer In-Memory-Outbox (`EMAIL_OUTBOX`) für Assertions.
    `notify(user, ...)` respektiert `user.notify_email` (FA-10 AK2).
  - `coach.py` (neu, FA-11): `sharpen_goal()` (vages Ziel → konkreter, AK2) und
    `motivational_message()` (motivierende Rückmeldung, AK1) über die
    Anthropic-API (`claude-opus-4-8`). Ohne `ANTHROPIC_API_KEY` oder fehlendes
    SDK greift ein deterministischer lokaler Fallback (offline-/testfähig). Die
    Prompt-Builder (`sharpen_prompt`, `motivation_prompt`) senden ausschliesslich
    Ziel-Text bzw. Streak-Zahl — keine Zugangsdaten, E-Mails oder fremden
    Chat-Inhalte (NFA-09 AK1).
  - `__init__.py`: `MAIL_*`-Config aus Env (`MAIL_SERVER`, `MAIL_PORT`,
    `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_SENDER`).
  - `forms.py`: `SettingsForm` (notify_email) und `CoachGoalForm` (goal_text).
  - `views.py`: Routen `GET/POST /settings`, `GET /coach`, `POST /coach/motivate`,
    `POST /coach/sharpen`; `profile()` gibt `reminders=due_reminders(...)` mit;
    `send_connection` und `chat` benachrichtigen den Empfänger/Partner per
    `notify(...)` (FA-10 AK1; Nachrichteninhalt wird bewusst nicht mitgeschickt).
    Helfer `_checked_in_today(user)`.
  - Templates: `settings.html` und `coach.html` (neu); `profile.html` um
    „Fällige Erinnerungen" ergänzt; `base.html` um Nav-Links „Coach" und
    „Einstellungen".
  - `static/style.css`: `.coach-bubble`.
  - `requirements.txt`: `anthropic` (optionale Abhängigkeit; nur für den
    Online-Coach nötig, App läuft ohne).
  - `tests/test_m6.py` (neu): 7 Tests.
- **How to run:** Schema-Reset nötig (neue Spalte `notify_email`):
  `instance/app.db` löschen → `flask --app main seed` →
  `flask --app main run --debug`. Erinnerungen erscheinen auf dem Profil, sobald
  die Check-in-Zeit eines Ziels überschritten ist. KI-Coach unter „Coach";
  E-Mail-Schalter unter „Einstellungen". Optional E-Mail real verschicken:
  `MAIL_SERVER`/`MAIL_USERNAME`/`MAIL_PASSWORD` setzen. KI-Coach online:
  `ANTHROPIC_API_KEY` setzen (sonst lokaler Fallback).
- **How to test:** `pytest tests/ -v` → 34 passed (4 + 4 + 5 + 9 + 5 + 7).
- **Deckt ab:** FA-09 (AK1–AK2), FA-10 (AK1–AK2), FA-11 (AK1–AK2), NFA-09 (AK1).
- **Known issues / Entscheidungen:** Kein Hintergrund-Scheduler — Erinnerungen
  werden beim Laden des Profils ausgewertet (in-App-Trigger), die E-Mail bei
  fälligem Check-in (Teil von FA-10 AK1) ist daher nicht abgedeckt; abgedeckt
  sind die Ereignisse „neue Nachricht" und „neue Verbindungsanfrage". „Fällig"
  wird pro Kalendertag ab `preferred_checkin_time` bestimmt (keine
  frequenz-genaue Wochentagslogik) — bewusste MVP-Vereinfachung. E-Mail ohne
  `MAIL_SERVER` nur als Log; KI-Coach ohne Key über lokalen Fallback.
- **Next steps:** UX-Politur & Zusatzfunktionen (Richtung 6.0) → M7.

### M7 — UX-Politur & Zusatzfunktionen · erledigt

- **Datum:** 30.06.2026
- **Ziel:** Note Richtung 6.0 über UX und sinnvolle Extras — Fortschritts­
  visualisierung, Verlässlichkeits-Score, Chat-Status, responsives Layout und
  formularnahe Fehlermeldungen.
- **Was geändert wurde:**
  - **FA-12 (Fortschritt):** Domain-Helfer `checkin_history(user, *, days=14,
    today=None)` in `models.py` (chronologische Tageszählung der Check-ins,
    `today` injizierbar/deterministisch). `profile()` gibt
    `history=checkin_history(...)` mit; `profile.html` rendert daraus ein
    einfaches CSS-Balkendiagramm (keine externe Chart-Bibliothek → offline,
    minimale Deps). Der numerische Streak bleibt im Profilkopf (FA-12 AK1).
  - **FA-13 (Reputation):** Neue Entity `Rating` (rater/ratee/stars 1–5,
    `UniqueConstraint(rater_id, ratee_id)`); User-Relationships
    `ratings_received`/`ratings_given` (cascade delete). Berechnete Properties
    auf `User`: `activity_level` (Anteil der letzten 14 Tage mit Check-in,
    FA-13 AK1), `avg_rating`, `reputation` (0–5: Aktivität, bei vorhandenen
    Bewertungen gleichgewichtet mit dem Bewertungsschnitt). `RatingForm` in
    `forms.py`; Route `POST /rate/<user_id>` (nur aktive Partner, sonst 403;
    Re-Bewerten überschreibt, FA-13 AK2). Reputation auf `profile.html` und
    `user_profile.html` sichtbar (AK3); Bewertungsformular auf dem Fremdprofil
    bei aktiver Verbindung. `/search` sortiert primär nach Match-Score, bei
    Gleichstand nach `reputation` (nachvollziehbare Reihenfolge, AK3).
  - **FA-16 (Status):** `Message.read_at` und `User.last_seen` (neue Spalten).
    Beim Öffnen des Chats werden die Nachrichten des Partners als gelesen
    markiert; der Absender sieht „Gesendet"/„Gelesen" an der eigenen Sprechblase
    (AK1). `User.is_online` (last_seen < 5 min) + `before_app_request`-Hook
    `_touch_last_seen` (auf 1 Schreibvorgang/Minute gedrosselt) treiben den
    Online-/Offline-Indikator im Chat-Kopf (AK2).
  - **NFA-04 (Usability):** `login.html` zeigt jetzt Feldfehler inline (AK2;
    die übrigen Formulare taten dies bereits). Klare Navigation/Beschriftungen
    für den Erst-Nutzer-Flow (AK1).
  - **NFA-06 (Responsiv):** Responsive Regeln in `static/style.css`
    (`overflow-x:hidden`, `img{max-width:100%}`, Pills umbrechen,
    `@media (max-width:575px)` für Nav/Cards/Check-in-Form) → Grundfunktionen
    ohne horizontales Scrollen auf dem Smartphone-Viewport (AK1).
  - `models.py`: Konstanten `REPUTATION_WINDOW_DAYS=14`,
    `ONLINE_WINDOW_SECONDS=300`.
  - `seed.py`: sechs gegenseitige Partner-Bewertungen (`_RATINGS`); Seed-
    Nachrichten erhalten `read_at` (gelten als gelesen).
  - `tests/test_m7.py` (neu): 8 Tests.
- **How to run:** Schema-Reset nötig (neue Tabelle `rating`, neue Spalten
  `message.read_at`, `user.last_seen`): `instance/app.db` löschen →
  `flask --app main seed` → `flask --app main run --debug`. Fortschritts-
  Diagramm und Reputation auf dem Profil; Bewerten auf dem Profil eines aktiven
  Partners (`/u/<id>`); Sende-/Lese- und Online-Status im Chat.
- **How to test:** `pytest tests/ -v` → 42 passed (4 + 4 + 5 + 9 + 5 + 7 + 8).
- **Deckt ab:** FA-12 (AK1–AK2), FA-13 (AK1–AK3), FA-16 (AK1–AK2),
  NFA-04 (AK1–AK2), NFA-06 (AK1).
- **Known issues / Entscheidungen:** Diagramm bewusst als CSS-Balken ohne
  JS-Chart-Lib (offline, keine Zusatz-Abhängigkeit). Reputation 0–5: ohne
  Bewertungen = Aktivität×5, mit Bewertungen Mittel aus Aktivität und
  Bewertungsschnitt — einfache, nachvollziehbare Formel statt gewichtetem
  Modell. Online-Status ist „last_seen < 5 min" und wird pro Request (gedrosselt)
  aktualisiert — kein WebSocket/Polling. Lese-Markierung passiert beim Laden des
  Chats (kein Live-Update). FA-15 (Sprachnachrichten, *Could*) **nicht** umgesetzt
  — Audio-Aufnahme/-Ablage steht in keinem Verhältnis zum MVP-Nutzen, bleibt
  optional offen.
- **Next steps:** Testlauf, Test-Prozeduren, Bug-Liste, MySQL-Integration → M8.

### M7.1 — Matches-Tab · erledigt

- **Datum:** 01.07.2026
- **Ziel:** Eigener `/matches`-Screen mit den Top-3-Partnervorschlägen je Ziel,
  ohne Filter — löst den seit M4 offenen TODO in `search.html`.
- **Was geändert wurde:**
  - `models.py`: neue Domain-Funktion `top_matches_for_goal(goal, limit=3)` —
    im Unterschied zu `match_score()` (gesamtes Goal-Set beider Nutzer) wertet
    sie gezielt ein einzelnes Goal aus (Kategorie Pflicht, +1 Frequenz, +1
    Check-in-Zeit; gleiche 0–4-Skala), Tie-Break über `reputation` (FA-13 AK3).
  - `views.py`: neue Route `GET /matches` (`login_required`), gruppiert die
    Ergebnisse pro eigenem Goal inkl. `Connection.between(...)` für den
    Verbinden/Annehmen/Ablehnen-Status.
  - `templates/matches.html` (neu): eine Sektion pro Goal, Karten im
    `result-card`-Stil aus `search.html`; Leerzustände für „kein Goal" und
    „kein Match für dieses Goal".
  - `templates/base.html`: Nav-Link „Matches" zwischen Suche und Coach.
    `templates/search.html`: Verweis auf `/matches`, veralteter TODO-Kommentar
    entfernt.
  - `tests/test_matches.py` (neu): 5 Tests (Kategorie-Filter/Selbstausschluss,
    Ranking bei vollem vs. teilweisem Overlap, `limit`, Route gruppiert nach
    Goal, Login-Pflicht).
- **How to run:** Kein Schema-Reset nötig (keine Modelländerung). `/matches`
  nach Login in der Nav.
- **How to test:** `pytest tests/ -v` → 47 passed (bisherige 42 + 5 neue).
- **Deckt ab:** FA-05 (dedizierte Match-Ansicht statt nur gefilterter Suche).
- **Known issues / Entscheidungen:** Score bewusst pro Goal statt pro Nutzer,
  damit ein Nutzer mit mehreren Zielen für jedes einzelne passende Partner
  sieht, statt eines über alle Goals gemittelten Gesamt-Scores.

### M8 — Testlauf, Test-Prozeduren, Bug-Liste, MySQL · geplant

- **Ziel:** Stabilität nachweisen und auf die Zielplattform integrieren.
- **Geplanter Umfang:** Test-Infrastruktur (`tests/conftest.py`, App-Fixture,
  temporäre SQLite-DB) bereits in M2 angelegt. M8 ergänzt: minimaler
  High-Value-Testsatz für alle Grundfunktionen (M3–M5); dokumentierte
  Test-Prozeduren und priorisierte Bug-Liste (Test-Engineering-Artefakt);
  Lauf gegen MySQL.
- **Deckt ab:** NFA-01 (AK2 MySQL), NFA-05, NFA-08; Test-Engineering-Deliverable.
- **Akzeptanz-Fokus:** `pytest` grün; Such-/Match-Abfragen unter zwei Sekunden auf
  Testdaten; App läuft gegen MySQL.

### M9 — Abgabe · geplant

- **Ziel:** Vollständige, bewertbare Abgabe.
- **Geplanter Umfang:** Git-Release (duda/heej als Contributors); Video-Demo
  (max. 10 Min, jede:r spricht); Projekt-Tagebuch (Stunden pro Person/Teil);
  README.md und PROJECT.md final synchron.
- **Deckt ab:** Abgabe-Artefakte für die Benotung.
- **Akzeptanz-Fokus:** Alle drei Artefakte fristgerecht via Moodle, mit Timestamp
  vor der (bestätigten) Deadline.

---

## 5. Entscheidungs- & Risiko-Log

- **App-Package im Repo-Root:** beibehalten, um zum Dozenten-Starter
  (`hello-world-fswd`) zu passen. Tests kommen in `tests/` mit einer App-Fixture.
- **SQLite → MySQL:** Entwicklung gegen SQLite, finale Integration MySQL nur über
  `DATABASE_URL`, ohne Code-Änderung (NFA-01).
- **Schema-Reset statt Migrationen** in der Prototyp-Phase (laut `ClaudeCode.md`),
  bis Persistenz-Stabilität explizit gefordert ist.
- **Distanz-Filter als City-Match:** Kein Geocoding; `/search`-Filter „Stadt/Ort"
  macht einen ILIKE-Substring-Match auf `User.city`. FA-14 (Distanzgewichtung im
  Score) bleibt für M7 offen.
- **Frequenz-Suche als exakter Match:** `SearchForm.frequency` ist ein SelectField
  mit festen Werten; die Suche filtert exakt. Nutzer mit abweichendem Freitext in
  `Goal.frequency` erscheinen nicht — bewusster Trade-off für klare UX.
- **match_score in models.py:** Domain-Logik gehört weder in den Controller noch
  in eine separate Service-Schicht (nicht im Stack vorhanden). Als Modul-Funktion
  direkt neben den Entities, da sie ausschliesslich auf Goal-Sets operiert.
- **SearchForm CSRF deaktiviert:** GET-Formulare ändern keinen Zustand; CSRF
  schützt nur POST/PUT/DELETE. Alle zustandsändernden Verbindungs-Routen verwenden
  POST mit CSRF-Token.
- **Streak als berechnete Property:** Statt eines gespeicherten Zählers wird der
  Streak aus den `Checkin`-Datumswerten berechnet (Kette aufeinanderfolgender
  Tage). Einzige Quelle der Wahrheit, kein Drift zwischen Zähler und Check-ins;
  erfüllt FA-08 AK1/AK2 ohne Hintergrundjob.
- **Chat-Gate:** `/chat/<conn_id>` ist nur für die beiden Partner erreichbar
  (403 sonst, NFA-03) und erst bei `status == "active"` (404 solange `requested`,
  FA-06 AK2). GET zeigt den Verlauf, POST sendet — eine Route, Redirect nach dem
  Senden (PRG-Muster).
- **Erinnerungen ohne Scheduler (M6):** `due_reminders` wird beim Laden des
  Profils ausgewertet (in-App-Trigger). Bewusst kein Cron/Hintergrundjob — im
  Stack nicht vorhanden und für den MVP nicht nötig. Der „Schedule" reuse-t
  `frequency`/`preferred_checkin_time` des Goals (keine Duplikat-Entity).
- **E-Mail datensparsam (M6):** Benachrichtigungen enthalten keinen
  Nachrichtentext (NFA-03); ohne `MAIL_SERVER` wird nur geloggt, sodass die App
  ohne Mailserver lauffähig bleibt. `notify()` respektiert `User.notify_email`.
- **KI-Coach mit Fallback (M6):** Anthropic-API nur bei gesetztem
  `ANTHROPIC_API_KEY`; sonst deterministischer lokaler Fallback. Prompts senden
  nur Ziel-Text/Streak (NFA-09). `anthropic` ist optionale Abhängigkeit (lazy
  import), damit Tests netzfrei bleiben und die App ohne Key läuft.
- **Reputation als berechnete Property (M7):** `User.reputation` (0–5) wird aus
  `activity_level` (Check-in-Quote der letzten 14 Tage) und `avg_rating`
  abgeleitet — keine gespeicherte Kennzahl, kein Drift. Bei Gleichstand im
  Match-Score sortiert `/search` nach Reputation (nachvollziehbar, FA-13 AK3).
  `Rating` ist eine eigene Entity mit `UniqueConstraint(rater, ratee)`; nur
  aktive Partner dürfen bewerten (NFA-03).
- **Fortschritts-Diagramm ohne JS (M7):** CSS-Balken aus `checkin_history`
  statt Chart-Bibliothek — offline, keine zusätzliche Abhängigkeit, passt zur
  Prototyp-Minimalität.
- **Online-Status ohne Push (M7):** `User.last_seen` wird per
  `before_app_request` gedrosselt (max. 1×/Minute) aktualisiert; `is_online` =
  „< 5 min". Lese-Status (`Message.read_at`) wird beim Öffnen des Chats gesetzt.
  Bewusst kein WebSocket/Polling — im Stack nicht vorhanden, für den MVP nicht
  nötig (Reload zeigt den aktuellen Stand).
- **Offen / Risiken:** MySQL-Integration noch ausstehend (→ M8). Test-Infrastruktur
  seit M2 vorhanden; Smoke-Tests für M0/M1-Funktionalität in M8 ergänzen.
  E-Mail bei fälligem Check-in (Teil von FA-10 AK1) bräuchte einen Scheduler →
  optional in M8. FA-14 (Distanzgewichtung) und FA-15 (Sprachnachrichten) bleiben
  als *Could* offen.
