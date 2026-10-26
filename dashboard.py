"""
HIV Clinical Trials Research Dashboard

Interactive dashboard built with:
- Python
- Plotly
- Dash
- Pandas
- ClinicalTrials.gov API v2

Reuses the analytical functions from the existing MCP project.
"""

from uuid import uuid4

import pandas as pd
import plotly.express as px

from dash import (
    Dash,
    Input,
    Output,
    State,
    dcc,
    html,
    dash_table,
    no_update,
)

from src.clinical_trials import (
    fetch_studies,
    normalize,
    geographic_counts,
    yearly_counts,
)


# ============================================================
# 1. APPLICATION CONFIGURATION
# ============================================================

app = Dash(
    __name__,
    title="HIV Clinical Trials | Research Dashboard"
)

server = app.server

# Local, single-user cache.
# This is suitable for development, not multi-user deployment.
CACHE = {}

BG = "#0b1220"
CARD = "#172235"
TEXT = "#e8eef8"
MUTED = "#a9b9d1"
ACCENT = "#36c3a6"


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def panel(children):
    """Create a dashboard panel."""

    return html.Div(
        children,
        style={
            "background": CARD,
            "borderRadius": "14px",
            "padding": "18px",
            "minWidth": 0,
        },
    )


def fig_theme(fig):
    """Apply consistent styling to Plotly charts."""

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font={"color": TEXT},
        margin={
            "l": 20,
            "r": 20,
            "t": 45,
            "b": 35,
        },
        hoverlabel={"bgcolor": "#26374f"},
    )

    return fig


def empty_chart(title):
    """Return a placeholder chart when no data is available."""

    fig = px.scatter(title=title)

    fig.add_annotation(
        text="Retrieve data or adjust filters",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 15},
    )

    return fig_theme(fig)


def metric(title, value):
    """Create a dashboard metric card."""

    return html.Div(
        [
            html.Div(
                title,
                style={
                    "color": MUTED,
                    "fontSize": "13px",
                },
            ),
            html.Div(
                f"{value:,}",
                style={
                    "fontSize": "27px",
                    "fontWeight": "bold",
                },
            ),
        ],
        style={
            "background": CARD,
            "padding": "15px 20px",
            "borderRadius": "12px",
            "flex": "1 1 160px",
        },
    )


# ============================================================
# 3. DASHBOARD LAYOUT
# ============================================================

app.layout = html.Div(

    [

        # Store the current dataset reference
        dcc.Store(
            id="store-key",
            storage_type="memory",
        ),

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        html.Div(
            [
                html.H1(
                    "HIV Clinical Trials | Research Dashboard",
                    style={"margin": "0 0 6px"},
                ),

                html.P(
                    "Explore registered HIV clinical trials "
                    "retrieved from ClinicalTrials.gov API v2.",
                    style={
                        "color": MUTED,
                        "margin": 0,
                    },
                ),
            ],
            style={"padding": "22px 0"},
        ),

        # ----------------------------------------------------
        # DATA RETRIEVAL
        # ----------------------------------------------------

        panel(
            html.Div(
                [

                    html.Div(
                        [
                            html.Label("Search term"),

                            dcc.Input(
                                id="query",
                                value="HIV",
                                type="text",
                                maxLength=200,
                                debounce=True,
                                style={
                                    "width": "100%",
                                    "padding": "10px",
                                    "color": "#111827",
                                    "boxSizing": "border-box",
                                },
                            ),
                        ],
                        style={"flex": "2 1 240px"},
                    ),

                    html.Div(
                        [
                            html.Label("Maximum records"),

                            dcc.Dropdown(
                                id="limit",
                                options=[
                                    {
                                        "label": f"{n:,}",
                                        "value": n,
                                    }
                                    for n in (
                                        100,
                                        250,
                                        500,
                                        1000,
                                        2000,
                                        5000,
                                    )
                                ],
                                value=500,
                                clearable=False,
                                style={"color": "#111827"},
                            ),
                        ],
                        style={"flex": "1 1 160px"},
                    ),

                    html.Button(
                        "Retrieve trials",
                        id="load",
                        n_clicks=0,
                        style={
                            "padding": "11px 20px",
                            "background": ACCENT,
                            "color": "#07131c",
                            "fontWeight": "bold",
                            "border": "none",
                            "borderRadius": "8px",
                            "cursor": "pointer",
                            "alignSelf": "end",
                        },
                    ),

                ],
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "12px",
                    "alignItems": "end",
                },
            )
        ),

        # Retrieval status
        html.Div(
            id="status",
            role="status",
            style={
                "color": MUTED,
                "margin": "12px 0",
            },
        ),

        # ----------------------------------------------------
        # METRIC CARDS
        # ----------------------------------------------------

        html.Div(
            id="metrics",
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "12px",
                "margin": "14px 0",
            },
        ),

        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        panel(
            html.Div(
                [

                    html.Div(
                        [
                            html.Label("Study status"),

                            dcc.Dropdown(
                                id="status-filter",
                                multi=True,
                                placeholder="All statuses",
                                style={"color": "#111827"},
                            ),
                        ],
                        style={"flex": "1 1 200px"},
                    ),

                    html.Div(
                        [
                            html.Label("Country"),

                            dcc.Dropdown(
                                id="country-filter",
                                multi=True,
                                placeholder="All countries",
                                style={"color": "#111827"},
                            ),
                        ],
                        style={"flex": "1 1 200px"},
                    ),

                    html.Div(
                        [
                            html.Label("Study type"),

                            dcc.Dropdown(
                                id="type-filter",
                                multi=True,
                                placeholder="All types",
                                style={"color": "#111827"},
                            ),
                        ],
                        style={"flex": "1 1 200px"},
                    ),

                ],
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "12px",
                },
            )
        ),

        # ----------------------------------------------------
        # INTERACTIVE CHARTS
        # ----------------------------------------------------

        html.Div(
            [

                panel(
                    dcc.Graph(
                        id="country-fig",
                        config={"displaylogo": False},
                        style={"height": "440px"},
                    )
                ),

                panel(
                    dcc.Graph(
                        id="continent-fig",
                        config={"displaylogo": False},
                        style={"height": "440px"},
                    )
                ),

                panel(
                    dcc.Graph(
                        id="trend-fig",
                        config={"displaylogo": False},
                        style={"height": "440px"},
                    )
                ),

                panel(
                    dcc.Graph(
                        id="status-fig",
                        config={"displaylogo": False},
                        style={"height": "440px"},
                    )
                ),

            ],
            style={
                "display": "grid",
                "gridTemplateColumns": (
                    "repeat(auto-fit, minmax(min(100%, 430px), 1fr))"
                ),
                "gap": "14px",
                "margin": "14px 0",
            },
        ),

        # ----------------------------------------------------
        # CLINICAL TRIAL TABLE
        # ----------------------------------------------------

        panel(
            [

                html.Div(
                    [

                        html.H3(
                            "Trial Records",
                            style={"margin": 0},
                        ),

                        html.Button(
                            "Download filtered CSV",
                            id="download-btn",
                            style={
                                "padding": "9px",
                                "borderRadius": "8px",
                                "cursor": "pointer",
                            },
                        ),

                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "gap": "12px",
                        "flexWrap": "wrap",
                        "marginBottom": "12px",
                    },
                ),

                dash_table.DataTable(
                    id="table",

                    columns=[
                        {"name": "NCT ID", "id": "nct_id"},
                        {"name": "Title", "id": "title"},
                        {"name": "Status", "id": "status"},
                        {"name": "Type", "id": "study_type"},
                        {"name": "Start", "id": "start_date"},
                        {"name": "Countries", "id": "countries_text"},
                    ],

                    page_size=12,

                    sort_action="native",
                    filter_action="native",

                    style_table={
                        "overflowX": "auto",
                    },

                    style_header={
                        "backgroundColor": "#24364e",
                        "color": TEXT,
                        "fontWeight": "bold",
                    },

                    style_cell={
                        "backgroundColor": CARD,
                        "color": TEXT,
                        "textAlign": "left",
                        "maxWidth": "420px",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "padding": "10px",
                    },

                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "#1c2b40",
                        }
                    ],
                ),

                dcc.Download(id="csv-download"),

            ]
        ),

        # ----------------------------------------------------
        # RESEARCH INTERPRETATION NOTE
        # ----------------------------------------------------

        html.P(
            "Interpretation: A study with sites in multiple "
            "countries counts once in each country. "
            "The same rule applies across continents. "
            "Counts reflect retrieved records and active filters, "
            "not disease prevalence or clinical trial access. "
            "Results may be limited by the selected record cap.",

            style={
                "color": MUTED,
                "fontSize": "13px",
                "marginTop": "18px",
            },
        ),

    ],

    style={
        "background": BG,
        "color": TEXT,
        "minHeight": "100vh",
        "padding": "0 22px 30px",
        "fontFamily": "Segoe UI, Arial, sans-serif",
        "maxWidth": "1500px",
        "margin": "auto",
    },
)


# ============================================================
# 4. RETRIEVE CLINICAL TRIAL DATA
# ============================================================

@app.callback(
    Output("store-key", "data"),
    Output("status", "children"),

    Input("load", "n_clicks"),

    State("query", "value"),
    State("limit", "value"),

    prevent_initial_call=True,
)
def load_trials(n_clicks, query, limit):

    try:

        result = fetch_studies(
            query=query or "",
            max_records=int(limit),
        )

        key = str(uuid4())

        CACHE.clear()

        CACHE[key] = {
            "raw": result["studies"],

            "rows": [
                normalize(study)
                for study in result["studies"]
            ],

            "meta": {
                k: v
                for k, v in result.items()
                if k != "studies"
            },
        }

        truncated = ""

        if result["truncated_at_limit"]:
            truncated = (
                " | LIMIT REACHED: "
                "Results are not exhaustive."
            )

        message = (
            f"Retrieved {result['count']:,} studies "
            f"at {result['retrieved_at_utc']}"
            f"{truncated}"
        )

        return key, message

    except Exception as exc:

        return (
            None,
            f"Retrieval failed: "
            f"{type(exc).__name__}: {exc}",
        )


# ============================================================
# 5. POPULATE FILTER OPTIONS
# ============================================================

@app.callback(
    Output("status-filter", "options"),
    Output("country-filter", "options"),
    Output("type-filter", "options"),

    Output("status-filter", "value"),
    Output("country-filter", "value"),
    Output("type-filter", "value"),

    Input("store-key", "data"),
)
def populate_filters(key):

    data = CACHE.get(key, {}).get("rows", [])

    statuses = sorted({
        row["status"]
        for row in data
        if row.get("status")
    })

    countries = sorted({
        country
        for row in data
        for country in row["countries"]
    })

    study_types = sorted({
        row["study_type"]
        for row in data
        if row.get("study_type")
    })

    return (
        statuses,
        countries,
        study_types,
        [],
        [],
        [],
    )


# ============================================================
# 6. FILTER CLINICAL TRIAL RECORDS
# ============================================================

def filtered_indices(
    key,
    statuses,
    countries,
    study_types,
):

    rows = CACHE.get(key, {}).get("rows", [])

    selected = []

    for index, row in enumerate(rows):

        if statuses:
            if row.get("status") not in statuses:
                continue

        if countries:
            if not set(row["countries"]).intersection(countries):
                continue

        if study_types:
            if row.get("study_type") not in study_types:
                continue

        selected.append(index)

    return selected


# ============================================================
# 7. UPDATE INTERACTIVE VISUALIZATIONS
# ============================================================

@app.callback(
    Output("country-fig", "figure"),
    Output("continent-fig", "figure"),
    Output("trend-fig", "figure"),
    Output("status-fig", "figure"),

    Output("table", "data"),
    Output("metrics", "children"),

    Input("store-key", "data"),
    Input("status-filter", "value"),
    Input("country-filter", "value"),
    Input("type-filter", "value"),
)
def update_dashboard(
    key,
    statuses,
    countries,
    study_types,
):

    sample = CACHE.get(key, {})

    indices = filtered_indices(
        key,
        statuses or [],
        countries or [],
        study_types or [],
    )

    raw = [
        sample["raw"][i]
        for i in indices
    ] if sample else []

    rows = [
        sample["rows"][i]
        for i in indices
    ] if sample else []

    # No data available
    if not rows:

        return (
            empty_chart("Top Countries"),
            empty_chart("Trials by Continent"),
            empty_chart("Trials by Start Year"),
            empty_chart("Study Status"),
            [],
            [],
        )

    # --------------------------------------------------------
    # COUNTRY ANALYSIS
    # --------------------------------------------------------

    by_country = geographic_counts(
        raw,
        "country",
    )[:15]

    country_df = pd.DataFrame(by_country)

    if not country_df.empty:

        country_fig = px.bar(
            country_df.iloc[::-1],
            x="unique_trials",
            y="name",
            orientation="h",
            title="Top 15 Countries",
            labels={
                "unique_trials": "Studies",
                "name": "Country",
            },
        )

    else:
        country_fig = empty_chart("Top Countries")

    # --------------------------------------------------------
    # CONTINENT ANALYSIS
    # --------------------------------------------------------

    by_continent = geographic_counts(
        raw,
        "continent",
    )

    if by_continent:

        continent_df = pd.DataFrame(by_continent)

        continent_fig = px.bar(
            continent_df,
            x="name",
            y="unique_trials",
            title="Trials by Continent",
            labels={
                "name": "Continent",
                "unique_trials": "Studies",
            },
        )

    else:
        continent_fig = empty_chart(
            "Trials by Continent"
        )

    # --------------------------------------------------------
    # YEARLY TREND ANALYSIS
    # --------------------------------------------------------

    by_year = yearly_counts(raw)

    if by_year:

        year_df = pd.DataFrame(by_year)

        trend_fig = px.line(
            year_df,
            x="year",
            y="unique_trials",
            markers=True,
            title="Clinical Trials by Start Year",
            labels={
                "year": "Start Year",
                "unique_trials": "Studies",
            },
        )

    else:
        trend_fig = empty_chart(
            "Trials by Start Year"
        )

    # --------------------------------------------------------
    # STUDY STATUS ANALYSIS
    # --------------------------------------------------------

    status_counts = pd.Series(
        [
            row.get("status") or "Unknown"
            for row in rows
        ]
    ).value_counts().reset_index()

    status_counts.columns = [
        "status",
        "trials",
    ]

    status_fig = px.bar(
        status_counts,
        x="status",
        y="trials",
        title="Clinical Trials by Study Status",
        labels={
            "status": "Status",
            "trials": "Studies",
        },
    )

    # --------------------------------------------------------
    # APPLY CHART STYLING
    # --------------------------------------------------------

    for fig in (
        country_fig,
        continent_fig,
        trend_fig,
        status_fig,
    ):
        fig_theme(fig)

    # --------------------------------------------------------
    # PREPARE TABLE
    # --------------------------------------------------------

    table_data = []

    for row in rows:

        table_data.append(
            {
                "nct_id": row.get("nct_id"),
                "title": row.get("title"),
                "status": row.get("status"),
                "study_type": row.get("study_type"),
                "start_date": row.get("start_date"),
                "countries_text": ", ".join(
                    row.get("countries", [])
                ),
            }
        )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    metrics = [
        metric("Filtered Studies", len(rows)),

        metric(
            "Countries",
            len(geographic_counts(raw, "country")),
        ),

        metric(
            "Continents",
            len(by_continent),
        ),

        metric(
            "Studies With Locations",
            sum(
                bool(row["countries"])
                for row in rows
            ),
        ),
    ]

    return (
        country_fig,
        continent_fig,
        trend_fig,
        status_fig,
        table_data,
        metrics,
    )


# ============================================================
# 8. DOWNLOAD FILTERED DATA
# ============================================================

@app.callback(
    Output("csv-download", "data"),

    Input("download-btn", "n_clicks"),

    State("store-key", "data"),
    State("status-filter", "value"),
    State("country-filter", "value"),
    State("type-filter", "value"),

    prevent_initial_call=True,
)
def download_data(
    n_clicks,
    key,
    statuses,
    countries,
    study_types,
):

    sample = CACHE.get(key)

    if not sample:
        return no_update

    indices = filtered_indices(
        key,
        statuses or [],
        countries or [],
        study_types or [],
    )

    rows = [
        sample["rows"][i]
        for i in indices
    ]

    if not rows:
        return no_update

    export_rows = []

    for row in rows:

        record = row.copy()

        record["countries"] = "; ".join(
            row.get("countries", [])
        )

        record["locations"] = str(
            row.get("locations", [])
        )

        record["interventions"] = str(
            row.get("interventions", [])
        )

        export_rows.append(record)

    dataframe = pd.DataFrame(export_rows)

    return dcc.send_data_frame(
        dataframe.to_csv,
        "hiv_trials_filtered.csv",
        index=False,
    )


# ============================================================
# 9. RUN DASHBOARD
# ============================================================

if __name__ == "__main__":

    print("Starting HIV Clinical Trials Dashboard...")

    app.run(
        debug=False,
        host="127.0.0.1",
        port=8050,
    )