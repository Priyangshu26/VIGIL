"""
VIGIL Dashboard - Overview Page
Executive monitoring summary and incident health metrics.
"""
import streamlit as st
from backend.incident_manager import incident_manager
from backend.database import SessionLocal
from backend.models import Camera, Incident
from dashboard.components.header import render_header
from dashboard.components.cards import render_kpi_card, severity_badge, status_badge
from dashboard.components.charts import plot_incident_distribution, plot_severity_breakdown, plot_daily_trend

def render_overview():
    render_header("Executive Overview", "Real-Time Healthcare Facility Safety Telemetry")

    # 1. Fetch live metrics from Database
    session = SessionLocal()
    try:
        total_cameras = session.query(Camera).count()
        active_cameras = session.query(Camera).filter(Camera.status == "Active").count()
    finally:
        session.close()

    stats = incident_manager.get_incident_stats()
    all_incidents = incident_manager.get_incidents(limit=100)

    # 2. KPI Metrics Grid
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card("Connected Cameras", f"{active_cameras}/{total_cameras}", "Active surveillance channels", "#2878B5")
    with c2:
        render_kpi_card("Total Incidents", stats["total"], "Persisted across facility", "#15324B")
    with c3:
        render_kpi_card("Critical Alerts", stats["critical"], "Requires immediate attention", "#D9534F")
    with c4:
        render_kpi_card("Pending Review", stats["pending"], "Awaiting clinical verification", "#E6A23C")
    with c5:
        render_kpi_card("Resolved Incidents", stats["resolved"], "Action completed & verified", "#398568")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Visual Charts Grid
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("<div class='section-box'><div class='section-title'>Incident Distribution by Category</div>", unsafe_allow_html=True)
        fig_dist = plot_incident_distribution(stats["by_type"])
        if fig_dist:
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No incident records available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chart2:
        st.markdown("<div class='section-box'><div class='section-title'>Incident Severity Breakdown</div>", unsafe_allow_html=True)
        fig_sev = plot_severity_breakdown(all_incidents)
        if fig_sev:
            st.plotly_chart(fig_sev, use_container_width=True)
        else:
            st.info("No incident records available.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. Recent Facility Activity Stream
    st.markdown("<div class='section-box'><div class='section-title'>Recent Safety Incidents & Alerts</div>", unsafe_allow_html=True)
    recent = all_incidents[:6]
    if recent:
        for inc in recent:
            sev_html = severity_badge(inc["severity"])
            st_html = status_badge(inc["status"])
            st.markdown(
                f"""
                <div style="background: #FAFCFE; border: 1px solid #E5EDF4; border-left: 4px solid {'#D9534F' if inc['severity'] == 'Critical' else '#2878B5'}; padding: 12px 16px; border-radius: 4px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: #15324B; font-size: 0.92rem;">{inc['incident_id']} &bull; {inc['event_type']}</span>
                        <span>{sev_html} &nbsp; {st_html}</span>
                    </div>
                    <div style="font-size: 0.84rem; color: #4A5B6D; margin-bottom: 4px;">{inc['description']}</div>
                    <div style="font-size: 0.76rem; color: #8A99A8;">
                        Camera: <b>{inc['camera_name']}</b> ({inc['camera_id']}) &bull; Timestamp: {inc['timestamp']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No recent incidents recorded.")
    st.markdown("</div>", unsafe_allow_html=True)
