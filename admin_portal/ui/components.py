"""
components.py - Reusable UI widgets and formatting utilities
"""

from typing import Any
import streamlit as st
from admin_portal.constants import STATUS_STYLES, PRIORITY_STYLES


def render_metric_card(
    title: str,
    value: Any,
    subtitle: str = "",
    accent_color: str = "#2563EB",
    icon: str = "📊",
):
    """Renders a premium executive summary card with distinct icon, top border, and shadow."""
    html = f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 4px solid {accent_color};
                border-radius: 14px; padding: 18px 22px; margin-bottom: 14px;
                box-shadow: 0 4px 16px -2px rgba(0, 0, 0, 0.06), 0 2px 6px -1px rgba(0, 0, 0, 0.04);
                transition: transform 0.2s ease, box-shadow 0.2s ease;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.84rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">{title}</span>
            <span style="font-size: 1.3rem; background: {accent_color}18; width: 36px; height: 36px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center;">{icon}</span>
        </div>
        <div style="font-size: 2.5rem; font-weight: 800; color: #0F172A; line-height: 1.1; margin: 6px 0;">{value}</div>
        {f'<div style="font-size: 0.82rem; color: #94A3B8; font-weight: 500; margin-top: 4px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def get_status_badge_html(status: str) -> str:
    """Returns HTML for status badge."""
    conf = STATUS_STYLES.get(status, {"bg": "#F1F5F9", "text": "#334155", "border": "#CBD5E1", "label": status})
    return (
        f'<span class="badge" style="background-color: {conf["bg"]}; '
        f'color: {conf["text"]}; border: 1px solid {conf["border"]}; font-weight: 600; padding: 4px 12px; border-radius: 14px;">'
        f'{conf["label"]}</span>'
    )


def get_priority_badge_html(priority: str) -> str:
    """Returns HTML for priority badge."""
    conf = PRIORITY_STYLES.get(priority, {"bg": "#F1F5F9", "text": "#475569", "border": "#CBD5E1", "label": priority})
    return (
        f'<span class="badge" style="background-color: {conf["bg"]}; '
        f'color: {conf["text"]}; border: 1px solid {conf["border"]}; font-weight: 600; padding: 4px 12px; border-radius: 14px;">'
        f'{conf["label"]}</span>'
    )


def render_header_banner(title: str, subtitle: str):
    """Renders an executive header banner spanning full width with crisp dark styling."""
    html = f"""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
                color: #FFFFFF; border-radius: 16px; padding: 26px 32px; margin-bottom: 24px;
                box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25); border: 1px solid rgba(255, 255, 255, 0.08);">
        <h1 style="color: #FFFFFF !important; margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em;">{title}</h1>
        <p style="color: #94A3B8 !important; margin: 8px 0 0 0; font-size: 1.05rem; font-weight: 500;">{subtitle}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(title: str, description: str):
    """Displays a clean empty-state placeholder."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 48px 24px; background: #FFFFFF; border-radius: 12px; border: 1px dashed #CBD5E1; margin: 20px 0;">
            <div style="font-size: 2.4rem; margin-bottom: 8px;">📋</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #1E293B;">{title}</div>
            <div style="font-size: 0.92rem; color: #64748B; margin-top: 6px;">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
