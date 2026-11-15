"""
VIGIL - AI-Powered Healthcare Safety and Monitoring System
Main Application Entry Point (Streamlit Desktop-First Dashboard)
"""
import os
import streamlit as st

# Configure Streamlit Application Page
st.set_page_config(
    page_title="VIGIL | Healthcare Safety & Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure Environment Variables
os.environ["YOLO_CONFIG_DIR"] = "/tmp/Ultralytics"
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

# Initialize SQLite Database & Seed Data
from backend.database import init_db
init_db()

# Load Custom Healthcare Theme CSS
css_path = os.path.join(os.path.dirname(__file__), "dashboard", "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import Page Views
from dashboard.pages.overview import render_overview
from dashboard.pages.live_monitoring import render_live_monitoring
from dashboard.pages.incident_management import render_incident_management
from dashboard.pages.camera_management import render_camera_management
from dashboard.pages.analytics import render_analytics
from dashboard.pages.settings_page import render_settings
from dashboard.pages.about import render_about

def main():
    # Sidebar Navigation & Product Identity
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0 16px 0; border-bottom: 2px solid #15324B;">
                <div style="font-size: 1.6rem; font-weight: 800; color: #15324B; letter-spacing: 1.5px; display: flex; align-items: center; gap: 8px;">
                    🛡️ VIGIL
                </div>
                <div style="font-size: 0.74rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #2878B5; margin-top: 2px;">
                    Healthcare Safety Intelligence
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # 7 Main Navigation Options
        pages = [
            "Overview",
            "Live Monitoring",
            "Incident Management",
            "Camera Management",
            "Analytics and Reports",
            "Settings",
            "About VIGIL"
        ]

        # Use query parameter or session state for seamless persistence
        if "selected_page" not in st.session_state:
            st.session_state.selected_page = "Overview"

        nav_selection = st.radio(
            "SYSTEM NAVIGATION",
            pages,
            index=pages.index(st.session_state.selected_page) if st.session_state.selected_page in pages else 0,
            label_visibility="collapsed"
        )
        st.session_state.selected_page = nav_selection

        st.markdown("<hr style='margin: 20px 0 12px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

        # System Status Pill in Sidebar
        st.markdown(
            """
            <div style="background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px; padding: 10px; font-size: 0.75rem; color: #334155;">
                <div style="font-weight: 700; color: #15324B; margin-bottom: 4px;">SYSTEM STATUS</div>
                <div>● Engine: <span style="color: #16A34A; font-weight: 600;">Operational</span></div>
                <div>● Database: <span style="color: #2878B5; font-weight: 600;">SQLite Local</span></div>
                <div>● Hardware: <span style="font-weight: 600;">Apple Silicon</span></div>
            </div>
            <div style="margin-top: 14px; font-size: 0.72rem; color: #94A3B8; text-align: center;">
                VIGIL Core v3.0 &bull; Build 2026
            </div>
            """,
            unsafe_allow_html=True
        )

    # Route to Selected Page
    if nav_selection == "Overview":
        render_overview()
    elif nav_selection == "Live Monitoring":
        render_live_monitoring()
    elif nav_selection == "Incident Management":
        render_incident_management()
    elif nav_selection == "Camera Management":
        render_camera_management()
    elif nav_selection == "Analytics and Reports":
        render_analytics()
    elif nav_selection == "Settings":
        render_settings()
    elif nav_selection == "About VIGIL":
        render_about()

if __name__ == "__main__":
    main()
