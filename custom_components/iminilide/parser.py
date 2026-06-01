from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import json
import re
import unicodedata

from .exceptions import IminilideParseError


@dataclass(slots=True, frozen=True)
class ControllerMetadata:
    name: str
    serial_number: str | None
    firmware_display: str | None
    firmware_base: str | None
    firmware_web: str | None


@dataclass(slots=True, frozen=True)
class VoieSummary:
    number: int
    name: str


@dataclass(slots=True, frozen=True)
class VoieConfig:
    number: int
    name: str
    active: bool
    sensor_type: str
    unit: str | None
    alarm_surveillance_enabled: bool
    alarm_high_threshold: float | None
    alarm_low_threshold: float | None


@dataclass(slots=True, frozen=True)
class ControllerDescription:
    metadata: ControllerMetadata
    voies: dict[int, VoieConfig]


@dataclass(slots=True, frozen=True)
class VoieReading:
    number: int
    name: str
    state: str
    raw_value: str | None
    numeric_value: float | None
    unit: str | None
    cycle_in_progress: str | None
    duration: str | None
    product_name: str | None


_TAG_RE = re.compile(r"<[^>]+>")
_INPUT_BY_NAME_TEMPLATE = r'<input[^>]*name="{field}"[^>]*>'
_INPUT_BY_ID_TEMPLATE = r'<input[^>]*id="{field}"[^>]*>'
_SELECT_TEMPLATE = r'<select[^>]*id="{field}"[^>]*>(.*?)</select>'
_OPTION_RE = re.compile(r"<option([^>]*)>(.*?)</option>", re.IGNORECASE | re.DOTALL)
_VALUE_RE = re.compile(r'value="([^"]*)"', re.IGNORECASE)
_FOOTER_RE = re.compile(
    r'<div class="element_bas_de_page">(.*?)</div>', re.IGNORECASE | re.DOTALL
)
_VOIE_LIST_RE = re.compile(
    r'href="/index\?configuration_voie(\d+)">Voie\s+\d+\s*\((.*?)\)</a>',
    re.IGNORECASE | re.DOTALL,
)


def parse_general_configuration(html: str) -> ControllerMetadata:
    """Parse controller metadata from the general configuration page."""

    footer_entries = _extract_footer_entries(html)
    return ControllerMetadata(
        name=_clean_text(_extract_input_value(html, "nom_iminilide")),
        serial_number=footer_entries.get("numero de serie"),
        firmware_display=footer_entries.get("afficheur"),
        firmware_base=footer_entries.get("base"),
        firmware_web=footer_entries.get("page internet"),
    )


def parse_voie_list(html: str) -> list[VoieSummary]:
    """Parse the list of voies from the voie configuration page."""

    voies: list[VoieSummary] = []
    for number, label in _VOIE_LIST_RE.findall(html):
        voies.append(VoieSummary(number=int(number), name=_clean_text(label)))

    if not voies:
        raise IminilideParseError("No voies were found in the configuration page")

    return voies


def parse_voie_configuration(html: str) -> VoieConfig:
    """Parse a single voie configuration page."""

    number = int(_extract_input_value(html, "numero"))
    name_parts = [
        _clean_text(_extract_input_value(html, "nom1")),
        _clean_text(_extract_input_value(html, "nom2")),
    ]
    name = " ".join(part for part in name_parts if part)
    sensor_type = _extract_selected_option_text(html, "type")
    unit = _empty_to_none(_extract_selected_option_text(html, "unite"))
    surveillance_enabled = _extract_selected_option_value(html, "surveillance_alarme") == "O"

    high_threshold: float | None = None
    low_threshold: float | None = None
    if surveillance_enabled and sensor_type not in {"Contact", "Contact Alim"}:
        high_threshold = _safe_float(_extract_input_value(html, "seuil_alarme_haut"))
        low_threshold = _safe_float(_extract_input_value(html, "seuil_alarme_bas"))

    return VoieConfig(
        number=number,
        name=name or f"Voie {number}",
        active=_is_checked(html, "active"),
        sensor_type=sensor_type,
        unit=unit,
        alarm_surveillance_enabled=surveillance_enabled,
        alarm_high_threshold=high_threshold,
        alarm_low_threshold=low_threshold,
    )


def parse_refresh_payload(payload: str) -> dict[int, VoieReading]:
    """Parse the JSON payload returned by POST / with action=refresh."""

    try:
        raw_data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise IminilideParseError("Refresh payload is not valid JSON") from exc

    readings: dict[int, VoieReading] = {}
    for key, raw_reading in raw_data.items():
        if not str(key).isdigit() or not isinstance(raw_reading, dict):
            continue

        try:
            number = int(raw_reading["num_voie"])
        except (KeyError, TypeError, ValueError) as exc:
            raise IminilideParseError("Refresh payload is missing a voie number") from exc

        raw_value = _empty_to_none(_clean_text(raw_reading.get("valeur_voie", "")))
        numeric_value, unit = _parse_measurement(raw_value)

        readings[number] = VoieReading(
            number=number,
            name=_clean_text(raw_reading.get("nom_voie", "")) or f"Voie {number}",
            state=_clean_text(raw_reading.get("etat_voie", "")),
            raw_value=raw_value,
            numeric_value=numeric_value,
            unit=unit,
            cycle_in_progress=_empty_to_none(_clean_text(raw_reading.get("cycle_en_cours", ""))),
            duration=_empty_to_none(_clean_text(raw_reading.get("duree", ""))),
            product_name=_empty_to_none(_clean_text(raw_reading.get("nom_produit", ""))),
        )

    return readings


def _extract_footer_entries(html: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw_entry in _FOOTER_RE.findall(html):
        cleaned = _clean_text(raw_entry)
        if ":" not in cleaned:
            continue
        label, value = cleaned.split(":", 1)
        entries[_normalize_ascii(label).lower().strip()] = value.strip()
    return entries


def _extract_input_value(html: str, field: str) -> str:
    tag = _extract_input_tag(html, field)
    value_match = _VALUE_RE.search(tag)
    if value_match is None:
        raise IminilideParseError(f"Input '{field}' has no value")
    return unescape(value_match.group(1))


def _extract_input_tag(html: str, field: str) -> str:
    for template in (_INPUT_BY_NAME_TEMPLATE, _INPUT_BY_ID_TEMPLATE):
        pattern = re.compile(template.format(field=re.escape(field)), re.IGNORECASE)
        match = pattern.search(html)
        if match is not None:
            return match.group(0)
    raise IminilideParseError(f"Input '{field}' was not found")


def _is_checked(html: str, field: str) -> bool:
    return "checked" in _extract_input_tag(html, field).lower()


def _extract_selected_option_value(html: str, field: str) -> str:
    value, _ = _extract_selected_option(html, field)
    return value


def _extract_selected_option_text(html: str, field: str) -> str:
    _, text = _extract_selected_option(html, field)
    return text


def _extract_selected_option(html: str, field: str) -> tuple[str, str]:
    select_match = re.search(
        _SELECT_TEMPLATE.format(field=re.escape(field)), html, re.IGNORECASE | re.DOTALL
    )
    if select_match is None:
        raise IminilideParseError(f"Select '{field}' was not found")

    first_option: tuple[str, str] | None = None
    for option_match in _OPTION_RE.finditer(select_match.group(1)):
        attributes, label = option_match.groups()
        value_match = _VALUE_RE.search(attributes)
        value = value_match.group(1) if value_match is not None else ""
        cleaned_label = _clean_text(label)
        if first_option is None:
            first_option = (value, cleaned_label)
        if "selected" in attributes.lower():
            return value, cleaned_label

    if first_option is not None:
        return first_option

    raise IminilideParseError(f"Select '{field}' has no options")


def _clean_text(value: str) -> str:
    text = _TAG_RE.sub(" ", unescape(value or ""))
    return " ".join(text.replace("\xa0", " ").split())


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    return value or None


def _safe_float(value: str) -> float | None:
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _parse_measurement(raw_value: str | None) -> tuple[float | None, str | None]:
    if not raw_value:
        return None, None

    match = re.match(r"^([-+]?\d+(?:[.,]\d+)?)\s*(.*)$", raw_value)
    if match is None:
        return None, None

    try:
        numeric_value = float(match.group(1).replace(",", "."))
    except ValueError:
        return None, None

    return numeric_value, _empty_to_none(match.group(2).strip())


def _normalize_ascii(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
