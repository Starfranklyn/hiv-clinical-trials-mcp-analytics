# HIV Clinical Trials MCP Server

An MCP adaptation of `Clinical_Trials.ipynb`, using ClinicalTrials.gov API v2. The original notebook is preserved in `notebooks/`.

## Setup

Python 3.10+ recommended:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python mcp_server.py
```

`python mcp_server.py` starts a **stdio** MCP server. It waits for a compatible MCP client and will not display a normal web interface. Example MCP client configuration (replace path with your absolute path):

```json
{
  "mcpServers": {
    "hiv-trials": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/hiv_clinical_trials_mcp/mcp_server.py"]
    }
  }
}
```

On Windows, use the absolute path to `.venv\\Scripts\\python.exe` instead. Configure the client's working directory to the project root if necessary, or use the absolute server path as shown.

## MCP tools

- `search_hiv_trials(max_records, status)` — search and normalize records
- `trial_details(nct_id)` — retrieve one study
- `trials_by_country(max_records)` — distinct trials by country
- `trials_by_continent(max_records)` — distinct trials by continent
- `hiv_trial_trends(max_records)` — count trials by start year
- `country_chart_data(max_records, top_n)` — chart-ready data

## Important limitations

- Calls require internet access to ClinicalTrials.gov. No live API access was used when building this project.
- Most tools cap retrieved records; results can be **partial samples**, not comprehensive counts. `truncated_at_limit` signals a cap where additional pages exist.
- Trial counts represent **registered studies**, not patient burden, trial access, or participants.
- A multicountry trial contributes to each applicable country; continent counts similarly overlap.
- `country_chart_data` returns labels and values; a connected client must render the chart.
- The original notebook contains additional exploratory outputs and adverse-event extractions; not all were converted to MCP tools in this first version.
- Do not use this research prototype for clinical decisions. Validate source fields, completeness, and analytic assumptions before publication.
