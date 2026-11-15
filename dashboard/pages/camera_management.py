"""
VIGIL Dashboard - Camera Management Page
Surveillance node topology, stream source binding, restricted zone geometry definition,
and per-camera module configuration.
"""
import json
import streamlit as st
import pandas as pd
from backend.database import SessionLocal
from backend.models import Camera
from dashboard.components.header import render_header

def render_camera_management():
    render_header("Camera Channel Management", "Surveillance Node Configuration, Restricted Zones & Stream Sources")

    session = SessionLocal()
    try:
        cameras = session.query(Camera).all()
        cam_dicts = [c.to_dict() for c in cameras]
    finally:
        session.close()

    # Layout: Top Table of Configured Cameras, Bottom Form to Add/Configure
    st.markdown("<div class='section-box'><div class='section-title'>Active Surveillance Channels</div>", unsafe_allow_html=True)
    if cam_dicts:
        df_cams = pd.DataFrame([
            {
                "Camera ID": c["camera_id"],
                "Name": c["name"],
                "Location": c["location"],
                "Source": c["source"],
                "Status": c["status"],
                "Crowd Limit": c["crowd_threshold"],
                "Restricted Zones": len(c["restricted_zones"]),
                "Active Modules": ", ".join(c["enabled_modules"])
            }
            for c in cam_dicts
        ])
        st.dataframe(df_cams, use_container_width=True, hide_index=True)
    else:
        st.info("No cameras configured.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Add / Edit Camera Section
    col_new, col_zone = st.columns([5, 5])

    with col_new:
        st.markdown("<div class='section-box'><div class='section-title'>Register New Surveillance Channel</div>", unsafe_allow_html=True)
        with st.form("add_camera_form"):
            c_id = st.text_input("Camera ID", value=f"CAM-0{len(cam_dicts)+1:02d}", help="Unique identifier, e.g. CAM-04")
            c_name = st.text_input("Camera Name", placeholder="e.g. Pediatric Ward Corridor")
            c_loc = st.text_input("Facility Location", placeholder="e.g. Building C - Level 1")
            c_source_type = st.selectbox("Stream Protocol / Source", ["Local Webcam (Index 0)", "RTSP Network Stream", "Video File Path", "Demo Video Simulation"])

            c_source = "webcam_0"
            if c_source_type == "RTSP Network Stream":
                c_source = st.text_input("RTSP Stream URL", placeholder="rtsp://admin:pass@192.168.1.50:554/live")
            elif c_source_type == "Video File Path":
                c_source = st.text_input("Absolute File Path", placeholder="/path/to/cctv_recording.mp4")
            elif c_source_type == "Demo Video Simulation":
                c_source = "data/videos/demo_hospital_corridor.mp4"

            c_crowd = st.number_input("Crowd Limit Threshold", min_value=1, max_value=25, value=4)
            c_status = st.selectbox("Initial Status", ["Active", "Inactive"])

            submit_add = st.form_submit_button("Register Camera", type="primary")

            if submit_add:
                if not c_name or not c_loc:
                    st.error("Camera Name and Location are required.")
                else:
                    db = SessionLocal()
                    try:
                        new_cam = Camera(
                            camera_id=c_id,
                            name=c_name,
                            location=c_loc,
                            source=c_source or "webcam_0",
                            status=c_status,
                            crowd_threshold=int(c_crowd),
                            restricted_zones_json="[]",
                            enabled_modules_json=json.dumps(["human_tracking", "fall_detection", "object_detection", "crowd_monitoring", "restricted_zone"])
                        )
                        db.add(new_cam)
                        db.commit()
                        st.success(f"Camera '{c_name}' ({c_id}) added successfully.")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Failed to add camera: {e}")
                    finally:
                        db.close()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_zone:
        st.markdown("<div class='section-box'><div class='section-title'>Configure Restricted Zones</div>", unsafe_allow_html=True)
        cam_select = st.selectbox("Select Target Camera", [f"{c['camera_id']} - {c['name']}" for c in cam_dicts])
        sel_cid = cam_select.split(" - ")[0] if cam_select else None

        target_cam = next((c for c in cam_dicts if c["camera_id"] == sel_cid), None)
        if target_cam:
            st.markdown(f"<b>Current Zones ({len(target_cam['restricted_zones'])}):</b>", unsafe_allow_html=True)
            for z in target_cam["restricted_zones"]:
                st.code(f"Zone '{z.get('name')}': Bounding Box [{z.get('x1')}, {z.get('y1')}, {z.get('x2')}, {z.get('y2')}]", language="json")

            with st.form("add_zone_form"):
                z_name = st.text_input("New Zone Label", placeholder="e.g. ICU Restricted Medicine Counter")
                st.markdown("<small>Normalized Bounding Box Coordinates (0.0 to 1.0):</small>", unsafe_allow_html=True)
                zc1, zc2 = st.columns(2)
                with zc1:
                    zx1 = st.number_input("X1 (Left)", min_value=0.0, max_value=1.0, value=0.05, step=0.05)
                    zy1 = st.number_input("Y1 (Top)", min_value=0.0, max_value=1.0, value=0.10, step=0.05)
                with zc2:
                    zx2 = st.number_input("X2 (Right)", min_value=0.0, max_value=1.0, value=0.40, step=0.05)
                    zy2 = st.number_input("Y2 (Bottom)", min_value=0.0, max_value=1.0, value=0.70, step=0.05)

                zone_submit = st.form_submit_button("Add Zone to Camera")
                if zone_submit:
                    if not z_name:
                        st.error("Zone label is required.")
                    else:
                        db = SessionLocal()
                        try:
                            cam_obj = db.query(Camera).filter(Camera.camera_id == sel_cid).first()
                            if cam_obj:
                                current_zones = cam_obj.restricted_zones
                                current_zones.append({
                                    "name": z_name,
                                    "x1": round(zx1, 2),
                                    "y1": round(zy1, 2),
                                    "x2": round(zx2, 2),
                                    "y2": round(zy2, 2)
                                })
                                cam_obj.restricted_zones = current_zones
                                db.commit()
                                st.success(f"Added zone '{z_name}' to {cam_obj.name}.")
                                st.rerun()
                        finally:
                            db.close()
        st.markdown("</div>", unsafe_allow_html=True)
