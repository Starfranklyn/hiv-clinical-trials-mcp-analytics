"""ClinicalTrials.gov API v2 retrieval and normalized HIV trial analysis."""
from collections import Counter
from datetime import datetime, timezone
from typing import Any
import re
import requests

BASE_URL = 'https://clinicaltrials.gov/api/v2/studies'
NCT_PATTERN = re.compile(r'^NCT\d{8}$', re.I)


def fetch_studies(query: str = 'HIV', max_records: int = 200, page_size: int = 100) -> dict[str, Any]:
    if not query.strip() or len(query) > 200:
        raise ValueError('query must be 1–200 characters')
    if not 1 <= max_records <= 5000:
        raise ValueError('max_records must be between 1 and 5000')
    if not 1 <= page_size <= 1000:
        raise ValueError('page_size must be between 1 and 1000')
    records: list[dict] = []
    token = None
    with requests.Session() as session:
        while len(records) < max_records:
            params = {'query.term': query, 'pageSize': min(page_size, max_records - len(records)), 'format': 'json'}
            if token:
                params['pageToken'] = token
            response = session.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            batch = payload.get('studies', [])
            records.extend(batch)
            token = payload.get('nextPageToken')
            if not token or not batch:
                break
    return {'studies': records, 'count': len(records), 'query': query,
            'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
            'truncated_at_limit': bool(token and len(records) >= max_records),
            'source': BASE_URL}


def normalize(study: dict) -> dict:
    p = study.get('protocolSection') or {}
    ident = p.get('identificationModule') or {}
    status = p.get('statusModule') or {}
    design = p.get('designModule') or {}
    locations = (p.get('contactsLocationsModule') or {}).get('locations') or []
    countries = sorted({loc['country'].strip() for loc in locations if loc.get('country')})
    interventions = (p.get('armsInterventionsModule') or {}).get('interventions') or []
    results = study.get('resultsSection') or {}
    outcomes = results.get('outcomeMeasuresModule') or results.get('outcomesModule') or {}
    return {'nct_id': ident.get('nctId'), 'title': ident.get('briefTitle') or ident.get('officialTitle'),
            'status': status.get('overallStatus'), 'study_type': design.get('studyType'),
            'phases': design.get('phases') or [], 'start_date': (status.get('startDateStruct') or {}).get('date'),
            'enrollment': (design.get('enrollmentInfo') or {}).get('count'),
            'countries': countries, 'locations': [{'facility': l.get('facility'), 'city': l.get('city'),
                'country': l.get('country')} for l in locations],
            'interventions': [{'name': x.get('name'), 'type': x.get('type')} for x in interventions],
            'has_results': bool(results), 'reported_outcomes': len(outcomes.get('outcomeMeasures') or outcomes.get('primaryOutcomes') or []),
            'source_url': f"https://clinicaltrials.gov/study/{ident.get('nctId')}" if ident.get('nctId') else None}


def get_study(nct_id: str) -> dict:
    if not NCT_PATTERN.fullmatch(nct_id):
        raise ValueError('NCT ID must look like NCT12345678')
    url = f'{BASE_URL}/{nct_id.upper()}'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return normalize(response.json())


def geographic_counts(studies: list[dict], dimension: str = 'country') -> list[dict]:
    if dimension not in ('country', 'continent'):
        raise ValueError('dimension must be country or continent')
    counts = Counter()
    if dimension == 'continent':
        import pycountry_convert as pc
        aliases = {'Côte D’Ivoire': 'Ivory Coast', 'Côte d’Ivoire': 'Ivory Coast',
                   'Korea, Republic of': 'South Korea', 'Tanzania, United Republic of': 'Tanzania'}
    for study in studies:
        countries = normalize(study)['countries']
        values = set()
        for country in countries:
            if dimension == 'country':
                values.add(country)
            else:
                try:
                    alpha = pc.country_name_to_country_alpha2(aliases.get(country, country))
                    code = pc.country_alpha2_to_continent_code(alpha)
                    values.add(pc.convert_continent_code_to_continent_name(code))
                except (KeyError, ValueError, LookupError):
                    values.add('Unknown')
        counts.update(values)
    return [{'name': name, 'unique_trials': count} for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def yearly_counts(studies: list[dict]) -> list[dict]:
    counts = Counter()
    for study in studies:
        date = normalize(study)['start_date']
        if date and re.match(r'^\d{4}', date):
            counts[date[:4]] += 1
    return [{'year': int(year), 'unique_trials': count} for year, count in sorted(counts.items())]
