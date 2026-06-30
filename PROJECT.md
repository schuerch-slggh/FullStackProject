# PROJECT.md — Engineering-Audit-Trail

## 1. Projektzusammenfassung

**Momentum** ist eine Accountability-Partner-Web-App (Flask/Python): Nutzer legen
ein Zielprofil an, finden über eine parametrische Suche und einen Match-Algorithmus
passende Partner, verbinden sich, chatten 1:1 und halten sich per Check-in
gegenseitig auf Kurs. Geplante Sonderfunktionen: Check-in-Schedule/Erinnerungen,
E-Mail-Notification und ein KI-Coach.

Quelle der Wahrheit für den Funktionsumfang ist `docs/anforderungskatalog.md`
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
- [ ] **M3** — Vollständiges Datenmodell (Connection, Message, Checkin)
- [ ] **M4** — Suche, Match-Algorithmus & Verbindung
- [ ] **M5** — 1:1-Chat & Check-in
- [ ] **M6** — Sonderfunktionen: Check-in-Schedule, E-Mail-Notification, KI-Coach
- [ ] **M7** — UX-Politur & Zusatzfunktionen (Richtung 6.0)
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

### M3 — Vollständiges Datenmodell · geplant

- **Ziel:** ER-Modell um die verbleibenden Grundfunktions-Entities erweitern.
- **Geplanter Umfang:** `Connection` (Match/Partnerschaft mit Status
  angefragt/aktiv), `Message` (Chat 1:1), `Checkin` (mit Datum und User-FK).
  Beziehungen, Indizes und Foreign Keys. `Goal` (1:n zu User) und `photo_url`
  auf `User` wurden bereits im Commitment-Feature umgesetzt. Kein separates
  `Photo`-Modell nötig. Schema-Reset statt Migrationen (Prototyp-Phase).
- **Deckt ab:** NFA-01 (Datenbasis für Match, Chat, Check-in).
- **Akzeptanz-Fokus:** Alle Grundfunktions-Entities vorhanden und über das ORM
  abfragbar.

### M4 — Suche, Match-Algorithmus & Verbindung · geplant

- **Ziel:** Partner finden, bewerten und verbinden.
- **Geplanter Umfang:** Parametrische Suche (Zielkategorie, Frequenz, Distanz) mit
  verständlicher Leer-Meldung; Match-Score aus Zielkategorie + Frequenz +
  Überlappung der Check-in-Zeiten, absteigend sortiert, nie der eigene Account;
  Match-Anfrage senden/annehmen, Chat erst nach beidseitiger Bestätigung.
- **Deckt ab:** FA-04, FA-05, FA-06; optional FA-14 (Distanzgewichtung); NFA-05.
- **Akzeptanz-Fokus:** Ergebnisliste erfüllt alle Filter; Selbst-Match
  ausgeschlossen; Chat-Freischaltung erst bei aktivem Match.

### M5 — 1:1-Chat & Check-in · geplant

- **Ziel:** Kommunikation und der wiederkehrende Kern-Loop.
- **Geplanter Umfang:** 1:1-Textchat (chronologisch, mit Zeitstempel, nur für die
  beiden Partner sichtbar); Check-in markieren, das den Streak erhöht bzw. bei
  Auslassung zurücksetzt.
- **Deckt ab:** FA-07, FA-08, NFA-03.
- **Akzeptanz-Fokus:** Nachrichten bleiben nach Reload erhalten; Dritte können den
  Chatverlauf nicht lesen; Check-in verändert den Streak korrekt.

### M6 — Sonderfunktionen · geplant

- **Ziel:** Die drei committeten Sonderfunktionen für die 4.0.
- **Geplanter Umfang:** Check-in-Schedule mit Erinnerungen (FA-09);
  E-Mail-Notification mit Ein/Aus-Schalter in den Einstellungen (FA-10);
  KI-Coach über die Anthropic-API für Motivation und Zielschärfung (FA-11),
  datensparsam (NFA-09).
- **Deckt ab:** FA-09, FA-10, FA-11, NFA-09.
- **Akzeptanz-Fokus:** Erinnerung wird zum fälligen Zeitpunkt ausgelöst; E-Mail bei
  relevanten Ereignissen; KI schreibt ein vages Ziel konkreter um, ohne fremde
  Chat-Inhalte oder Zugangsdaten zu übermitteln.

### M7 — UX-Politur & Zusatzfunktionen · geplant

- **Ziel:** Note Richtung 6.0 über UX und sinnvolle Extras.
- **Geplanter Umfang:** Streak-/Fortschritts-Diagramm (FA-12); Reputations-Score
  aus Aktivität + Bewertungen (FA-13); Gesendet-/Gelesen- und Online-Status
  (FA-16); durchgängig responsives Design (NFA-06); Bedienbarkeit ohne Anleitung
  (NFA-04). Optional Sprachnachrichten (FA-15).
- **Deckt ab:** FA-12, FA-13, FA-16, NFA-04, NFA-06; optional FA-15.
- **Akzeptanz-Fokus:** Grundfunktionen auf Smartphone-Viewport ohne horizontales
  Scrollen; Score sichtbar und nachvollziehbar in der Match-Reihenfolge.

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
- **Offen / Risiken:** MySQL-Integration noch ausstehend (→ M8). Test-Infrastruktur
  seit M2 vorhanden; Smoke-Tests für M0/M1-Funktionalität in M8 ergänzen.
