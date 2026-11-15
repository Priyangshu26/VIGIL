"""
VIGIL Dashboard - Incident Management Page
Comprehensive audit table, severity filtering, status verification workflows,
and high-resolution snapshot forensic inspection.
"""
import os
import streamlit as st
import pandas as pd
from PIL import Image

from backend.incident_manager import incident_manager
from backend.database import SessionLocal
from backend.models import Camera
from dashboard.components.header import render_header
from dashboard.components.cards import severity_badge, status_badge

def render_incident_management():
    render_header("Incident Management & Audit", "Centralised Healthcare Safety Event Log & Human Verification")

    # Fetch camera list for filter
    session = SessionLocal()
    try:
        cams = session.query(Camera).all()
        cam_ids = ["All"] + [c.camera_id for c in cams]
    finally:
        session.close()

    # Filter Controls
    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([3, 3, 3, 2])
    with f1:
        sel_camera = st.selectbox("Filter by Camera", cam_ids)
    with f2:
        sel_severity = st.selectbox("Filter by Severity", ["All", "Critical", "High", "Medium", "Low"])
    with f3:
        sel_status = st.selectbox("Filter by Status", ["All", "Pending", "Verified", "Resolved", "False Alert"])
    with f4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        refresh_btn = st.button("🔄 Refresh Data", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Fetch filtered incidents
    incidents = incident_manager.get_incidents(
        camera_id=sel_camera if sel_camera != "All" else None,
        severity=sel_severity if sel_severity != "All" else None,
        status=sel_status if sel_status != "All" else None,
        limit=200
    )

    if not incidents:
        st.info("No incidents match the selected filter criteria.")
        return

    # Two column layout: Left for Incident Table & Selection, Right for Incident Forensic Inspector
    col_table, col_detail = st.columns([6, 4])

    with col_table:
        st.markdown(f"<div class='section-box'><div class='section-title'>Logged Incidents ({len(incidents)} Records)</div>", unsafe_allow_html=True)

        # Build clean display table
        table_rows = []
        for inc in incidents:
            table_rows.append({
                "Incident ID": inc["incident_id"],
                "Timestamp": inc["timestamp"],
                "Camera": f"{inc['camera_name']} ({inc['camera_id']})",
                "Event Type": inc["event_type"],
                "Severity": inc["severity"],
                "Status": inc["status"]
            })

        df_display = pd.DataFrame(table_rows)
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Incident ID": st.column_config.TextColumn("Incident ID", width="medium"),
                "Timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
                "Severity": st.column_config.TextColumn("Severity", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Incident Selection for Forensic Inspection
    incident_options = {f"{i['incident_id']} - {i['event_type']} ({i['timestamp']})": i for i in incidents}
    
    with col_detail:
        st.markdown("<div class='section-box'><div class='section-title'>Incident Detail & Evidence Inspector</div>", unsafe_allow_html=True)
        selected_key = st.selectbox("Inspect Incident", list(incident_options.keys()))
        selected_inc = incident_options.get(selected_key)

        if selected_inc:
            s_badge = severity_badge(selected_inc["severity"])
            st_badge = status_badge(selected_inc["status"])

            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 1.05rem; font-weight: 700; color: #15324B;">{selected_inc['incident_id']}</span>
                        <span>{s_badge} &nbsp; {st_badge}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; margin-bottom: 6px;"><b>Camera:</b> {selected_inc['camera_name']} ({selected_inc['camera_id']})</div>
                    <div style="font-size: 0.85rem; color: #475569; margin-bottom: 6px;"><b>Timestamp:</b> {selected_inc['timestamp']}</div>
                    <div style="font-size: 0.85rem; color: #1E293B; background: #FFFFFF; border: 1px solid #E2E8F0; padding: 8px 10px; border-radius: 4px; margin-top: 8px;">
                        <b>Description:</b><br>{selected_inc['description']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Snapshot Forensic Evidence
            snap_path = selected_inc.get("snapshot_path")
            st.markdown("<b>Captured Snapshot Evidence:</b>", unsafe_allow_html=True)
            if snap_path and os.path.exists(snap_path):
                img = Image.open(snap_path)
                st.image(img, caption=f"Evidence Snapshot - {selected_inc['incident_id']}", use_container_width=True)
            else:
                # Fallback evidence preview placeholder
                st.markdown(
                    f"""
                    <div style="background: #0F172A; border-radius: 6px; padding: 24px 16px; text-align: center; color: #94A3B8; font-size: 0.85rem;">
                        <div style="font-size: 1.1rem; color: #E2E8F0; margin-bottom: 6px;">[EVIDENCE RECORD LOGGED]</div>
                        {selected_inc['event_type']} &bull; {selected_inc['timestamp']}<br>
                        Location: {selected_inc['camera_name']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Verification Workflow & Action Form
            st.markdown("<hr style='margin: 14px 0;'>", unsafe_allow_html=True)
            st.markdown("<b>Update Verification Status:</b>", unsafe_allow_html=True)
            with st.form(key=f"verify_form_{selected_inc['incident_id']}"):
                current_st = selected_inc["status"]
                st_index = ["Pending", "Verified", "Resolved", "False Alert"].index(current_st) if current_st in ["Pending", "Verified", "Resolved", "False Alert"] else 0
                new_status = st.selectbox("Action / Resolution", ["Pending", "Verified", "Resolved", "False Alert"], index=st_index)
                notes = st.text_area("Clinical Verification Notes", value=selected_inc.get("verification_notes") or "", placeholder="Enter clinical follow-up actions, nursing staff dispatched, or resolution details...")
                submit_btn = st.form_submit_button("Submit Status Update", type="primary")

                if submit_btn:
                    ok = incident_manager.update_incident_status(selected_inc["incident_id"], new_status, notes)
                    if ok:
                        st.success(f"Incident {selected_inc['incident_id']} updated to '{new_status}' successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to update incident status.")

        st.markdown("</div>", unsafe_allow_html=True)
