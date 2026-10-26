from src.clinical_trials import normalize, geographic_counts, yearly_counts, fetch_studies
from unittest.mock import patch, Mock
import pytest

SAMPLE = {'protocolSection': {'identificationModule': {'nctId': 'NCT12345678', 'briefTitle': 'HIV example'},
          'statusModule': {'overallStatus': 'RECRUITING', 'startDateStruct': {'date': '2024-03'}},
          'contactsLocationsModule': {'locations': [{'country': 'Nigeria'}, {'country': 'Nigeria'}, {'country': 'Ghana'}]}}}

def test_normalization():
    row = normalize(SAMPLE)
    assert row['nct_id'] == 'NCT12345678'
    assert row['countries'] == ['Ghana', 'Nigeria']

def test_country_deduplication():
    assert geographic_counts([SAMPLE], 'country') == [{'name': 'Ghana', 'unique_trials': 1}, {'name': 'Nigeria', 'unique_trials': 1}]

def test_year():
    assert yearly_counts([SAMPLE]) == [{'year': 2024, 'unique_trials': 1}]

def test_invalid_limit():
    with pytest.raises(ValueError):
        fetch_studies(max_records=0)

def test_pagination():
    responses = []
    for payload in ({'studies': [SAMPLE], 'nextPageToken': 'next'}, {'studies': [SAMPLE]}):
        r = Mock(); r.json.return_value = payload; responses.append(r)
    with patch('src.clinical_trials.requests.Session') as factory:
        factory.return_value.__enter__.return_value.get.side_effect = responses
        result = fetch_studies(max_records=3)
        assert result['count'] == 2
        assert factory.return_value.__enter__.return_value.get.call_args_list[1].kwargs['params']['pageToken'] == 'next'
