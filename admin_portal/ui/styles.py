"""
styles.py - Custom CSS Design System and Styling Utilities
Delivers high-contrast, modern, executive aesthetic with full-width layout and pristine sidebar contrast.
"""

import streamlit as st


def apply_custom_styles():
    """Injects custom CSS for sleek design, badges, cards, full-width layout, and high-contrast sidebar."""
    st.markdown(
        """
        <style>
        /* =======================================================
           1. FULL-WIDTH FLUID LAYOUT (ELIMINATE SIDE GUTTERS)
           ======================================================= */
        html, body {
            overflow-x: hidden;
        }

        .main,
        .main .block-container,
        div[data-testid="stAppViewBlockContainer"],
        section[data-testid="stMain"] > div {
            max-width: 100% !important;
            width: 100% !important;
            padding-top: 1.5rem !important;
            padding-left: 2.5rem !important;
            padding-right: 2.5rem !important;
            padding-bottom: 3.5rem !important;
        }

        /* =======================================================
           2. INPUT FIELDS & FORMS (CLEAN CRISP WHITE & LEGIBLE)
           ======================================================= */
        input[type="text"],
        input[type="password"],
        textarea,
        div[data-baseweb="input"],
        div[data-baseweb="base-input"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 8px !important;
            font-size: 1rem !important;
        }

        input[type="text"]:focus,
        input[type="password"]:focus,
        textarea:focus {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
        }

        /* =======================================================
           3. HIGH-CONTRAST EXECUTIVE SIDEBAR THEME
           ======================================================= */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child,
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"],
        section[data-testid="stSidebar"] {
            background-color: #F8FAFC !important;
            background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%) !important;
            border-right: 1.5px solid #E2E8F0 !important;
            box-shadow: 2px 0 16px rgba(0, 0, 0, 0.04) !important;
        }

        /* Profile card in sidebar */
        .sidebar-profile-card {
            background: #FFFFFF !important;
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 14px !important;
            padding: 18px !important;
            margin-bottom: 20px !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
            transition: all 0.25s ease !important;
        }
        .sidebar-profile-card:hover {
            border-color: #93C5FD !important;
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.08) !important;
        }

        .sidebar-label {
            font-size: 0.76rem !important;
            letter-spacing: 0.1em !important;
            color: #64748B !important;
            text-transform: uppercase !important;
            font-weight: 700 !important;
            margin-bottom: 4px !important;
        }
        .sidebar-user-name {
            font-size: 1.18rem !important;
            font-weight: 800 !important;
            color: #0F172A !important;
            letter-spacing: -0.01em !important;
            margin-bottom: 8px !important;
        }
        .sidebar-role-badge {
            display: inline-block !important;
            background: #EEF2FF !important;
            color: #4338CA !important;
            border: 1px solid #C7D2FE !important;
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            padding: 4px 12px !important;
            border-radius: 20px !important;
            letter-spacing: 0.03em !important;
        }

        .sidebar-menu-header {
            font-size: 0.82rem !important;
            letter-spacing: 0.12em !important;
            color: #475569 !important;
            text-transform: uppercase !important;
            font-weight: 800 !important;
            margin: 18px 0 12px 4px !important;
        }

        /* =======================================================
           NAVIGATION MENU ITEMS IN SIDEBAR
           ======================================================= */
        [data-testid="stSidebar"] div[role="radiogroup"] {
            display: flex !important;
            flex-direction: column !important;
            gap: 10px !important;
            width: 100% !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] > label {
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            background: #FFFFFF !important;
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            margin: 0 !important;
            cursor: pointer !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
            transition: all 0.2s ease !important;
        }

        /* Large, crystal-clear, bold navigation text */
        [data-testid="stSidebar"] div[role="radiogroup"] label p {
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            color: #0F172A !important;
            letter-spacing: -0.01em !important;
            margin: 0 0 0 8px !important;
        }

        /* Hover effect */
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: #EFF6FF !important;
            border-color: #93C5FD !important;
            transform: translateX(4px) !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover p {
            color: #1D4ED8 !important;
        }

        /* Active / Selected state */
        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background: #EEF2FF !important;
            border-color: #6366F1 !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2) !important;
            transform: translateX(4px) !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
            color: #4338CA !important;
            font-weight: 800 !important;
        }

        /* Sign Out Button in Sidebar */
        [data-testid="stSidebar"] .stButton > button {
            background: #FEE2E2 !important;
            color: #DC2626 !important;
            border: 1.5px solid #FCA5A5 !important;
            border-radius: 10px !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            padding: 10px 16px !important;
            transition: all 0.2s ease !important;
            margin-top: 14px !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #DC2626 !important;
            color: #FFFFFF !important;
            border-color: #B91C1C !important;
            box-shadow: 0 4px 14px rgba(220, 38, 38, 0.35) !important;
            transform: translateY(-2px) !important;
        }

        /* =======================================================
           4. DATA METRIC CARDS & BADGES
           ======================================================= */
        .metric-card {
            background: #FFFFFF !important;
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 14px !important;
            padding: 20px 24px !important;
            margin-bottom: 16px !important;
            box-shadow: 0 4px 18px -2px rgba(0, 0, 0, 0.05), 0 2px 6px -1px rgba(0, 0, 0, 0.02) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }
        .metric-card:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 10px 24px -4px rgba(0, 0, 0, 0.1) !important;
        }
        .metric-title {
            font-size: 0.88rem !important;
            font-weight: 700 !important;
            color: #475569 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        .metric-value {
            font-size: 2.6rem !important;
            font-weight: 800 !important;
            color: #0F172A !important;
            line-height: 1.1 !important;
            margin: 8px 0 4px 0 !important;
        }
        .metric-subtitle {
            font-size: 0.85rem !important;
            color: #64748B !important;
            font-weight: 500 !important;
        }

        /* Status & Priority Badges */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 14px;
            font-size: 0.8rem;
            font-weight: 600;
            text-align: center;
            letter-spacing: 0.02em;
        }

        /* Custom Table styling */
        div[data-testid="stDataFrame"] {
            border: 1.5px solid #E2E8F0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
