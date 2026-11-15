"""
VIGIL Dashboard - Live Monitoring Page
Real-time video analytics stream with YOLO pose, fall detection, crowd monitoring,
unattended objects, restricted zones, and live telemetry.
"""
import os
import cv2
import time
import tempfile
import streamlit as st
import numpy as np
from datetime import datetime

from backend.database import SessionLocal
from backend.models import Camera
from backend.incident_manager import incident_manager
from vision.pipeline import VisionPipeline
from dashboard.components.header import render_header
from dashboard.components.cards import render_kpi_card, severity_badge, status_badge

def render_live_monitoring():
    render_header("Live Surveillance Analytics", "Real-Time AI Video Feed & Spatial Behaviour Monitoring")

    # Fetch available cameras from DB
    session = SessionLocal()
    try:
        cameras = session.query(Camera).all()
        cam_options = {f"{c.camera_id} - {c.name}": c for c in cameras}
    finally:
        session.close()

    # Layout: Main Feed Column & Control Sidebar Column
    col_feed, col_ctrl = st.columns([7, 3])

    with col_ctrl:
        st.markdown("<div class='section-box'><div class='section-title'>Feed & Channel Control</div>", unsafe_allow_html=True)
        selected_cam_label = st.selectbox("Select Active Camera", list(cam_options.keys()) if cam_options else ["CAM-01 - Ward 4 Corridor"])
        active_cam = cam_options.get(selected_cam_label) if cam_options else None
        active_cam_id = active_cam.camera_id if active_cam else "CAM-01"

        # Source Selection
        source_type = st.radio(
            "Video Stream Source",
            ["Built-in Webcam (Local)", "Hospital Demo Feed", "Upload Video File"],
            index=0
        )

        uploaded_video_path = None
        if source_type == "Upload Video File":
            uploaded_file = st.file_uploader("Upload MP4 / AVI Video", type=["mp4", "avi", "mov"])
            if uploaded_file is not None:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tfile.write(uploaded_file.read())
                uploaded_video_path = tfile.name

        st.markdown("<hr style='margin: 12px 0;'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Active AI Modules</div>", unsafe_allow_html=True)

        mod_tracking = st.checkbox("Human Detection & Tracking (YOLO)", value=True)
        mod_fall = st.checkbox("Patient Fall Detection (Pose Analysis)", value=True)
        mod_object = st.checkbox("Unattended Object Detection", value=True)
        mod_crowd = st.checkbox("Crowd & Congestion Monitor", value=True)
        mod_zone = st.checkbox("Restricted-Area Intrusion Monitor", value=True)

        crowd_thresh = st.slider("Crowd Limit Threshold", min_value=1, max_value=10, value=active_cam.crowd_threshold if active_cam else 4)

        enabled_mods = []
        if mod_tracking: enabled_mods.append("human_tracking")
        if mod_fall: enabled_mods.append("fall_detection")
        if mod_object: enabled_mods.append("object_detection")
        if mod_crowd: enabled_mods.append("crowd_monitoring")
        if mod_zone: enabled_mods.append("restricted_zone")

        st.markdown("</div>", unsafe_allow_html=True)

    # Initial Active Alert count from database for this camera
    initial_pending_alerts = len(incident_manager.get_incidents(camera_id=active_cam_id, status="Pending"))

    with col_feed:
        # Stream control buttons
        st.markdown("<div class='section-box' style='padding: 14px;'>", unsafe_allow_html=True)
        btn_c1, btn_c2, btn_c3 = st.columns([2, 2, 6])
        with btn_c1:
            start_btn = st.button("▶ START MONITORING", use_container_width=True, type="primary")
        with btn_c2:
            stop_btn = st.button("⏹ STOP STREAM", use_container_width=True)
        with btn_c3:
            st.markdown(
                f"<div style='text-align: right; font-size: 0.85rem; color: #15324B; padding-top: 8px;'>"
                f"Location: <b>{active_cam.location if active_cam else 'Ward 4'}</b> &bull; Resolution: <b>640x480</b>"
                f"</div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Video Frame Container
        frame_placeholder = st.empty()
        status_placeholder = st.empty()
        alert_ticker_placeholder = st.empty()

        # Telemetry metrics cards below video
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            kpi_occ = st.empty()
        with m2:
            kpi_alerts = st.empty()
        with m3:
            kpi_objects = st.empty()
        with m4:
            kpi_fps = st.empty()

        # Initial card states
        kpi_occ.markdown("""<div class="kpi-card"><div class="kpi-title">Occupancy</div><div class="kpi-value">0</div><div class="kpi-subtitle">Visible Persons</div></div>""", unsafe_allow_html=True)
        kpi_alerts.markdown(f"""<div class="kpi-card" style="border-left: 4px solid {'#D9534F' if initial_pending_alerts > 0 else '#398568'};"><div class="kpi-title">Active Alerts</div><div class="kpi-value">{initial_pending_alerts}</div><div class="kpi-subtitle">Pending in Database</div></div>""", unsafe_allow_html=True)
        kpi_objects.markdown("""<div class="kpi-card"><div class="kpi-title">Tracked Items</div><div class="kpi-value">0</div><div class="kpi-subtitle">Bags / Objects</div></div>""", unsafe_allow_html=True)
        kpi_fps.markdown("""<div class="kpi-card"><div class="kpi-title">Inference Rate</div><div class="kpi-value">--</div><div class="kpi-subtitle">Frames Per Sec</div></div>""", unsafe_allow_html=True)

    # Manage stream session state
    if "is_streaming" not in st.session_state:
        st.session_state.is_streaming = False

    if start_btn:
        st.session_state.is_streaming = True
    if stop_btn:
        st.session_state.is_streaming = False

    # Video Processing Loop
    if st.session_state.is_streaming:
        cap = None
        if source_type == "Built-in Webcam (Local)":
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("Cannot access built-in webcam. Please verify macOS camera permissions in System Settings -> Privacy & Security -> Camera.")
                st.session_state.is_streaming = False
                return
        elif source_type == "Hospital Demo Feed":
            demo_path = os.path.join("data", "videos", "demo_hospital_corridor.mp4")
            if not os.path.exists(demo_path):
                from scripts.generate_demo_footage import generate_hospital_corridor_video
                generate_hospital_corridor_video(demo_path)
            cap = cv2.VideoCapture(demo_path)
        elif source_type == "Upload Video File":
            if uploaded_video_path and os.path.exists(uploaded_video_path):
                cap = cv2.VideoCapture(uploaded_video_path)
            else:
                st.warning("Please upload a valid video file first.")
                st.session_state.is_streaming = False
                return

        # Initialize Pipeline
        pipeline = VisionPipeline({
            "camera_id": active_cam.camera_id if active_cam else "CAM-01",
            "name": active_cam.name if active_cam else "Ward 4 Corridor",
            "crowd_threshold": crowd_thresh,
            "restricted_zones": active_cam.restricted_zones if active_cam else [],
            "bed_zones": getattr(active_cam, "bed_zones", []),
            "enabled_modules": enabled_mods
        })

        frame_count = 0
        current_pending_alerts = initial_pending_alerts
        recent_alert_messages = []

        status_placeholder.info("Surveillance feed initialized. Analyzing frames with YOLO...")

        while st.session_state.is_streaming and cap and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                if source_type == "Hospital Demo Feed":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break

            frame_count += 1
            t_frame_start = time.time()

            # Process frame through VIGIL Vision Pipeline
            annotated_frame, metrics, alerts = pipeline.process_frame(frame)

            t_elapsed = time.time() - t_frame_start
            fps = 1.0 / max(0.001, t_elapsed)

            # If alerts were triggered in this frame, update total count & ticker
            if alerts:
                current_pending_alerts += len(alerts)
                now_str = datetime.now().strftime("%H:%M:%S")
                for a in alerts:
                    recent_alert_messages.insert(0, f"[{now_str}] {a}")
                if len(recent_alert_messages) > 3:
                    recent_alert_messages = recent_alert_messages[:3]

            # Render Alert Ticker Banner if there are active recent alerts
            if recent_alert_messages:
                ticker_items = "".join([f"<li style='margin-bottom: 2px;'>{msg}</li>" for msg in recent_alert_messages])
                alert_ticker_placeholder.markdown(
                    f"""
                    <div style="background: #FDE8E8; border: 1px solid #F8B4B4; border-left: 5px solid #D9534F; padding: 10px 14px; border-radius: 4px; margin-bottom: 12px; color: #9B1C1C; font-size: 0.85rem;">
                        <b style="font-size: 0.9rem;">🚨 ACTIVE INCIDENT TICKER:</b>
                        <ul style="margin: 4px 0 0 16px; padding: 0;">{ticker_items}</ul>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Convert BGR to RGB for Streamlit display
            rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)

            # Update Telemetry KPIs
            occ_count = metrics.get("people_count", 0)
            obj_count = metrics.get("objects_tracked", 0)

            kpi_occ.markdown(f"""<div class="kpi-card" style="border-left: 4px solid {'#E6A23C' if occ_count >= crowd_thresh else '#2878B5'};"><div class="kpi-title">Occupancy</div><div class="kpi-value">{occ_count}/{crowd_thresh}</div><div class="kpi-subtitle">Visible Persons</div></div>""", unsafe_allow_html=True)
            kpi_alerts.markdown(f"""<div class="kpi-card" style="border-left: 4px solid {'#D9534F' if current_pending_alerts > 0 else '#398568'};"><div class="kpi-title">Active Alerts</div><div class="kpi-value">{current_pending_alerts}</div><div class="kpi-subtitle">Pending in Database</div></div>""", unsafe_allow_html=True)
            kpi_objects.markdown(f"""<div class="kpi-card"><div class="kpi-title">Tracked Items</div><div class="kpi-value">{obj_count}</div><div class="kpi-subtitle">Bags / Objects</div></div>""", unsafe_allow_html=True)
            kpi_fps.markdown(f"""<div class="kpi-card"><div class="kpi-title">Inference Rate</div><div class="kpi-value">{fps:.1f}</div><div class="kpi-subtitle">Frames Per Sec</div></div>""", unsafe_allow_html=True)

            time.sleep(0.03)

        if cap:
            cap.release()
    else:
        # Show standby placeholder when stream is stopped
        standby_canvas = np.full((400, 640, 3), (25, 35, 45), dtype=np.uint8)
        cv2.putText(standby_canvas, "VIGIL VIDEO FEED STANDBY", (140, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (160, 180, 200), 2, cv2.LINE_AA)
        cv2.putText(standby_canvas, "Click 'START MONITORING' to begin real-time analysis", (130, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 140, 160), 1, cv2.LINE_AA)
        frame_placeholder.image(standby_canvas, channels="RGB", use_container_width=True)
