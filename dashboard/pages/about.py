"""
VIGIL Dashboard - About Page
Project identity, architectural overview, ethical boundaries, and team details.
"""
import streamlit as st
from dashboard.components.header import render_header

def render_about():
    render_header("About VIGIL System", "AI-Powered Healthcare Safety and Monitoring System")

    st.markdown(
        """
        <div class="section-box">
            <div class="section-title">Executive Project Identity</div>
            <p style="font-size: 0.92rem; line-height: 1.6; color: #263746;">
                <b>VIGIL</b> is an AI-powered computer vision analytics platform engineered to enhance patient safety,
                accelerate incident intervention, and reduce dependence on continuous manual surveillance in healthcare facilities.
                VIGIL is designed as a software intelligence layer that integrates with existing hospital CCTV infrastructure,
                processing feeds locally on modern hardware to identify critical safety events in real time.
            </p>
        </div>

        <div class="section-box">
            <div class="section-title">Core AI Capabilities & Modular Architecture</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <div style="background: #FAFCFE; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px;">
                    <b style="color: #15324B;">1. Human Detection & Tracking</b>
                    <p style="font-size: 0.85rem; color: #4A5B6D; margin-top: 6px;">
                        Spatial-temporal tracking powered by YOLO and robust Centroid/IoU association to track patient
                        and visitor movements without biometric identification.
                    </p>
                </div>
                <div style="background: #FAFCFE; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px;">
                    <b style="color: #D9534F;">2. Patient Fall Posture Analysis</b>
                    <p style="font-size: 0.85rem; color: #4A5B6D; margin-top: 6px;">
                        Skeletal joint keypoint analysis (17 COCO joints) tracking torso angle and aspect ratio to detect
                        sudden collapses and prone floor postures while differentiating normal sitting or bending.
                    </p>
                </div>
                <div style="background: #FAFCFE; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px;">
                    <b style="color: #2878B5;">3. Unattended Object Detection</b>
                    <p style="font-size: 0.85rem; color: #4A5B6D; margin-top: 6px;">
                        Detects stationary bags, backpacks, and luggage; continuously verifies human proximity radius
                        to flag unattended items requiring staff verification.
                    </p>
                </div>
                <div style="background: #FAFCFE; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px;">
                    <b style="color: #E6A23C;">4. Crowd & Congestion Monitoring</b>
                    <p style="font-size: 0.85rem; color: #4A5B6D; margin-top: 6px;">
                        Live occupancy monitoring against per-camera capacity limits to prevent bottlenecks in ER entrances
                        and waiting halls with automated cooldown alerts.
                    </p>
                </div>
                <div style="background: #FAFCFE; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px;">
                    <b style="color: #795290;">5. Restricted-Area Perimeter Monitoring</b>
                    <p style="font-size: 0.85rem; color: #4A5B6D; margin-top: 6px;">
                        Configurable rectangular safety zones (medicine carts, ICU rooms) with ground contact foot-level
                        intrusion checks and staff verification logging.
                    </p>
                </div>
                <div style="background: #FAFCFE; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px;">
                    <b style="color: #D9534F;">6. Context-Aware Incident Correlation</b>
                    <p style="font-size: 0.85rem; color: #4A5B6D; margin-top: 6px;">
                        Correlates temporally coupled events (e.g. Fall Incident + Subsequent Crowd Surge) into a single
                        high-priority clinical emergency notification.
                    </p>
                </div>
            </div>
        </div>

        <div class="section-box">
            <div class="section-title">Ethical Safeguards & Privacy by Design</div>
            <ul style="font-size: 0.88rem; line-height: 1.8; color: #263746; padding-left: 20px;">
                <li><b>No Facial Recognition:</b> VIGIL strictly tracks human figures using anonymous skeletal posture and bounding boxes. No biometric profiles or facial identification models are utilized.</li>
                <li><b>Local On-Device Processing:</b> Video feeds are processed entirely in-memory on local facility servers. No video streams or patient footage are transmitted to external third-party cloud services.</li>
                <li><b>Decision-Support Role:</b> VIGIL acts as a clinical decision-support tool to reduce operator fatigue. It is not an autonomous diagnostic medical device or a replacement for clinical staff.</li>
                <li><b>Human-in-the-Loop Verification:</b> Every flagged incident is presented to staff for human verification (Pending &rarr; Verified / False Alert / Resolved).</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
