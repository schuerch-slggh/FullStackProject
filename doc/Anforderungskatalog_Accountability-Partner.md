# Anforderungskatalog — Accountability-Partner

*Requirements-Engineering-Artefakt · Full Stack Web Development FS2026*

## Legende

- **FA** = Funktionale Anforderung · **NFA** = Nicht-funktionale Anforderung
- **Priorität (MoSCoW):** Must (nötig für die 4.0) · Should / Could (Ausbau Richtung 6.0)
- Jede Anforderung enthält mindestens ein überprüfbares Akzeptanzkriterium (AK).

---

## 1. Funktionale Anforderungen

### Benutzerkonto & Profil

#### FA-01 — Registrierung und Login · *Must*
Nutzer können ein Konto erstellen und sich mit E-Mail und Passwort anmelden.
- **AK1:** Bei der Registrierung mit gültiger, noch nicht vergebener E-Mail und Passwort wird ein Konto angelegt und der Nutzer eingeloggt.
- **AK2:** Bei falschem Passwort oder unbekannter E-Mail wird der Login abgelehnt und eine Fehlermeldung angezeigt, ohne preiszugeben, welches der beiden Felder falsch war.
- **AK3:** Eine bereits registrierte E-Mail kann kein zweites Mal verwendet werden.

#### FA-02 — Eigenes Profil anlegen und bearbeiten · *Must*
Nutzer können ein Profil mit strukturierten Daten, Freitext und Foto pflegen.
- **AK1:** Das Profil speichert mindestens: Name, optional Alter, Zielkategorie, konkretes Ziel (Freitext), gewünschte Frequenz, bevorzugte Check-in-Zeit, kurzer Bio-Text.
- **AK2:** Änderungen am Profil werden in der Datenbank gespeichert und sind nach erneutem Laden der Seite weiterhin sichtbar.
- **AK3:** Ein Profilfoto kann hochgeladen und angezeigt werden.

#### FA-03 — Fremdprofil anzeigen (View) · *Must*
Nutzer können das Profil anderer Nutzer ansehen.
- **AK1:** Das angezeigte Profil zeigt strukturierte Daten, Freitext und Foto an.
- **AK2:** Der aktuelle Streak des Nutzers wird auf dem Profil dargestellt.

### Suche & Match

#### FA-04 — Parametrische Suche (Search) · *Must*
Nutzer können nach anderen Accountability-Partnern filtern.
- **AK1:** Es kann mindestens nach Zielkategorie, Frequenz und Distanz gefiltert werden.
- **AK2:** Die Ergebnisliste enthält nur Profile, die alle gesetzten Filterkriterien erfüllen.
- **AK3:** Wenn kein Profil passt, wird eine verständliche Leer-Meldung statt einer leeren Seite angezeigt.

#### FA-05 — Match-Algorithmus (Match) · *Must*
Das System berechnet eine Übereinstimmung aus den strukturierten Profildaten.
- **AK1:** Der Match-Score berücksichtigt Zielkategorie, Frequenz und Überlappung der Check-in-Zeiten.
- **AK2:** Vorschläge werden absteigend nach Score sortiert dargestellt.
- **AK3:** Derselbe Nutzer wird sich selbst nie als Match vorgeschlagen.

#### FA-06 — Verbindung herstellen · *Must*
Nutzer können eine Match-Anfrage senden und annehmen, wodurch eine Partnerschaft entsteht.
- **AK1:** Eine gesendete Anfrage ist für den Empfänger sichtbar.
- **AK2:** Erst nach beidseitiger Bestätigung gilt ein Match als aktiv und der Chat wird freigeschaltet.

### Kommunikation

#### FA-07 — 1:1-Chat (Chat) · *Must*
Verbundene Partner können Textnachrichten senden und empfangen.
- **AK1:** Eine gesendete Nachricht erscheint beim Empfänger und bleibt nach Neuladen erhalten.
- **AK2:** Nachrichten werden chronologisch mit Zeitstempel dargestellt.
- **AK3:** Nur die beiden Partner einer Verbindung können deren Nachrichten lesen.

#### FA-08 — Check-in durchführen · *Must*
Nutzer können einen erledigten Check-in für ihr Ziel markieren.
- **AK1:** Ein Check-in wird mit Datum gespeichert und erhöht den Streak.
- **AK2:** Wird an einem geplanten Tag kein Check-in gemacht, wird der Streak entsprechend zurückgesetzt.

### Sonderfunktionen

#### FA-09 — Check-in-Schedule / Erinnerungen · *Should*
Nutzer können wiederkehrende Check-in-Zeitpunkte festlegen, an die die App erinnert.
- **AK1:** Ein Zeitplan (z.B. täglich/wöchentlich) kann angelegt und gespeichert werden.
- **AK2:** Zum fälligen Zeitpunkt wird eine Erinnerung ausgelöst.

#### FA-10 — E-Mail-Notification · *Should*
Das System benachrichtigt Nutzer per E-Mail über relevante Ereignisse.
- **AK1:** Bei einer neuen Nachricht, einem neuen passenden Partner oder einem fälligen Check-in wird eine E-Mail versendet.
- **AK2:** Nutzer können Benachrichtigungen in den Einstellungen aktivieren oder deaktivieren.

#### FA-11 — KI-Coach · *Should*
Ein Sprachmodell unterstützt Nutzer bei Motivation und Zielformulierung.
- **AK1:** Bei einem verpassten Check-in kann der KI-Coach eine motivierende Rückmeldung erzeugen.
- **AK2:** Der KI-Coach kann ein vage formuliertes Ziel in eine konkretere Formulierung umschreiben.

#### FA-12 — Streak- und Fortschrittsanzeige · *Should*
Nutzer sehen ihren Verlauf visuell aufbereitet.
- **AK1:** Der aktuelle Streak wird numerisch angezeigt.
- **AK2:** Ein einfaches Diagramm zeigt die Check-in-Historie über die Zeit.

#### FA-13 — Reputations-/Verlässlichkeits-Score · *Should*
Jeder Nutzer erhält einen Score, der seine Zuverlässigkeit als Accountability-Partner abbildet. Der Score setzt sich aus zwei Komponenten zusammen: dem Aktivitätsniveau des Nutzers (z.B. Check-in-Quote, Regelmässigkeit) und Bewertungen durch frühere Matching-Partner.
- **AK1:** Das Aktivitätsniveau fliesst messbar in den Score ein (z.B. Anteil eingehaltener geplanter Check-ins).
- **AK2:** Ein Matching-Partner kann eine Bewertung abgeben, die in den Score des bewerteten Nutzers einfliesst.
- **AK3:** Der resultierende Score ist auf dem Profil sichtbar und beeinflusst nachvollziehbar die Match-Reihenfolge.

#### FA-14 — Distanz als Match-Kriterium · *Could*
Die geografische Distanz zwischen Nutzern fliesst gewichtet in den Match-Score ein.
- **AK1:** Bei sonst gleichen Kriterien erhält ein näher gelegener Partner einen höheren Match-Score.
- **AK2:** Die maximale Distanz kann in der Suche als Filter gesetzt werden.

#### FA-15 — Sprachnachrichten · *Could*
Verbundene Partner können sich gesprochene Nachrichten senden, um z.B. eine Sprache gesprochen zu üben.
- **AK1:** Eine aufgenommene Sprachnachricht kann gesendet und vom Empfänger abgespielt werden.
- **AK2:** Sprachnachrichten werden wie Textnachrichten chronologisch im Chatverlauf dargestellt.

#### FA-16 — Gesendet-/Gelesen- und Online-Status · *Could*
Nutzer sehen den Status ihrer Nachrichten und ob der Partner online ist.
- **AK1:** Eine gelesene Nachricht wird beim Absender als gelesen markiert.
- **AK2:** Der Online-Status des Partners wird im Chat angezeigt.

---

## 2. Nicht-funktionale Anforderungen

#### NFA-01 — Persistente Datenhaltung · *Must*
Alle relevanten Daten (Profile, Matches, Nachrichten, Check-ins) werden in einer relationalen Datenbank gespeichert.
- **AK1:** Nach einem Neustart der Anwendung sind alle zuvor gespeicherten Daten weiterhin vorhanden.
- **AK2:** Die Anwendung läuft gegen MySQL (Entwicklung gegen SQLite ist zulässig).

#### NFA-02 — Sicherheit der Zugangsdaten · *Must*
Passwörter werden niemals im Klartext gespeichert.
- **AK1:** In der Datenbank sind Passwörter ausschliesslich als Hash abgelegt.
- **AK2:** Geschützte Seiten sind ohne gültige Anmeldung nicht erreichbar.

#### NFA-03 — Datenschutz und Zugriffsschutz · *Must*
Nutzer können nur auf Daten zugreifen, für die sie berechtigt sind.
- **AK1:** Chat-Inhalte sind ausschliesslich für die beiden beteiligten Partner einsehbar.
- **AK2:** Ein Nutzer kann die privaten Einstellungen eines anderen Nutzers nicht einsehen oder ändern.

#### NFA-04 — Benutzbarkeit (Usability) · *Should*
Die Grundfunktionen sind ohne Anleitung bedienbar.
- **AK1:** Ein neuer Nutzer kann ohne Hilfestellung Profil anlegen, suchen, matchen und eine Nachricht senden.
- **AK2:** Fehleingaben in Formularen werden direkt am betroffenen Feld erklärt.

#### NFA-05 — Reaktionszeit (Performance) · *Should*
Die Anwendung reagiert für typische Aktionen zügig.
- **AK1:** Bei einem Testdatenbestand antworten Such- und Match-Abfragen in unter zwei Sekunden.
- **AK2:** Das Senden einer Nachricht ist für den Absender ohne merkliche Verzögerung sichtbar.

#### NFA-06 — Responsives Design · *Should*
Die Oberfläche ist auf Desktop und mobilen Geräten nutzbar.
- **AK1:** Auf einem Smartphone-Viewport sind alle Grundfunktionen ohne horizontales Scrollen bedienbar.

#### NFA-07 — Wartbarkeit und Versionierung · *Should*
Der Code ist nachvollziehbar strukturiert und versioniert.
- **AK1:** Das Projekt liegt in einem Git-Repository mit nachvollziehbarer Commit-Historie.
- **AK2:** Die Anwendung trennt Datenzugriff, Logik und Darstellung (Controller/Entities/Views).

#### NFA-08 — Robustheit · *Should*
Die Anwendung fängt ungültige Eingaben ab, ohne abzustürzen.
- **AK1:** Ungültige oder leere Pflichteingaben führen zu einer Fehlermeldung statt zu einem Absturz.
- **AK2:** Der direkte Aufruf einer geschützten URL ohne Anmeldung leitet auf den Login um.

#### NFA-09 — Datensparsamkeit bei der KI-Nutzung · *Could*
Bei der Nutzung des KI-Coachs werden nur notwendige Daten an den externen Dienst übermittelt.
- **AK1:** An die KI-Schnittstelle werden keine Zugangsdaten und keine Chat-Inhalte fremder Nutzer gesendet.

---

## 3. Abdeckung der Pflichtfunktionen (Nachweis für die 4.0)

| Pflichtfunktion (PDF) | Abgedeckt durch |
|-----------------------|-----------------|
| View — Profil anzeigen | FA-02, FA-03 |
| Store — Datenspeicherung | NFA-01 |
| Search — parametrische Suche | FA-04 |
| Match — Algorithmus | FA-05, FA-06 |
| Chat — 1:1-Nachrichten | FA-07 |
| Drei Sonderfunktionen | FA-09, FA-10, FA-11 |
