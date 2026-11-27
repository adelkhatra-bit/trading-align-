"""Normalisation et provenance des annonces économiques ALIGN.

Le flux Forex Factory/Fair Economy reste un agrégateur de calendrier, pas une source
officielle de publication des statistiques. Les valeurs réelles ne sont affichées
que si le flux les fournit; sinon le rapport le dit explicitement.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import hashlib
import re
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc
PARIS = ZoneInfo("Europe/Paris")

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CALENDAR_SOURCE = "Forex Factory / Fair Economy (flux agrégé)"

_OFFICIAL_SOURCES = (
    {
        "name": "U.S. Bureau of Labor Statistics — Consumer Price Index",
        "url": "https://www.bls.gov/news.release/cpi.toc.htm",
        "keywords": ("consumer price index", "cpi"),
    },
    {
        "name": "U.S. Bureau of Labor Statistics — Producer Price Index",
        "url": "https://www.bls.gov/news.release/ppi.toc.htm",
        "keywords": ("producer price index", "ppi"),
    },
    {
        "name": "U.S. Bureau of Labor Statistics — Employment Situation",
        "url": "https://www.bls.gov/news.release/empsit.toc.htm",
        "keywords": (
            "employment situation", "nonfarm payroll", "payrolls",
            "unemployment rate",
        ),
    },
    {
        "name": "U.S. Bureau of Labor Statistics — JOLTS",
        "url": "https://www.bls.gov/news.release/jolts.toc.htm",
        "keywords": ("jolts", "job openings"),
    },
    {
        "name": "U.S. Department of Labor — Weekly Unemployment Claims",
        "url": "https://www.dol.gov/ui/data.pdf",
        "keywords": ("unemployment claims", "jobless claims", "initial claims"),
    },
    {
        "name": "U.S. Bureau of Economic Analysis (BEA)",
        "url": "https://www.bea.gov/news/schedule",
        "keywords": (
            "gross domestic product", "prelim gdp", "gdp", "core pce",
            "pce", "personal income", "personal spending",
        ),
    },
    {
        "name": "Federal Reserve",
        "url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "keywords": (
            "fomc", "federal reserve", "fed funds", "rate decision",
            "interest rate", "powell", "fed ", "fed governor", "speaks",
            "beige book",
        ),
    },
    {
        "name": "U.S. Census Bureau",
        "url": "https://www.census.gov/economic-indicators/calendar-listview.html",
        "keywords": (
            "goods trade balance", "trade balance", "international trade",
            "wholesale inventories", "retail inventories",
            "advance economic indicators", "advance wholesale",
            "advance retail", "retail sales", "durable goods", "new home sales",
        ),
    },
)

_LOW_IMPACT_MACRO_KEYWORDS = (
    "goods trade balance", "trade balance", "international trade",
    "wholesale inventories", "retail inventories", "advance economic indicators",
    "advance wholesale", "advance retail", "retail sales", "durable goods",
    "new home sales", "consumer confidence", "unemployment claims",
    "jobless claims", "core pce", "pce", "personal income", "personal spending",
    "prelim gdp", "gdp", "employment situation", "nonfarm payroll", "payrolls",
    "consumer price index", "cpi", "producer price index", "ppi", "jolts",
    "job openings", "fomc", "federal reserve", "fed funds", "rate decision",
    "interest rate", "powell", "fed ", "speaks", "beige book",
)


def _clean(value, limit=240):
    text = re.sub(r"<[^>]*>", " ", "" if value is None else str(value))
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _timestamp(value):
    """Convertit uniquement une date avec fuseau explicite; jamais d'heure locale implicite."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if number > 10_000_000_000:
            number /= 1000.0
        return int(number)
    raw = str(value).strip()
    parsed = None
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        try:
            parsed = email.utils.parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed is None or parsed.tzinfo is None:
        return None
    return int(parsed.astimezone(UTC).timestamp())


def _official_source(title):
    lowered = title.lower()
    for source in _OFFICIAL_SOURCES:
        if any(keyword in lowered for keyword in source["keywords"]):
            return {"name": source["name"], "url": source["url"]}
    return None


def normaliser_evenement(raw, retrieved_at):
    """Normalise un événement USD et conserve les limites de provenance."""
    if not isinstance(raw, dict):
        return None
    currency = _clean(raw.get("country") or raw.get("currency"), 8).upper()
    title = _clean(raw.get("title") or raw.get("name"))
    event_ts = _timestamp(raw.get("date") or raw.get("event_at"))
    if currency != "USD" or not title or event_ts is None:
        return None

    impact = _clean(raw.get("impact") or "Unknown", 16).title()
    lowered = title.lower()
    macro_match = any(keyword in lowered for keyword in _LOW_IMPACT_MACRO_KEYWORDS)
    if impact not in ("High", "Medium", "Low"):
        return None
    if impact == "Low" and not macro_match:
        relevance = "calendar_low"
    elif impact == "Low":
        relevance = "macro_watch"
    else:
        relevance = "calendar_impact"

    official = _official_source(title)
    event_utc = dt.datetime.fromtimestamp(event_ts, UTC)
    event_paris = event_utc.astimezone(PARIS)
    # updated_at décrit la mise à jour de la fiche calendrier, pas la publication économique.
    # Ne jamais le présenter comme l'heure réelle de publication de la statistique.
    published_value = next(
        (raw.get(key) for key in (
            "published_at", "publishedAt", "publication_time", "publicationTime",
            "pubDate", "datePublished",
        ) if raw.get(key) not in (None, "")),
        None,
    )
    published_ts = _timestamp(published_value)
    updated_value = next(
        (raw.get(key) for key in ("updated_at", "updatedAt", "last_updated", "lastUpdated")
         if raw.get(key) not in (None, "")),
        None,
    )
    updated_ts = _timestamp(updated_value)
    actual_raw = next(
        (raw.get(key) for key in ("actual", "actualValue", "result")
         if raw.get(key) not in (None, "")),
        None,
    )
    actual = _clean(actual_raw, 100)
    forecast = _clean(raw.get("forecast"), 100)
    previous = _clean(raw.get("previous"), 100)
    identity = "|".join((CALENDAR_SOURCE, currency, title.casefold(), str(event_ts)))
    event_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]

    return {
        "id": event_id,
        "titre": title,
        "pays": currency,
        "currency": currency,
        "t": event_ts,
        "event_at_utc": event_utc.isoformat().replace("+00:00", "Z"),
        "event_at_paris": event_paris.isoformat(),
        "impact": impact,
        "importance": impact,
        "importance_source": CALENDAR_SOURCE,
        "relevance": relevance,
        "entry_block": impact in ("High", "Medium"),
        "prev": forecast,
        "forecast": forecast,
        "avant": previous,
        "previous": previous,
        "actual": actual or None,
        "actual_source": CALENDAR_SOURCE if actual else None,
        "actual_verified_officially": False,
        "actual_first_seen_at": int(retrieved_at) if actual else None,
        "published_at": published_ts,
        "published_at_source": CALENDAR_SOURCE if published_ts is not None else None,
        "published_at_paris": (
            dt.datetime.fromtimestamp(published_ts, PARIS).isoformat()
            if published_ts is not None else None
        ),
        "source_updated_at": updated_ts,
        "source_updated_at_paris": (
            dt.datetime.fromtimestamp(updated_ts, PARIS).isoformat()
            if updated_ts is not None else None
        ),
        "source_name": CALENDAR_SOURCE,
        "source_url": CALENDAR_URL,
        "retrieved_at": int(retrieved_at),
        "official_source_name": official["name"] if official else None,
        "official_source_url": official["url"] if official else None,
    }


def normaliser_evenements(raw_events, retrieved_at):
    """Retourne (événements de veille, tous les événements USD du jour)."""
    daily = {}
    for raw in raw_events if isinstance(raw_events, list) else []:
        event = normaliser_evenement(raw, retrieved_at)
        if event is not None:
            daily[event["id"]] = event
    all_usd = sorted(daily.values(), key=lambda event: (event["t"], event["id"]))
    blocking = [event for event in all_usd if event["impact"] in ("High", "Medium")]
    watch = [
        event for event in all_usd
        if event["impact"] == "Low" and event["relevance"] == "macro_watch"
    ]
    return blocking, watch, all_usd


def event_key(event):
    return str(event.get("id") or f'{event.get("t", 0)}:{event.get("titre", "")}')


def intervalle_rafraichissement(events, now):
    """Rafraîchit plus souvent avant/après une publication pour capter son résultat."""
    distances = []
    for event in events or []:
        try:
            distances.append(int(event["t"]) - int(now))
        except (KeyError, TypeError, ValueError):
            continue
    if any(-45 * 60 <= distance <= 120 * 60 for distance in distances):
        return 300
    if any(-6 * 3600 <= distance <= 6 * 3600 for distance in distances):
        return 900
    return 3600


def source_line(event):
    parts = [
        f"Calendrier: {event.get('source_name') or CALENDAR_SOURCE}",
        event.get("source_url") or CALENDAR_URL,
    ]
    if event.get("official_source_name") and event.get("official_source_url"):
        parts.extend((
            f"Référence officielle: {event['official_source_name']}",
            event["official_source_url"],
        ))
    return " • ".join(parts)


def facts_line(event):
    """Sépare les valeurs du flux agrégé des données officielles et de la réaction prix."""
    actual = _clean(event.get("actual"), 100)
    forecast_raw = event.get("forecast") if event.get("forecast") not in (None, "") else event.get("prev")
    previous_raw = event.get("previous") if event.get("previous") not in (None, "") else event.get("avant")
    forecast = _clean(forecast_raw, 100)
    previous = _clean(previous_raw, 100)
    if actual:
        line = f"📌 Valeur reçue du calendrier agrégé (non vérifiée directement auprès de l’organisme): {actual}"
    else:
        line = "📌 Valeur publiée: non reçue dans le flux au moment du contrôle; aucun chiffre n'est inventé."
    if forecast:
        line += f" • Prévision: {forecast}"
    if previous:
        line += f" • Précédent: {previous}"
    published = event.get("published_at_paris")
    if published:
        line += f"\n🕒 Publication déclarée par le flux: {published}"
    else:
        line += "\n🕒 Heure de publication distincte: non fournie par le flux."
    if actual:
        line += f"\nSource de la valeur: {event.get('actual_source') or CALENDAR_SOURCE}"
    official_name = event.get("official_source_name")
    official_url = event.get("official_source_url")
    if official_name and official_url:
        line += f"\n🔗 Référence officielle: {official_name} — {official_url}"
    else:
        line += f"\n🔗 Source du calendrier: {event.get('source_url') or CALENDAR_URL}"
    return line
