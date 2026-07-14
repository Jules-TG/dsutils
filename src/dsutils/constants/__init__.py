"""
**Country codes** adhering to ISO 3166-1 alpha-2:

- `EU27_COUNTRY_CODES_MAP`: `dict` mapping each EU27 country code to its country name.
- `INVERSE_EU27_CODES_MAP`: `dict` mapping each EU27 country name to its country code.
- `EU27_COUNTRY_CODES`: `list` of EU27 country codes.
- `EU27_COUNTRIES`: `list` of EU27 country names.
"""

EU27_COUNTRY_CODES_MAP: dict = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "GR": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LV": "Latvia",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "SE": "Sweden",
}

INVERSE_EU27_CODES_MAP: dict = {v: k for k, v in EU27_COUNTRY_CODES_MAP.items()}
EU27_COUNTRY_CODES: list = list(EU27_COUNTRY_CODES_MAP.keys())
EU27_COUNTRIES: list = list(EU27_COUNTRY_CODES_MAP.values())
