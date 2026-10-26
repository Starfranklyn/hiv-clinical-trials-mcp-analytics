"""Run with `python mcp_server.py` (stdio MCP transport)."""
from mcp.server.fastmcp import FastMCP
from src.clinical_trials import fetch_studies, normalize, get_study, geographic_counts, yearly_counts

mcp = FastMCP('HIV Clinical Trials Research')

@mcp.tool()
def search_hiv_trials(max_records: int = 100, status: str = '') -> dict:
    """Search registered HIV studies and return structured records with source IDs. Results may be capped."""
    result = fetch_studies('HIV', max_records=max_records)
    rows = [normalize(s) for s in result.pop('studies')]
    if status:
        rows = [r for r in rows if (r['status'] or '').casefold() == status.casefold()]
    return {**result, 'matched_count_in_sample': len(rows), 'records': rows,
            'note': 'Status filter applies to retrieved sample; counts are not population totals.'}

@mcp.tool()
def trial_details(nct_id: str) -> dict:
    """Retrieve an individual registered trial by its NCT identifier."""
    return get_study(nct_id)

@mcp.tool()
def trials_by_country(max_records: int = 500) -> dict:
    """Count distinct HIV trial NCT IDs per country; multicountry trials count once in each country."""
    result = fetch_studies('HIV', max_records=max_records)
    return {'counts': geographic_counts(result['studies'], 'country'), 'retrieved_count': result['count'],
            'retrieved_at_utc': result['retrieved_at_utc'], 'truncated_at_limit': result['truncated_at_limit'],
            'counting_rule': 'One NCT ID per country; totals across countries can exceed study count.'}

@mcp.tool()
def trials_by_continent(max_records: int = 500) -> dict:
    """Count distinct HIV trial NCT IDs per continent, with country-to-continent mapping."""
    result = fetch_studies('HIV', max_records=max_records)
    return {'counts': geographic_counts(result['studies'], 'continent'), 'retrieved_count': result['count'],
            'retrieved_at_utc': result['retrieved_at_utc'], 'truncated_at_limit': result['truncated_at_limit'],
            'counting_rule': 'One NCT ID per continent; multicontinent studies count in each continent.'}

@mcp.tool()
def hiv_trial_trends(max_records: int = 500) -> dict:
    """Summarize HIV trial start years in a bounded API sample."""
    result = fetch_studies('HIV', max_records=max_records)
    return {'start_year_counts': yearly_counts(result['studies']), 'retrieved_count': result['count'],
            'retrieved_at_utc': result['retrieved_at_utc'], 'truncated_at_limit': result['truncated_at_limit']}

@mcp.tool()
def country_chart_data(max_records: int = 500, top_n: int = 15) -> dict:
    """Return chart-ready labels and values for top countries (not a rendered image)."""
    if not 1 <= top_n <= 100:
        raise ValueError('top_n must be 1–100')
    result = trials_by_country(max_records)
    rows = result['counts'][:top_n]
    return {'labels': [r['name'] for r in rows], 'values': [r['unique_trials'] for r in rows],
            'metadata': {k: v for k, v in result.items() if k != 'counts'}}

if __name__ == '__main__':
    mcp.run(transport='stdio')
