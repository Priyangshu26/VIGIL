"""
VIGIL Header Component
"""
import streamlit as st

def render_header(title: str, subtitle: str = "AI-Powered Healthcare Safety and Monitoring System"):
    st.markdown(
        f"""
        <div class="vigil-header">
            <div>
                <h1>VIGIL &mdash; {title}</h1>
                <p>{subtitle}</p>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(40, 120, 181, 0.25); border: 1px solid #2878B5; padding: 4px 10px; border-radius: 4px; font-size: 0.78rem; font-weight: 600; color: #FFFFFF;">
                    ● SYSTEM ACTIVE &bull; LOCAL INFERENCE
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
