"""KI-Coach über die Anthropic-API (FA-11), datensparsam (NFA-09).

An die KI gehen ausschliesslich der Ziel-Text bzw. der Streak-Zähler — niemals
Zugangsdaten, E-Mail-Adressen oder fremde Chat-Inhalte (NFA-09 AK1). Ist kein
`ANTHROPIC_API_KEY` gesetzt (oder das SDK fehlt), greift ein deterministischer
lokaler Fallback, damit die App offline läuft und Tests netzfrei bleiben.
"""
import os

MODEL = "claude-opus-4-8"
MAX_TOKENS = 200


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
