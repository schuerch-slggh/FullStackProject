"""KI-Coach über die Anthropic-API (FA-11), datensparsam (NFA-09).

An die KI gehen ausschliesslich der Ziel-Text bzw. der Streak-Zähler — niemals
Zugangsdaten, E-Mail-Adressen oder fremde Chat-Inhalte (NFA-09 AK1). Ist kein
`ANTHROPIC_API_KEY` gesetzt (oder das SDK fehlt), greift ein deterministischer
lokaler Fallback, damit die App offline läuft und Tests netzfrei bleiben.
"""
import os

MODEL = "claude-opus-4-8"
MAX_TOKENS = 200
CHAT_MAX_TOKENS = 400

# Fester Ton & Rahmen des Coachs (System-Prompt). Enthält KEINE Nutzerdaten —
# der kompakte Nutzerkontext wird pro Anfrage separat angehängt (NFA-09).
COACH_SYSTEM = (
    "Du bist der GrindMate-Coach, ein persönlicher Accountability-Coach. "
    "Ton: motivierend, konkret, positiv-verbindlich — Druck ja, aber "
    "unterstützend, nie herablassend. Antworte auf Deutsch, kurz und praxisnah "
    "(1–4 Sätze, gern mit einer konkreten nächsten Handlung). Beziehe dich, wo "
    "sinnvoll, auf Streak, Ziel und Check-in-Quote der Person. Bleib strikt beim "
    "Thema Zielerreichung, Motivation, Gewohnheiten und Lernen. Gib keine "
    "medizinischen, finanziellen, rechtlichen oder anderweitig heiklen Ratschläge "
    "— verweise dann freundlich an Fachpersonen. Erfinde keine Fakten über die "
    "Person, die nicht im Kontext stehen."
)


def _client():
    """Anthropic-Client, falls Key und SDK vorhanden sind, sonst None."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    return anthropic.Anthropic()


def _generate(prompt: str) -> str | None:
    """Eine einzelne Text-Antwort von der API; None, wenn kein Client verfügbar."""
    client = _client()
    if client is None:
        return None
    msg = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return next((b.text for b in msg.content if b.type == "text"), "").strip()


def sharpen_prompt(goal_text: str) -> str:
    """Prompt zum Umschreiben — enthält nur den Ziel-Text (NFA-09)."""
    return (
        "Formuliere das folgende Ziel konkreter und messbar, in einem Satz auf "
        "Deutsch. Gib nur das umformulierte Ziel zurück, ohne Vorrede.\n\n"
        f"Ziel: {goal_text}"
    )


def motivation_prompt(streak: int, goal_text: str | None) -> str:
    """Prompt für eine motivierende Rückmeldung — nur Streak-Zahl + optional Ziel."""
    ziel = f" Sein Ziel: {goal_text}." if goal_text else ""
    return (
        "Schreibe eine kurze, motivierende Nachricht (max. 2 Sätze, Deutsch) für "
        f"jemanden mit einem Check-in-Streak von {streak} Tagen.{ziel} "
        "Sei ermutigend, ohne zu übertreiben."
    )


def sharpen_goal(goal_text: str) -> str:
    """Schreibt ein vage formuliertes Ziel konkreter um (FA-11 AK2)."""
    goal_text = (goal_text or "").strip()
    if not goal_text:
        return ""
    result = _generate(sharpen_prompt(goal_text))
    return result or _fallback_sharpen(goal_text)


def motivational_message(streak: int, goal_text: str | None = None) -> str:
    """Erzeugt eine motivierende Rückmeldung, z.B. bei verpasstem Check-in (FA-11 AK1)."""
    streak = streak or 0
    result = _generate(motivation_prompt(streak, goal_text))
    return result or _fallback_motivation(streak)


def _fallback_sharpen(goal_text: str) -> str:
    return (
        f"{goal_text} — konkret: Lege Wochentage, Uhrzeit und ein messbares "
        "Mindestziel fest (z.B. „3x pro Woche, 30 Minuten“)."
    )


def _fallback_motivation(streak: int) -> str:
    if streak <= 0:
        return (
            "Jeder Streak beginnt mit einem einzigen Check-in. Mach heute den "
            "ersten Schritt – dein:e Partner:in zieht mit."
        )
    return (
        f"{streak} Tage am Stück – stark! Bleib dran, ein Tag nach dem anderen. "
        "Dein nächster Check-in hält die Kette am Leben."
    )


# ---------------------------------------------------------------------------
# Chat-Coach (Konversation mit Verlauf) + situativer Kopf-Satz (FA-11)
# ---------------------------------------------------------------------------

def _chat(system: str, messages: list[dict]) -> "str | None":
    """Mehrstufiger Chat-Call mit Verlauf; None, wenn kein Client verfügbar."""
    client = _client()
    if client is None:
        return None
    msg = client.messages.create(
        model=MODEL,
        max_tokens=CHAT_MAX_TOKENS,
        system=system,
        messages=messages,
    )
    return next((b.text for b in msg.content if b.type == "text"), "").strip() or None


def context_block(ctx: dict) -> str:
    """Kompakter Nutzerkontext als eine Zeile — datensparsam (NFA-09).

    Enthält bewusst nur Name (Vorname), Ziel, Kategorie, Streak und Quote —
    keine E-Mail, kein Passwort, keine fremden Chat-Inhalte.
    """
    parts = []
    if ctx.get("name"):
        parts.append(f"Name: {ctx['name']}")
    if ctx.get("goal"):
        cat = f" (Kategorie {ctx['category']})" if ctx.get("category") else ""
        parts.append(f"Ziel: {ctx['goal']}{cat}")
    else:
        parts.append("Ziel: noch keines gesetzt")
    parts.append(f"Streak: {ctx.get('streak', 0)} Tage")
    parts.append(f"Check-in-Quote (14 Tage): {ctx.get('quote', 0)}%")
    parts.append(f"Heute eingecheckt: {'ja' if ctx.get('checked_in') else 'nein'}")
    return "AKTUELLER NUTZER — " + " · ".join(parts)


def build_system_prompt(ctx: dict) -> str:
    """Fester Coach-Prompt + angehängter Nutzerkontext."""
    return COACH_SYSTEM + "\n\n" + context_block(ctx)


def chat_reply(messages: list[dict], ctx: dict) -> str:
    """Coach-Antwort auf den Konversationsverlauf; Fallback ohne API."""
    reply = _chat(build_system_prompt(ctx), messages)
    return reply or _fallback_chat(messages, ctx)


def coach_headline(facts: dict) -> str:
    """Ein situativer Kopf-Satz, serverseitig aus echten Fakten formuliert."""
    result = _generate(headline_prompt(facts))
    return result or _fallback_headline(facts)


def headline_prompt(facts: dict) -> str:
    """Prompt für den Kopf-Satz — nur berechnete Fakten, keine sensiblen Daten."""
    streak = facts.get("streak", 0)
    quote = facts.get("quote", 0)
    checked_in = facts.get("checked_in")
    longest = facts.get("longest_streak", 0)
    best_day = facts.get("best_weekday")
    missed = facts.get("days_since_checkin")

    lage = [
        f"aktueller Streak: {streak} Tage",
        f"längster Streak bisher: {longest} Tage",
        f"Check-in-Quote der letzten 14 Tage: {quote}%",
        f"heute schon eingecheckt: {'ja' if checked_in else 'nein'}",
    ]
    if best_day:
        lage.append(f"aktivster Wochentag: {best_day}")
    if missed is not None:
        lage.append(f"letzter Check-in vor {missed} Tag(en)")

    return (
        "Formuliere EINEN kurzen, motivierenden Satz auf Deutsch (max. 20 Wörter) "
        "für die Startseite des Coachs, passend zur folgenden Lage. Nenne eine "
        "konkrete Zahl. Bei laufendem Streak bestärkend; nach verpasstem Check-in "
        "aufbauend statt tadelnd. Gib nur den Satz zurück, ohne Anführungszeichen.\n\n"
        "Lage: " + "; ".join(lage) + "."
    )


def _fallback_chat(messages: list[dict], ctx: dict) -> str:
    """Freundliche, datenbasierte Antwort, wenn die API nicht verfügbar ist."""
    streak = ctx.get("streak", 0)
    goal = ctx.get("goal")
    ziel = f" für „{goal}“" if goal else ""
    if streak > 0:
        return (
            f"Der Coach ist gerade offline – aber deine {streak} Tage Streak"
            f"{ziel} sprechen für sich. Definiere die kleinste nächste Handlung "
            "und mach sie noch heute."
        )
    return (
        "Der Coach ist gerade offline. Fang klein an: lege eine konkrete, "
        f"messbare nächste Handlung{ziel} fest und checke heute ein – so startet "
        "dein Streak."
    )


def _fallback_headline(facts: dict) -> str:
    """Kopf-Satz aus den Fakten zusammengesetzt, wenn die API nicht antwortet."""
    streak = facts.get("streak", 0)
    quote = facts.get("quote", 0)
    checked_in = facts.get("checked_in")
    longest = facts.get("longest_streak", 0)

    if streak <= 0:
        return (
            "Noch kein aktiver Streak – heute ist der beste Tag, den ersten "
            "Check-in zu setzen."
        )
    if streak >= longest and streak > 1:
        return f"{streak} Tage am Stück – dein bisher längster Lauf. Weiter so!"
    if not checked_in:
        return (
            f"{streak} Tage Streak stehen auf dem Spiel – ein kurzer Check-in "
            "heute hält die Kette am Leben."
        )
    return f"{streak} Tage dran, {quote}% Check-in-Quote – solide Arbeit, bleib dran."
