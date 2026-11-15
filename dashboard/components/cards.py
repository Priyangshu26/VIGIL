"""
VIGIL Cards & Badges Component
"""
from typing import Any
import streamlit as st

def render_kpi_card(title: str, value: Any, subtitle: str = "", border_color: str = "#2878B5"):
    html = f"""
    <div class="kpi-card" style="border-left: 4px solid {border_color};">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def severity_badge(severity: str) -> str:
    s = (severity or "Low").capitalize()
    cls = f"badge-{s.lower()}"
    return f'<span class="badge {cls}">{s}</span>'

def status_badge(status: str) -> str:
    st_val = (status or "Pending").capitalize()
    cls = f"badge-{st_val.lower().replace(' ', '-')}"
    return f'<span class="badge {cls}">{st_val}</span>'
