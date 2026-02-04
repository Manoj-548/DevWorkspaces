"""
Enhanced Comprehensive Dashboard with Real-Time WebSocket Support
Features:
- WebSocket streaming for real-time updates
- Pagination with deduplication
- Overall logs dashboard
- Background task monitoring
- Persistent storage
"""

import streamlit as st
import asyncio
import json
import os
import sys
import time
import psutil
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any, List
import requests

# Add parent directories to path for imports
sys.path.append('/home/manoj/DevWorkspaces')

# Import authentication
from login.login_page import require_auth, show_logout_button

# WebSocket URL
WEBSOCKET_URL = "ws://localhost:8765/ws"
API_BASE_URL = "http://localhost:8765"

# Page configuration
st.set_page_config(
    page_title="DevWorkspaces Real-Time Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== Session State Management ====================

def init_session_state():
    """Initialize session state for real-time data"""
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'system_stats' not in st.session_state:
        st.session_state.system_stats = []
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'processes' not in st.session_state:
        st.session_state.processes = []
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()


# ==================== API Functions ====================

def get_system_stats() -> Dict[str, Any]:
    """Get current system stats via API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/system/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'timestamp': datetime.now().isoformat()
    }


def get_logs(source: str = None, level: str = None, limit: int = 50) -> List[Dict]:
    """Get logs from API"""
    try:
        params = f"?limit={limit}"
        if source:
            params += f"&source={source}"
        if level:
            params += f"&level={level}"
        
        response = requests.get(f"{API_BASE_URL}/api/logs{params}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('logs', [])
    except:
        pass
    return []


def get_processes() -> List[Dict]:
    """Get processes from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/processes", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('processes', [])
    except:
        pass
    return []


def get_github_status() -> Dict:
    """Get GitHub status"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/github/status", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"GitHub API error: {e}")
    return {}


def get_connection_stats() -> Dict:
    """Get WebSocket connection stats"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {}


def get_health() -> Dict:
    """Get API health"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {}


# ==================== UI Components ====================

def render_stats_gauge(value: float, title: str, threshold: float = 80):
    """Render a gauge chart for statistics"""
    color = "green" if value < threshold else ("orange" if value < 90 else "red")
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, threshold], 'color': "lightgreen"},
                {'range': [threshold, 90], 'color': "lightyellow"},
                {'range': [90, 100], 'color': "lightcoral"}
            ]
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=10))
    return fig


def render_paginated_table(data: List[Dict], page: int, items_per_page: int,
                          key: str, columns: List[str]):
    """Render a paginated table"""
    total_pages = max(1, (len(data) + items_per_page - 1) // items_per_page)
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(data))
    page_data = data[start_idx:end_idx]
    
    if page_data:
        df = pd.DataFrame(page_data)
        st.dataframe(df[columns], use_container_width=True)
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("First", key=f"{key}_first"):
            st.session_state.current_page[key] = 0
            st.rerun()
    
    with col2:
        if st.button("Prev", key=f"{key}_prev"):
            if st.session_state.current_page[key] > 0:
                st.session_state.current_page[key] -= 1
                st.rerun()
    
    with col3:
        st.markdown(f"**Page {page + 1} of {total_pages}** (Total: {len(data)} items)")
    
    with col4:
        if st.button("Next", key=f"{key}_next"):
            if page < total_pages - 1:
                st.session_state.current_page[key] += 1
                st.rerun()
    
    with col5:
        if st.button("Last", key=f"{key}_last"):
            st.session_state.current_page[key] = total_pages - 1
            st.rerun()
    
    return page_data


# ==================== Main Dashboard ====================

def main():
    # Initialize session state
    init_session_state()
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = {
            'logs': 0,
            'processes': 0
        }
    
    # Check authentication
    if not require_auth():
        return
    
    # Show logout button
    show_logout_button()
    
    # Title
    st.title("DevWorkspaces Real-Time Dashboard")
    st.markdown("WebSocket-Powered Streaming Dashboard with Pagination and Deduplication")
    
    # Connection status
    status_col1, status_col2, status_col3 = st.columns(3)
    
    # Try to connect to API
    health = get_health()
    st.session_state.connected = health.get('status') == 'healthy'
    
    with status_col1:
        connection_status = "Connected" if st.session_state.connected else "Disconnected"
        st.markdown(f"**API Status:** {connection_status}")
    with status_col2:
        last_update = st.session_state.last_update.strftime("%H:%M:%S")
        st.markdown(f"**Last Update:** {last_update}")
    with status_col3:
        st.markdown(f"**Data Points:** {len(st.session_state.system_stats)}")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select View", [
        "Overview",
        "System Monitor",
        "Processes",
        "GitHub",
        "Logs",
        "Connections"
    ])
    
    # Auto-refresh toggle
    st.sidebar.markdown("---")
    st.session_state.auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 60, 5)
    
    # ==================== Overview Page ====================
    if page == "Overview":
        st.header("Overview")
        
        stats = get_system_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("CPU Usage", f"{stats.get('cpu_percent', 0):.1f}%")
        with col2:
            st.metric("Memory Usage", f"{stats.get('memory_percent', 0):.1f}%")
        with col3:
            st.metric("Disk Usage", f"{stats.get('disk_usage', 0):.1f}%")
        with col4:
            st.metric("Processes", len(st.session_state.processes))
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.plotly_chart(
                render_stats_gauge(stats.get('cpu_percent', 0), "CPU Usage"),
                use_container_width=True
            )
        
        with col_chart2:
            st.plotly_chart(
                render_stats_gauge(stats.get('memory_percent', 0), "Memory Usage"),
                use_container_width=True
            )
        
        st.subheader("System Stats History")
        if st.session_state.system_stats:
            stats_df = pd.DataFrame(st.session_state.system_stats[-50:])
            fig = px.line(
                stats_df,
                x='timestamp',
                y=['cpu_percent', 'memory_percent', 'disk_usage'],
                title="System Metrics Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # ==================== System Monitor Page ====================
    elif page == "System Monitor":
        st.header("System Monitor")
        
        stats = get_system_stats()
        
        st.session_state.system_stats.append(stats)
        st.session_state.system_stats = st.session_state.system_stats[-100:]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.plotly_chart(
                render_stats_gauge(stats.get('cpu_percent', 0), "CPU"),
                use_container_width=True
            )
        with col2:
            st.plotly_chart(
                render_stats_gauge(stats.get('memory_percent', 0), "Memory"),
                use_container_width=True
            )
        with col3:
            st.plotly_chart(
                render_stats_gauge(stats.get('disk_usage', 0), "Disk"),
                use_container_width=True
            )
        
        with st.expander("Detailed System Information"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Memory:**")
                mem = psutil.virtual_memory()
                st.write(f"Total: {mem.total / (1024**3):.2f} GB")
                st.write(f"Used: {mem.used / (1024**3):.2f} GB")
                st.write(f"Available: {mem.available / (1024**3):.2f} GB")
            with col_b:
                disk = psutil.disk_usage('/')
                st.markdown("**Disk:**")
                st.write(f"Total: {disk.total / (1024**3):.2f} GB")
                st.write(f"Used: {disk.used / (1024**3):.2f} GB")
                st.write(f"Free: {disk.free / (1024**3):.2f} GB")
        
        st.subheader("Stats History")
        if st.session_state.system_stats:
            df = pd.DataFrame(st.session_state.system_stats)
            st.dataframe(df, use_container_width=True)
    
    # ==================== Processes Page ====================
    elif page == "Processes":
        st.header("Running Processes")
        
        processes = get_processes()
        
        if processes:
            st.subheader(f"Found {len(processes)} processes")
            
            page_idx = st.session_state.current_page.get('processes', 0)
            render_paginated_table(
                processes, page_idx, 20, 'processes',
                ['pid', 'name', 'cpu_percent', 'memory_percent']
            )
            
            st.subheader("Process Resource Usage")
            if len(processes) <= 50:
                df = pd.DataFrame(processes)
                fig = px.bar(
                    df,
                    x='name',
                    y=['cpu_percent', 'memory_percent'],
                    title="Process Resource Usage",
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No processes found or API unavailable")
    
    # ==================== GitHub Page ====================
    elif page == "GitHub":
        st.header("GitHub Repository")
        
        gh_status = get_github_status()
        
        if gh_status and 'error' not in gh_status:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Stars", gh_status.get('stars', 0))
            with col2:
                st.metric("Forks", gh_status.get('forks', 0))
            with col3:
                st.metric("Open Issues", gh_status.get('open_issues', 0))
            with col4:
                st.metric("Status", "Active")
        else:
            st.warning("GitHub API unavailable or error")
    
    # ==================== Logs Page ====================
    elif page == "Logs":
        st.header("Overall Logs")
        st.markdown("Centralized log aggregation from all sources")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            log_filter = st.selectbox("Filter by Source", ["All", "system_monitor", "github_sync", "log_aggregator"])
        with col2:
            level_filter = st.selectbox("Filter by Level", ["All", "INFO", "WARNING", "ERROR", "DEBUG"])
        with col3:
            st.markdown("")
            refresh_logs = st.button("Refresh Logs")
        
        logs = get_logs(
            source=None if log_filter == "All" else log_filter,
            level=None if level_filter == "All" else level_filter
        )
        
        if logs:
            st.session_state.logs = logs
            
            page_idx = st.session_state.current_page.get('logs', 0)
            render_paginated_table(
                logs, page_idx, 50, 'logs',
                ['timestamp', 'level', 'source', 'message']
            )
            
            st.subheader("Log Level Distribution")
            df = pd.DataFrame(logs)
            level_counts = df['level'].value_counts()
            fig = px.pie(
                values=level_counts.values,
                names=level_counts.index,
                title="Log Levels"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No logs available. Make sure the API is running.")
    
    # ==================== Connections Page ====================
    elif page == "Connections":
        st.header("WebSocket Connections")
        
        conn_stats = get_connection_stats()
        
        if conn_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Connections", conn_stats.get('total_connections', 0))
            with col2:
                st.metric("Active", conn_stats.get('active_connections', 0))
            with col3:
                st.metric("Idle", conn_stats.get('idle_connections', 0))
            with col4:
                channels = conn_stats.get('channels', {})
                st.metric("Channels", len(channels))
            
            st.subheader("Channel Subscriptions")
            channels = conn_stats.get('channels', {})
            if channels:
                df = pd.DataFrame([
                    {'Channel': k, 'Subscribers': v} for k, v in channels.items()
                ])
                st.dataframe(df, use_container_width=True)
        else:
            st.info("WebSocket server unavailable")
    
    # Update timestamp
    st.session_state.last_update = datetime.now()
    
    # Auto-refresh
    if st.session_state.auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
