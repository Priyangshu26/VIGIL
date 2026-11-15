"""
VIGIL Dashboard - Analytics & Reports Page
Safety metrics aggregation, camera-wise trend analytics, resolution rates,
and CSV export compliance report generation.
"""
import streamlit as st
import pandas as pd
from backend.incident_manager import incident_manager
from dashboard.components.header import render_header
from dashboard.components.cards import render_kpi_card
from dashboard.components.charts import (
    plot_incident_distribution,
    plot_severity_breakdown,
    plot_daily_trend,
    plot_camera_distribution
)

def render_analytics():
    render_header("Safety Analytics & Reporting", "Incident Trend Analysis, Resolution Metrics & Audit Export")

    # Fetch incident records
    incidents = incident_manager.get_incidents(limit=500)
    stats = incident_manager.get_incident_stats()

    if not incidents:
        st.info("No incident records available for analytics.")
        return

    df = pd.DataFrame(incidents)

    # Top KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Total Logged Events", len(df), "Cumulative facility events", "#15324B")
    with c2:
        resolution_rate = (stats["resolved"] / max(1, stats["total"])) * 100.0
        render_kpi_card("Resolution Rate", f"{resolution_rate:.1f}%", f"{stats['resolved']} of {stats['total']} resolved", "#398568")
    with c3:
        render_kpi_card("Critical Severity", stats["critical"], "Immediate escalation events", "#D9534F")
    with c4:
        render_kpi_card("Pending Action", stats["pending"], "Requires clinical verification", "#E6A23C")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Visual Analytics Grid
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        st.markdown("<div class='section-box'><div class='section-title'>Incident Volume by Category</div>", unsafe_allow_html=True)
        fig_type = plot_incident_distribution(stats["by_type"])
        if fig_type:
            st.plotly_chart(fig_type, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with row1_c2:
        st.markdown("<div class='section-box'><div class='section-title'>Severity Distribution</div>", unsafe_allow_html=True)
        fig_sev = plot_severity_breakdown(incidents)
        if fig_sev:
            st.plotly_chart(fig_sev, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        st.markdown("<div class='section-box'><div class='section-title'>Incident Volume by Camera Location</div>", unsafe_allow_html=True)
        fig_cam = plot_camera_distribution(stats["by_camera"])
        if fig_cam:
            st.plotly_chart(fig_cam, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with row2_c2:
        st.markdown("<div class='section-box'><div class='section-title'>Incident Timeline & Daily Activity Trend</div>", unsafe_allow_html=True)
        fig_trend = plot_daily_trend(incidents)
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # CSV Compliance Export
    st.markdown("<div class='section-box'><div class='section-title'>Clinical Audit & Regulatory Compliance Export</div>", unsafe_allow_html=True)
    st.markdown("Download complete incident audit trail in CSV format for hospital clinical review, safety audits, and risk assessment records.")

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 DOWNLOAD INCIDENT LOGS (CSV)",
        data=csv_data,
        file_name=f"vigil_incident_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        type="primary"
    )
    st.markdown("</div>", unsafe_allow_html=True)
