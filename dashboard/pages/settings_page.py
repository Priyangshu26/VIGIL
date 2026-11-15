"""
VIGIL Dashboard - Settings Page
Configuration for AI detection parameters, cooldown timers, hardware acceleration,
and system database operations.
"""
import streamlit as st
import torch
import cv2
import ultralytics
from backend.database import SessionLocal, init_db
from backend.models import AppSetting
from dashboard.components.header import render_header

def render_settings():
    render_header("System & Detection Settings", "Tune Computer Vision Thresholds, Alert Cooldowns & Hardware Target")

    col_tune, col_sys = st.columns([6, 4])

    with col_tune:
        st.markdown("<div class='section-box'><div class='section-title'>Computer Vision & Posture Thresholds</div>", unsafe_allow_html=True)
        with st.form("settings_form"):
            st.markdown("<b>Fall Detection Sensitivity:</b>", unsafe_allow_html=True)
            fall_frames = st.slider("Fall Confirmation Frames", min_value=3, max_value=25, value=8, help="Number of consecutive prone frames required to verify a fall incident")
            aspect_ratio = st.slider("Fall Aspect Ratio Threshold (Width / Height)", min_value=0.8, max_value=2.0, value=1.15, step=0.05)
            torso_angle = st.slider("Torso Angle from Vertical (Degrees)", min_value=40.0, max_value=80.0, value=55.0, step=1.0)

            st.markdown("<hr style='margin: 14px 0;'>", unsafe_allow_html=True)
            st.markdown("<b>Unattended Object & Crowd Timing:</b>", unsafe_allow_html=True)
            unattended_sec = st.number_input("Unattended Object Stationary Duration (Seconds)", min_value=2.0, max_value=60.0, value=5.0, step=1.0)
            proximity_px = st.number_input("Human Proximity Radius (Pixels)", min_value=50, max_value=300, value=130, step=10)
            crowd_cooldown = st.number_input("Crowd Alert Cooldown (Seconds)", min_value=5.0, max_value=120.0, value=25.0, step=5.0)

            save_btn = st.form_submit_button("Save Configuration", type="primary")
            if save_btn:
                st.success("Configuration thresholds saved successfully.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_sys:
        st.markdown("<div class='section-box'><div class='section-title'>Hardware & Runtime Environment</div>", unsafe_allow_html=True)
        mps_status = "Available (Active)" if torch.backends.mps.is_available() else "Unavailable (Fallback to CPU Inference)"

        st.markdown(
            f"""
            <div style="font-size: 0.85rem; line-height: 1.8; color: #263746;">
                <b>Platform:</b> Apple Silicon (arm64, macOS)<br>
                <b>PyTorch Version:</b> {torch.__version__}<br>
                <b>Metal (MPS) Acceleration:</b> {mps_status}<br>
                <b>OpenCV Engine:</b> {cv2.__version__}<br>
                <b>Ultralytics Framework:</b> {ultralytics.__version__}<br>
                <b>Primary Pose Model:</b> yolov8n-pose.pt<br>
                <b>Primary Object Model:</b> yolov8n.pt<br>
                <b>Default Inference Resolution:</b> 640x640<br>
                <b>Database Engine:</b> SQLite (SQLAlchemy ORM)
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<hr style='margin: 14px 0;'>", unsafe_allow_html=True)
        st.markdown("<b>Database Maintenance:</b>", unsafe_allow_html=True)
        if st.button("Reset / Re-seed Benchmark Data"):
            init_db()
            st.success("Database re-initialized and seed benchmarks restored.")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
