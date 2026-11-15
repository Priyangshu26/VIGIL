"""
VIGIL Analytics Charts Component
Customized Plotly charts using the healthcare visual identity palette with high-contrast text.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

PALETTE = {
    "Critical": "#D9534F",
    "High": "#E6A23C",
    "Medium": "#2878B5",
    "Low": "#6C7A89",
    "navy": "#15324B",
    "blue": "#2878B5",
    "green": "#398568"
}

def plot_incident_distribution(by_type: Dict[str, int]):
    """Horizontal bar chart showing incident counts by type."""
    if not by_type:
        return None

    df = pd.DataFrame(list(by_type.items()), columns=["Incident Type", "Count"]).sort_values("Count", ascending=True)
    fig = px.bar(
        df,
        x="Count",
        y="Incident Type",
        orientation="h",
        color_discrete_sequence=["#2878B5"]
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=12, color="#15324B"),
        xaxis=dict(
            showgrid=True,
            gridcolor="#EDF2F7",
            dtick=1,
            tickfont=dict(color="#15324B", size=12, family="Inter, sans-serif"),
            title=dict(text="Count", font=dict(color="#15324B", size=12))
        ),
        yaxis=dict(
            title="",
            tickfont=dict(color="#15324B", size=12, family="Inter, sans-serif")
        )
    )
    return fig

def plot_severity_breakdown(incidents: list):
    """Donut chart showing severity distribution."""
    if not incidents:
        return None

    df = pd.DataFrame(incidents)
    sev_counts = df["severity"].value_counts().reset_index()
    sev_counts.columns = ["Severity", "Count"]

    color_map = {
        "Critical": "#D9534F",
        "High": "#E6A23C",
        "Medium": "#2878B5",
        "Low": "#6C7A89"
    }

    fig = px.pie(
        sev_counts,
        values="Count",
        names="Severity",
        hole=0.55,
        color="Severity",
        color_discrete_map=color_map
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=12, color="#15324B"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(color="#15324B", size=12)
        )
    )
    return fig

def plot_daily_trend(incidents: list):
    """Line chart showing daily incident trend."""
    if not incidents:
        return None

    df = pd.DataFrame(incidents)
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    daily = df.groupby("date").size().reset_index(name="Incidents")

    fig = px.line(
        daily,
        x="date",
        y="Incidents",
        markers=True,
        color_discrete_sequence=["#15324B"]
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=12, color="#15324B"),
        xaxis=dict(
            showgrid=True,
            gridcolor="#EDF2F7",
            title=dict(text="Date", font=dict(color="#15324B", size=12)),
            tickfont=dict(color="#15324B", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#EDF2F7",
            title=dict(text="Incident Count", font=dict(color="#15324B", size=12)),
            tickfont=dict(color="#15324B", size=11)
        )
    )
    return fig

def plot_camera_distribution(by_camera: Dict[str, int]):
    """Bar chart of incidents per camera."""
    if not by_camera:
        return None

    df = pd.DataFrame(list(by_camera.items()), columns=["Camera", "Incidents"])
    fig = px.bar(
        df,
        x="Camera",
        y="Incidents",
        color_discrete_sequence=["#15324B"]
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=12, color="#15324B"),
        xaxis=dict(
            title="",
            tickfont=dict(color="#15324B", size=12)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#EDF2F7",
            tickfont=dict(color="#15324B", size=11)
        )
    )
    return fig
