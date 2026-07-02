# Matching v2 — Design & Spezifikation

*Entwurf zur Überarbeitung des Matching-Algorithmus (FA-05, FA-14, NFA-05).
Ziel: aus einem groben 0–4-Kriterien-Zähler ein aussagekräftiges, erklärbares
Kompatibilitäts-Ranking machen. Bezieht sich auf die bestehende Logik in
`models.py` (`MATCH_CRITERIA`, `match_score`, `top_matches_for_goal`).*

> **Umsetzungsstand:** **v2a ist umgesetzt** (siehe `PROJECT.md`, Meilenstein
> „Matching v2a — Nähe statt Gleichheit", und `models.py`). Der 0–4-Zähler und
> `MATCH_CRITERIA` existieren nicht mehr; `match_score()` liefert bereits einen
> kontinuierlichen Score in `[0, 1]` aus `domain`/`rhythm`/`timefit`/`reliab`/
> `intensity`. §2 Punkt 1 und 4 sowie der v2a-Teil von §3/§3.1/§3.3 unten sind
> damit **historisch/umgesetzt**, nicht mehr offen. §3.2 (Text-Ähnlichkeit),
> §5 (Distanz) und §6 (personenzentrierte Seite) sind weiterhin **offen**
> (v2b–v2e, siehe §8). Eine Abweichung von der ursprünglichen Spezifikation:
> `domain_fit` läuft in v2a ohne `sim` (kein `goal_text`-Vergleich vor v2c) und
> reduziert sich deshalb auf `1.0`/`0.0` statt der `max(sim, 0.6*same_cat)`-
> Formel — der 0.6-Deckel ergibt ohne zweite Signalquelle keinen Sinn (siehe
> §3.2).

## 1. Leitprinzip

Accountability-Matching ist **kein Ähnlichkeits-Dating**, sondern die Suche nach
einer **funktionierenden Arbeitsbeziehung**: zwei Menschen, die sich zuverlässig
gegenseitig auf Kurs halten. Entscheidend sind daher nicht identische Profile,
sondern **Kompatibilität** in Domäne, Rhythmus, Verlässlichkeit und Intensität.

## 2. Schwächen des aktuellen Standes

1. ~~**Gleichheit statt Nähe.**~~ Frequenz (`"3x pro Woche"`) und Check-in-Zeit
   (`"08:00"`) wurden per Mengenschnitt exakt verglichen; `3x`/`4x pro Woche` und
   `08:00`/`08:30` matchten nicht, obwohl fast identisch. **✅ Behoben in v2a**
   (`rhythm_fit`/`time_fit`, `models.py`).
2. **`goal_text` ungenutzt.** Das reichhaltigste Signal (die konkrete Tätigkeit)
   fließt gar nicht ein; nur die grobe Kategorie zählt. **Offen** (v2c).
3. **Grobkörnig.** Score 0–4 ganzzahlig → viele Gleichstände. **✅ Behoben in
   v2a** (kontinuierlicher Score in `[0, 1]`).
4. ~~**Verlässlichkeit nur als Tie-Break.**~~ `activity_level`, `reputation`,
   `is_online` waren vorhanden, beeinflussten den Score aber nicht. **✅ Behoben
   in v2a** (`reliability_fit`/`intensity_fit` sind echte Score-Komponenten;
   `reputation` bleibt zusätzlich Tie-Break, FA-13 AK3).
5. **Distanz nur Filter.** Kein gewichteter Einfluss; `city` ist Freitext ohne
   Koordinaten. **Offen** (v2d).

## 3. Scoring-Modell v2

Kontinuierlicher Score in `[0, 1]` (Anzeige als %), gewichtete Summe normierter
Komponenten. Jede Komponente liefert selbst einen Wert in `[0, 1]`.

**Umgesetzt in v2a:** `domain` (nur Kategorie, ohne `sim`), `rhythm`,
`timefit`, `reliab`, `intensity`. `proximity` ist noch nicht Teil des Scores;
`models.py` verzichtet auf eine feste Neugewichtung der verbleibenden fünf
Komponenten und normiert stattdessen einmalig über
`MATCH_WEIGHT_TOTAL = 0.90` (Summe der fünf aktiven Gewichte) — das entspricht
der `score = score_raw / Σ(weight_i)`-Renormierung unten.

| Komponente | Gewicht | Quelle |
|---|---|---|
| `domain`   | 0.30 | Kategorie + semantische Ähnlichkeit von `goal_text` |
| `rhythm`   | 0.20 | Frequenz-Nähe (Sessions/Woche) |
| `timefit`  | 0.15 | Nähe der bevorzugten Check-in-Zeit |
| `reliab`   | 0.15 | gemeinsame Verlässlichkeit + Liveness |
| `intensity`| 0.10 | Ähnliches Commitment-Level |
| `proximity`| 0.10 | Distanz — **nur wenn „vor Ort"**, sonst Gewicht umverteilt |

```
score_raw = Σ (weight_i * component_i)   # nur aktive Komponenten
score     = score_raw / Σ (weight_i)     # Re-Normierung, falls proximity entfällt
score    *= capacity_factor              # Kapazitäts-/Liveness-Multiplikator
```

`capacity_factor ∈ [0.5, 1.0]`: senkt Kandidaten, die schon viele aktive
Verbindungen haben oder lange inaktiv sind (ein Top-Match, der nie antwortet, ist
ein schlechter Vorschlag). Tie-Break weiterhin `reputation` (FA-13 AK3).

### 3.1 Normalisierungs-Helfer (deterministisch, ohne KI)

```python
def freq_to_per_week(s: str) -> float | None:
    if not s: return None
    s = s.strip().lower()
    if s == "täglich": return 7.0
    # Muster "{n}x pro Woche" / "{n}x pro Monat"
    m = re.match(r"(\d+)x pro (woche|monat)", s)
    if not m: return None
    n = int(m.group(1))
    return n if m.group(2) == "woche" else n / 4.33

def rhythm_fit(a: str, b: str) -> float:
    fa, fb = freq_to_per_week(a), freq_to_per_week(b)
    if fa is None or fb is None: return 0.0
    return 1 - min(1.0, abs(fa - fb) / 7.0)          # 0 Tage Diff = 1.0

def time_to_min(s: str) -> int | None:
    try:
        hh, mm = s.strip().split(":"); return int(hh) * 60 + int(mm)
    except Exception: return None

def time_fit(a: str, b: str) -> float:
    ta, tb = time_to_min(a), time_to_min(b)
    if ta is None or tb is None: return 0.0
    diff = abs(ta - tb); diff = min(diff, 1440 - diff)  # zirkulär über Mitternacht
    return 1 - min(1.0, diff / 180.0)                    # innerhalb 3h = Teil-Kredit
```

### 3.2 Domain-Fit (mit optionalen Embeddings) — Ziel-Design für v2c

**In v2a noch nicht umgesetzt.** `models.py` implementiert `domain` aktuell
als reinen Kategorie-Vergleich (`1.0` bei geteilter Kategorie, sonst `0.0`,
über alle Zielpaare der beiden Nutzer bzw. innerhalb der Kategorie des
Ziels bei `top_matches_for_goal`). Die `max(sim, 0.6*same_cat)`-Formel unten
ist das Zieldesign für v2c, sobald `text_similarity` existiert — ohne `sim`
ergäbe sie nur einen künstlichen Deckel von `0.6`, den v2a deshalb nicht
übernimmt.

```python
def domain_fit(goal_a, goal_b) -> float:
    same_cat = 1.0 if goal_a.goal_category == goal_b.goal_category else 0.0
    sim = text_similarity(goal_a.goal_text, goal_b.goal_text)  # 0..1, s. §4
    # Text-Ähnlichkeit dominiert, Kategorie als Boden/Booster:
    return max(sim, 0.6 * same_cat)
```

Über mehrere Ziele: `domain = max` über alle Zielpaare (bestes passendes Paar).

### 3.3 Verlässlichkeit & Intensität

```python
def reliability_fit(a: User, b: User) -> float:
    both_active = min(a.activity_level, b.activity_level)   # beide zeigen auf
    similar     = 1 - abs(a.activity_level - b.activity_level)
    live        = 1.0 if (a.is_online or b.is_online) else 0.85
    return both_active * 0.6 + similar * 0.4 * live

def intensity_fit(a: User, b: User) -> float:
    # Commitment-Level grob über Streak (gedeckelt) + Zielanzahl
    la = min(a.streak, 30) / 30 + min(len(a.goals), 5) / 5
    lb = min(b.streak, 30) / 30 + min(len(b.goals), 5) / 5
    return 1 - abs(la - lb) / 2
```

## 4. Text-Ähnlichkeit — das richtige Werkzeug

**Fürs Scoring: Embeddings, nicht der Chat-LLM.** Jeden `goal_text` **einmal beim
Speichern** in einen Vektor umwandeln, persistieren, zur Match-Zeit per Cosinus
vergleichen. Skaliert (O(n) einmalig, O(1) je Vergleich), deterministisch
cachebar, erfüllt NFA-05.

- **Empfohlen für dieses Projekt:** lokales `sentence-transformers`-Modell
  (offline, kostenlos, deterministisch) — passt zum Offline-Fallback-Prinzip des
  Coaches. Anthropic selbst hat keinen Embeddings-Endpoint; falls gehostet
  gewünscht, ein Drittanbieter.
- **Deterministischer Fallback** (kein Modell/Netz), analog `coach.py`: normierte
  Token-Überlappung (Jaccard/TF-IDF) der Zieltexte. So bleiben Tests netzfrei.

```python
def text_similarity(a: str, b: str) -> float:
    vec = embedding_provider()          # None, wenn Modell/Netz fehlt
    if vec is None:
        return _token_overlap(a, b)     # deterministischer Fallback
    return _cosine(vec(a), vec(b))
```

**Nicht** einen LLM pro Kandidatenpaar zum Scoren aufrufen (O(n) Calls, langsam,
nicht-deterministisch). Der LLM darf **nur die Top 3–5** veredeln: ein kurzer
„Warum ihr zwei passt"-Satz über den bestehenden Coach — reine UX-Politur,
wenige Calls, kein Ranking-Einfluss.

## 5. Distanz — bedingt, nicht pauschal (FA-14)

Distanz zählt nur, wenn die Partnerschaft **vor Ort** gedacht ist. Sonst
verschlechtert sie Remote-Matches.

1. **Präferenz einführen:** pro Ziel (oder in der Suche) ein Schalter
   `remote | vor Ort`. Nur bei „vor Ort" wird `proximity` aktiv (sonst Gewicht
   umverteilt).
2. **Koordinaten statt Freitext:** `city` mit **Autocomplete aus einem
   Städte-Datensatz** (DACH) hinterlegen, das liefert `lat/lng` gratis und säubert
   die Daten. Alternativ Geocoding beim Speichern, Ergebnis cachen.
3. **Score:** `proximity = exp(-distance_km / SCALE)` (z.B. `SCALE=25`), plus
   optionaler Radius-Filter in der Suche (Upgrade des heutigen `city`-Filters).

## 6. Match-Seite v2 — Person zuerst, Aktivitäten darin

Heute getrennt: `/search` (ganze Person) und `/matches` (pro Ziel, Top-3) — dort
kann dieselbe Person mehrfach erscheinen, ohne dass ihr **Mehrfach-Match**
sichtbar wird.

**Zusammenführen in eine personenzentrierte Rangliste:**

```
person_score = best_goal_score + Σ_extra (0.1 * goal_score)   # gedeckelt, z.B. +0.3
```

- **Einheit = Person.** Beste Ziel-Passung plus abnehmender Bonus je zusätzlich
  gematchtem Ziel → „Power-Matches" (Passung auf mehreren Zielen) steigen nach
  oben.
- **Personenkarte** zeigt als Chips, *welche* eigenen Ziele passen, je mit
  Breakdown (Transparenz beibehalten), dazu Reputation + Online-Status.
- **Pro-Ziel-Drill-down** bleibt als Sekundäransicht („wer passt zu *diesem*
  Commitment").
- **Dedupe:** bestehende/laufende Verbindungen ausblenden oder markieren.
- **Sortierung:** bester Match · nächster (bei „vor Ort") · verlässlichster.
- **Leerzustände:** kein eigenes Ziel → zum Anlegen führen; keine Kandidaten →
  Kriterien lockern und „nächstbeste" zeigen.

## 7. Randfälle & Qualität

- **Qualität vor Quantität:** Schwelle setzen (keine Vorschläge unter z.B. 0.35),
  lieber wenige starke Matches.
- **Cold-Start:** bei wenigen Nutzern Gewichte weicher fahren / Fallback-Liste.
- **Determinismus & Tests:** alle Komponenten deterministisch + Offline-Fallback,
  Tests bleiben netzfrei (wie `coach.py`).
- **Performance (NFA-05):** Embeddings beim Speichern vorberechnen, im Ranking
  keine API-Calls.
- **Sicherheit:** für „vor Ort" altersangemessen paaren; breite Zielkategorien,
  kein detailliertes Ernährungs-/Gewichts-Tracking.
- **Lern-Loop (später):** akzeptierte vs. ignorierte Anfragen und langlebige,
  aktive Partnerschaften protokollieren und daraus Gewichte nachjustieren — nicht
  vor der Deadline überbauen.

## 8. Meilenstein-Vorschlag

Als eigener Meilenstein „Matching v2" durch den Workflow in `ClaudeCode.md`:

1. **v2a — Nähe statt Gleichheit** ✅ **erledigt** (höchster ROI, kein
   KI-Bedarf): Frequenz- und Zeit-Normalisierung, kontinuierlicher Score,
   Verlässlichkeit/Intensität in den Score. Tests für die Helfer. Siehe
   `PROJECT.md` (Meilenstein „Matching v2a — Nähe statt Gleichheit") und
   `models.py`.
2. **v2b — Personenzentrierte Match-Seite:** Aggregation + Karten-UI + Drill-down.
3. **v2c — Semantik:** `goal_text`-Embeddings mit deterministischem Fallback,
   Embedding beim Speichern vorberechnen.
4. **v2d — Distanz (FA-14):** „vor Ort"-Präferenz, Städte-Autocomplete mit
   Koordinaten, `proximity` + Radius-Filter.
5. **v2e (optional) — LLM-Veredelung:** „Warum ihr passt"-Satz für die Top-Matches.

Deckt ab: FA-05 (stärker), FA-14, NFA-05; stützt FA-13 (Reputation wird echter
Score-Faktor).
