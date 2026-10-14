from __future__ import annotations

PALETTE = {
    "graphite": "#20272D",
    "slate": "#3F5666",
    "steel": "#587487",
    "muted": "#6F7981",
    "border": "#D8DEE3",
    "surface": "#FFFFFF",
    "background": "#F5F6F7",
    "accent": "#B89B4F",
    "normal": "#4F7567",
    "warning": "#B68B32",
    "critical": "#B0603E",
    "breached": "#8E3F43",
}


DASHBOARD_CSS = """
<style>
:root {
    --ris-background: #0E141B;
    --ris-surface: #151D26;
    --ris-surface-2: #1B2530;
    --ris-border: #2B3743;
    --ris-text: #F3F6F8;
    --ris-muted: #A7B3BE;
    --ris-accent: #C7A76A;
    --ris-accent-blue: #74A7D8;
    --ris-accent-teal: #6FD2B0;
    --ris-warning: #F6C85F;
    --ris-danger: #FF6B6B;
}

html, body, [class*="css"] {
    color: var(--ris-text);
}

[data-testid="stAppViewContainer"] {
    background: var(--ris-background);
    color: var(--ris-text);
}

[data-testid="stMain"] {
    background: var(--ris-background);
}

[data-testid="stMainBlockContainer"] {
    max-width: 1520px;
    padding-top: 0.75rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: #111923;
    border-right: 1px solid var(--ris-border);
}

[data-testid="stSidebar"] * {
    color: var(--ris-text);
}

h1, h2, h3, h4, h5, h6, p, span, label, div {
    color: var(--ris-text);
}

small, .stCaption, [data-testid="stCaptionContainer"] {
    color: var(--ris-muted) !important;
}

[data-testid="stMetric"] {
    background: var(--ris-surface);
    border: 1px solid var(--ris-border);
    border-radius: 12px;
    padding: 0.8rem 0.9rem;
    min-height: 100px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.20);
}

[data-testid="stMetricLabel"] {
    color: var(--ris-muted);
    font-size: 0.78rem;
    font-weight: 650;
}

[data-testid="stMetricValue"] {
    color: var(--ris-text);
    font-weight: 750;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.35rem;
    border-bottom: 1px solid var(--ris-border);
    margin-bottom: 1rem;
}

.stTabs [data-baseweb="tab"] {
    height: 42px;
    padding: 0 1rem;
    border-radius: 8px 8px 0 0;
    color: var(--ris-muted);
    background: transparent;
    font-weight: 650;
}

.stTabs [aria-selected="true"] {
    color: var(--ris-text);
    background: var(--ris-surface);
    border: 1px solid var(--ris-border);
    border-bottom: 1px solid var(--ris-surface);
}

[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    background: var(--ris-surface);
    border: 1px solid var(--ris-border);
    border-radius: 12px;
    padding: 0.35rem;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
input, textarea {
    background: var(--ris-surface-2) !important;
    color: var(--ris-text) !important;
    border-color: var(--ris-border) !important;
}

button[kind="primary"] {
    background: var(--ris-accent) !important;
    color: #0E141B !important;
    border: none !important;
    font-weight: 700 !important;
}

button[kind="secondary"] {
    background: var(--ris-surface-2) !important;
    color: var(--ris-text) !important;
    border: 1px solid var(--ris-border) !important;
}

/* Ocultar chrome de Streamlit */
header[data-testid="stHeader"] {
    display: none !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

[data-testid="stDecoration"] {
    display: none !important;
}

[data-testid="stStatusWidget"] {
    display: none !important;
}

#MainMenu {
    visibility: hidden !important;
}

footer {
    visibility: hidden !important;
}

/* RIS/PACS semantic dashboard classes */

.ris-header {
    padding: 0.10rem 0 0.45rem 0;
}

.ris-title {
    color: var(--ris-text);
    font-size: 2rem;
    font-weight: 760;
    letter-spacing: -0.028em;
    line-height: 1.08;
    margin: 0;
}

.ris-subtitle {
    color: var(--ris-muted);
    font-size: 0.82rem;
    line-height: 1.40;
    margin-top: 0.35rem;
}

.ris-section-title {
    color: var(--ris-text);
    font-size: 1.02rem;
    font-weight: 700;
    margin: 0.10rem 0 0.40rem 0;
}

.ris-caption {
    color: var(--ris-muted);
    font-size: 0.76rem;
    line-height: 1.40;
}

.ris-kpi {
    background: var(--ris-surface);
    border: 1px solid var(--ris-border);
    border-radius: 12px;
    min-height: 96px;
    padding: 0.78rem 0.88rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.16);
}

.ris-kpi-label {
    color: var(--ris-muted);
    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.025em;
    text-transform: uppercase;
}

.ris-kpi-value {
    color: var(--ris-text);
    font-size: 1.52rem;
    font-weight: 760;
    line-height: 1.15;
    margin-top: 0.28rem;
}

.ris-kpi-note {
    color: var(--ris-muted);
    font-size: 0.68rem;
    line-height: 1.30;
    margin-top: 0.22rem;
}

.ris-rule {
    border: 0;
    border-top: 1px solid var(--ris-border);
    margin: 0.55rem 0 0.95rem 0;
}

.ris-analytic-heading {
    color: var(--ris-text);
    font-size: 0.92rem;
    font-weight: 720;
    letter-spacing: 0.018em;
    margin: 0.15rem 0 0.08rem 0;
}

.ris-analytic-description {
    color: var(--ris-muted);
    font-size: 0.75rem;
    line-height: 1.40;
    margin-bottom: 0.55rem;
}

.ris-context-strip {
    background: var(--ris-surface);
    border: 1px solid var(--ris-border);
    border-radius: 9px;
    padding: 0.50rem 0.75rem;
    color: var(--ris-muted);
    font-size: 0.72rem;
    margin-bottom: 0.85rem;
}


/* Streamlit application chrome */

[data-testid="stAppDeployButton"] {
    display: none !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

[data-testid="stHeader"] {
    display: none !important;
}

[data-testid="stDecoration"] {
    display: none !important;
}

#MainMenu {
    visibility: hidden !important;
}

footer {
    visibility: hidden !important;
}


/* Sidebar reversible navigation */

/*
Keep Streamlit's header and toolbar in the DOM because the
collapsed-sidebar expansion control is rendered in this area.
The surfaces remain visually transparent.
*/

header[data-testid="stHeader"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    height: 2.75rem !important;
    min-height: 2.75rem !important;
    background: transparent !important;
    box-shadow: none !important;
    border: 0 !important;
    pointer-events: none !important;
}

[data-testid="stToolbar"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: transparent !important;
    box-shadow: none !important;
    pointer-events: none !important;
}

/*
Hide Streamlit chrome selectively rather than hiding
the complete toolbar/header.
*/

[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
}

/*
Current and compatibility selectors for sidebar controls.
Do not force their native display state; Streamlit decides
which control is appropriate for expanded/collapsed state.
*/

[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    z-index: 100000 !important;
}

/*
Re-open control when the sidebar is collapsed.
*/

[data-testid="stExpandSidebarButton"] {
    position: fixed !important;
    top: 0.55rem !important;
    left: 0.65rem !important;
}

/*
Dark-theme treatment for both directions.
*/

[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button {
    pointer-events: auto !important;
    background: #1B2530 !important;
    color: #F3F6F8 !important;
    border: 1px solid #2B3743 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.22) !important;
    min-width: 34px !important;
    width: 34px !important;
    min-height: 34px !important;
    height: 34px !important;
}

[data-testid="stExpandSidebarButton"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:hover {
    background: #243240 !important;
    border-color: #587487 !important;
}

[data-testid="stExpandSidebarButton"] svg,
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    color: #F3F6F8 !important;
    fill: #F3F6F8 !important;
}

/*
Controls inside the header/toolbar regain pointer events
even though the transparent shell itself ignores clicks.
*/

header[data-testid="stHeader"]
[data-testid="stExpandSidebarButton"],
[data-testid="stToolbar"]
[data-testid="stExpandSidebarButton"] {
    pointer-events: auto !important;
}

</style>
"""


def dashboard_css() -> str:
    return DASHBOARD_CSS
