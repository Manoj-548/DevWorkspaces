import streamlit as st
import os
import sys
import time
import psutil
import subprocess
import requests
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import gitlab
import git
from atlassian import Bitbucket
import streamlit_authenticator as stauth
from typing import Dict, Any, List

sys.path.append('../..')
sys.path.append('/home/manoj/DevWorkspaces/services')
from login.login_page import require_auth, show_logout_button
from network_manager.network_manager import (
    NetworkManager,
    get_network_status,
    test_network_speed,
    switch_to_best_interface,
    create_port_forward,
    close_port_forward
)

# WebSocket URL for real-time dashboard
WEBSOCKET_URL = "ws://localhost:8765/ws"
API_BASE_URL = "http://localhost:8765"

WORKSPACE_ROOT = Path("/home/manoj/DevWorkspaces")
ARCHIVE_ROOT = Path("/mnt/d/ArchiveWorkspaces")
GITHUB_REPO = "Manoj-548/DevWorkspaces"
HF_USER = "Manoj548"
GITLAB_URL = "https://gitlab.com"
GITLAB_PROJECT_ID = "your_project_id"
BITBUCKET_WORKSPACE = "your_workspace"
BITBUCKET_REPO = "your_repo"
UBUNTU_LOGS_DIR = Path("/var/log")
MAX_DISK_USAGE_PERCENT = 80
BACKUP_DIR = Path("/backups")
BACKUP_RETENTION_DAYS = 30
CRITICAL_THRESHOLD = 90
WARNING_THRESHOLD = 80

st.set_page_config(
    page_title="DevWorkspaces Comprehensive Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=30 * 1000, key="data_refresh")

def get_system_stats():
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'network_connections': len(psutil.net_connections()),
        'timestamp': datetime.now()
    }

def get_workspace_projects():
    projects = {}
    projects_dir = WORKSPACE_ROOT / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                projects[project_dir.name] = {
                    'path': str(project_dir),
                    'type': 'current',
                    'last_modified': datetime.fromtimestamp(project_dir.stat().st_mtime),
                    'size': sum(f.stat().st_size for f in project_dir.rglob('*') if f.is_file())
                }
    return projects

def get_archived_projects():
    archived = {}
    if ARCHIVE_ROOT.exists():
        for root_dir in ARCHIVE_ROOT.iterdir():
            if root_dir.is_dir():
                archived[root_dir.name] = {
                    'path': str(root_dir),
                    'type': 'archived',
                    'last_modified': datetime.fromtimestamp(root_dir.stat().st_mtime),
                    'size': sum(f.stat().st_size for f in root_dir.rglob('*') if f.is_file())
                }
    return archived

def get_github_status():
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}"
        headers = {}
        github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            repo_data = response.json()
            return {
                'name': repo_data.get('name'),
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'open_issues': repo_data.get('open_issues_count', 0),
                'last_updated': repo_data.get('updated_at'),
                'status': 'active'
            }
        elif response.status_code == 403:
            return {'status': 'rate_limited', 'message': 'GitHub API rate limit exceeded.'}
        else:
            return {'status': 'error', 'message': f'API Error: {response.status_code}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_github_workflows():
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
        headers = {}
        github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            runs = data.get('workflow_runs', [])[:10]
            return {
                'total_runs': len(runs),
                'successful': sum(1 for r in runs if r.get('conclusion') == 'success'),
                'failed': sum(1 for r in runs if r.get('conclusion') == 'failure'),
                'in_progress': sum(1 for r in runs if r.get('status') == 'in_progress'),
                'recent_runs': runs[:5]
            }
        return {'status': 'error', 'message': f'API Error: {response.status_code}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_huggingface_status():
    try:
        api_url = f"https://huggingface.co/api/users/{HF_USER}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            return {
                'name': user_data.get('name'),
                'username': user_data.get('username'),
                'num_models': user_data.get('numModels', 0),
                'num_datasets': user_data.get('numDatasets', 0),
                'num_spaces': user_data.get('numSpaces', 0),
                'status': 'active'
            }
        return {'status': 'error', 'message': f'API Error: {response.status_code}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_running_processes():
    workspace_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
        try:
            if 'python' in proc.info['name'].lower() or 'streamlit' in proc.info['name'].lower():
                cmdline = proc.cmdline()
                if any('DevWorkspaces' in str(cmd) for cmd in cmdline):
                    workspace_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent'],
                        'started': datetime.fromtimestamp(proc.info['create_time'])
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return workspace_processes

def get_storage_info():
    try:
        disk = psutil.disk_usage('/')
        logs_size = sum(f.stat().st_size for f in UBUNTU_LOGS_DIR.rglob('*') if f.is_file()) if UBUNTU_LOGS_DIR.exists() else 0
        return {
            'total_disk_gb': disk.total / (1024**3),
            'used_disk_gb': disk.used / (1024**3),
            'free_disk_gb': disk.free / (1024**3),
            'disk_percent': disk.percent,
            'logs_size_mb': logs_size / (1024**2),
            'needs_cleanup': disk.percent > MAX_DISK_USAGE_PERCENT
        }
    except Exception as e:
        return {'error': str(e)}

def cleanup_old_logs():
    try:
        if UBUNTU_LOGS_DIR.exists():
            cutoff = datetime.now() - timedelta(days=30)
            old_logs = [f for f in UBUNTU_LOGS_DIR.rglob('*.log') if datetime.fromtimestamp(f.stat().st_mtime) < cutoff]
            for log in old_logs[:10]:
                compressed = log.with_suffix('.log.gz')
                if not compressed.exists():
                    shutil.move(str(log), str(compressed))
            return len(old_logs)
        return 0
    except Exception as e:
        return 0

def get_system_health_status():
    stats = get_system_stats()
    health_score = 100
    issues = []
    warnings = []

    if stats['cpu_percent'] >= CRITICAL_THRESHOLD:
        health_score -= 20
        issues.append(f"Critical CPU: {stats['cpu_percent']:.1f}%")
    elif stats['cpu_percent'] >= WARNING_THRESHOLD:
        health_score -= 10
        warnings.append(f"High CPU: {stats['cpu_percent']:.1f}%")

    if stats['memory_percent'] >= CRITICAL_THRESHOLD:
        health_score -= 25
        issues.append(f"Critical Memory: {stats['memory_percent']:.1f}%")
    elif stats['memory_percent'] >= WARNING_THRESHOLD:
        health_score -= 15
        warnings.append(f"High Memory: {stats['memory_percent']:.1f}%")

    if stats['disk_usage'] >= CRITICAL_THRESHOLD:
        health_score -= 30
        issues.append(f"Critical Disk: {stats['disk_usage']:.1f}%")
    elif stats['disk_usage'] >= WARNING_THRESHOLD:
        health_score -= 20
        warnings.append(f"High Disk: {stats['disk_usage']:.1f}%")

    return {
        'health_score': max(0, health_score),
        'status': 'critical' if health_score < 50 else ('warning' if health_score < 80 else 'healthy'),
        'issues': issues,
        'warnings': warnings
    }


# ==================== Real-Time Dashboard API Functions ====================

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


def get_github_status_realtime() -> Dict:
    """Get GitHub status from real-time API"""
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

def sync_to_cloud(repo_type, local_path):
    try:
        if repo_type == 'github':
            repo = git.Repo(local_path)
            origin = repo.remote('origin')
            origin.push()
            return "Synced to GitHub"
        return f"{repo_type} sync not implemented"
    except Exception as e:
        return f"Sync error: {str(e)}"

def main():
    if not require_auth():
        return
    show_logout_button()

    # Initialize session state for real-time dashboard
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'system_stats' not in st.session_state:
        st.session_state.system_stats = []
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    if 'current_page' not in st.session_state:
        st.session_state.current_page = {
            'logs': 0,
            'processes': 0
        }
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True

    st.title("DevWorkspaces Comprehensive Dashboard")
    st.markdown("Real-time monitoring of workspace, GitHub CI/CD, and Hugging Face")
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select View", [
        "Overview",
        "Workspace Monitor",
        "GitHub CI/CD",
        "Hugging Face",
        "System Performance",
        "Process Monitor",
        "Storage Management",
        "Cloud Storage",
        "Script Analysis",
        "Pagination Demo"
    ])
    
    system_stats = get_system_stats()
    workspace_projects = get_workspace_projects()
    archived_projects = get_archived_projects()
    github_status = get_github_status()
    github_workflows = get_github_workflows()
    hf_status = get_huggingface_status()
    running_processes = get_running_processes()
    storage_info = get_storage_info()
    health = get_system_health_status()
    
    if page == "Overview":
        st.header("Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("CPU", f"{system_stats['cpu_percent']:.1f}%")
            st.metric("Memory", f"{system_stats['memory_percent']:.1f}%")
        with col2:
            st.metric("Projects", len(workspace_projects))
            st.metric("Processes", len(running_processes))
        with col3:
            st.metric("GitHub Status", github_status.get('status', 'unknown'))
        with col4:
            st.metric("HF Models", hf_status.get('num_models', 0))
        
        st.subheader("System Health")
        health_color = "green" if health['status'] == 'healthy' else ("orange" if health['status'] == 'warning' else "red")
        st.markdown(f"**Health Status:** :{health_color}[{health['status'].upper()}] (Score: {health['health_score']})")
        
        if health['issues']:
            for issue in health['issues']:
                st.error(issue)
        if health['warnings']:
            for warning in health['warnings']:
                st.warning(warning)
    
    elif page == "Workspace Monitor":
        st.header("Workspace Monitor")
        tab1, tab2 = st.tabs(["Current", "Archived"])
        with tab1:
            if workspace_projects:
                data = [{'Project': k, 'Size (MB)': v['size']/(1024*1024)} for k, v in workspace_projects.items()]
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.info("No projects found")
        with tab2:
            if archived_projects:
                st.info(f"Found {len(archived_projects)} archived projects")
            else:
                st.info("No archived projects")
    
    elif page == "GitHub CI/CD":
        st.header("GitHub CI/CD Status")
        if github_status.get('status') == 'rate_limited':
            st.warning("GitHub API rate limited. Set GITHUB_TOKEN.")
        elif github_status.get('status') != 'error':
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Stars", github_status.get('stars', 0))
            with col2: st.metric("Forks", github_status.get('forks', 0))
            with col3: st.metric("Issues", github_status.get('open_issues', 0))
        
        if github_workflows.get('status') != 'error':
            st.subheader("Workflow Stats")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total Runs", github_workflows.get('total_runs', 0))
            with col2: st.metric("Successful", github_workflows.get('successful', 0))
            with col3: st.metric("Failed", github_workflows.get('failed', 0))
            with col4: st.metric("In Progress", github_workflows.get('in_progress', 0))
    
    elif page == "Hugging Face":
        st.header("Hugging Face Status")
        if hf_status.get('status') != 'error':
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Username", hf_status.get('username', 'N/A'))
            with col2: st.metric("Models", hf_status.get('num_models', 0))
            with col3: st.metric("Datasets", hf_status.get('num_datasets', 0))
            with col4: st.metric("Spaces", hf_status.get('num_spaces', 0))
        if st.button("Sync to Hugging Face"):
            st.info("Sync functionality would be implemented here")
    
    elif page == "System Performance":
        st.header("System Performance")
        col1, col2, col3 = st.columns(3)
        with col1:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=system_stats['cpu_percent'],
                title={'text': "CPU %"}, gauge={'axis': {'range': [0, 100]}}))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=system_stats['memory_percent'],
                title={'text': "Memory %"}, gauge={'axis': {'range': [0, 100]}}))
            st.plotly_chart(fig, use_container_width=True)
        with col3:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=system_stats['disk_usage'],
                title={'text': "Disk %"}, gauge={'axis': {'range': [0, 100]}}))
            st.plotly_chart(fig, use_container_width=True)
    
    elif page == "Process Monitor":
        st.header("Process Monitor")
        if running_processes:
            data = [{'PID': p['pid'], 'Name': p['name'], 'CPU%': p['cpu_percent'], 'Mem%': p['memory_percent']} for p in running_processes]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No workspace processes running")
    
    elif page == "Storage Management":
        st.header("Storage Management")
        if not storage_info.get('error'):
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total", f"{storage_info['total_disk_gb']:.1f} GB")
            with col2: st.metric("Used", f"{storage_info['used_disk_gb']:.1f} GB")
            with col3: st.metric("Free", f"{storage_info['free_disk_gb']:.1f} GB")
            with col4: st.metric("Usage", f"{storage_info['disk_percent']:.1f}%")
            
            if storage_info['needs_cleanup']:
                st.warning("Disk usage is high!")
                if st.button("Clean Up Logs"):
                    result = cleanup_old_logs()
                    st.success(f"Cleaned {result} log files")
    
    elif page == "Cloud Storage":
        st.header("Cloud Storage")
        tab1, tab2, tab3 = st.tabs(["GitHub", "GitLab", "Bitbucket"])
        with tab1:
            st.subheader("GitHub")
            if st.button("Sync to GitHub"):
                result = sync_to_cloud('github', str(WORKSPACE_ROOT))
                st.success(result)
        with tab2:
            st.subheader("GitLab")
            st.info("Set GITLAB_TOKEN for GitLab access")
        with tab3:
            st.subheader("Bitbucket")
            st.info("Set BITBUCKET credentials for Bitbucket access")

    elif page == "Script Analysis":
        st.header("Script Analysis Dashboard")
        st.markdown("Comprehensive analysis of all scripts in the DevWorkspaces ecosystem")

        # Script categories
        script_categories = {
            "Bootstrap Scripts": ["bootstrap.sh", "scripts/bootstrap.sh"],
            "Hugging Face": ["scripts/huggingface_sync.py"],
            "Workers": ["services/workers/system_monitor.py", "services/workers/github_sync.py", "services/workers/log_aggregator.py"],
            "API Services": ["services/realtime_api/main.py", "services/realtime_api/config.py"],
            "Dashboard Scripts": ["projects/comprehensive-dashboard/run_dashboard.sh", "projects/python-dashboard/run_django.sh"],
            "CI/CD": [".github/workflows/python-app.yml", ".github/workflows/docker.yml"]
        }

        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Dependencies", "Execution Status", "Performance"])

        with tab1:
            st.subheader("Script Overview")
            for category, scripts in script_categories.items():
                with st.expander(f"{category} ({len(scripts)} scripts)"):
                    for script in scripts:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.code(script, language="text")
                        with col2:
                            if os.path.exists(script):
                                st.success("Exists")
                            else:
                                st.error("Missing")
                        with col3:
                            if os.path.exists(script):
                                size = os.path.getsize(script)
                                st.metric("Size", f"{size} bytes")

        with tab2:
            st.subheader("Dependency Analysis")
            st.markdown("### Key Dependencies")
            deps = {
                "Streamlit": "Web dashboard framework",
                "psutil": "System monitoring",
                "requests": "HTTP API calls",
                "plotly": "Data visualization",
                "pandas": "Data manipulation",
                "asyncio": "Asynchronous operations",
                "websockets": "Real-time communication"
            }
            for dep, desc in deps.items():
                st.markdown(f"**{dep}**: {desc}")

        with tab3:
            st.subheader("Execution Status")
            st.markdown("### Service Status")
            services_status = {
                "Django API": "http://localhost:8000",
                "Real-time API": "http://localhost:8765",
                "Dashboard": "Streamlit app"
            }
            for service, url in services_status.items():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"**{service}**")
                with col2:
                    try:
                        if "localhost:8000" in url:
                            response = requests.get(url, timeout=2)
                            st.success(f"Running (Status: {response.status_code})")
                        elif "localhost:8765" in url:
                            response = requests.get(url + "/api/health", timeout=2)
                            st.success(f"Running (Status: {response.status_code})")
                        else:
                            st.info("Local service")
                    except:
                        st.error("Not running")

        with tab4:
            st.subheader("Performance Metrics")
            st.markdown("### System Resource Usage by Scripts")

            # Mock performance data - in real implementation, this would be collected
            perf_data = {
                "system_monitor.py": {"cpu": 5.2, "memory": 45.1},
                "github_sync.py": {"cpu": 2.1, "memory": 32.8},
                "realtime_dashboard.py": {"cpu": 8.5, "memory": 156.3},
                "main.py": {"cpu": 3.2, "memory": 67.9}
            }

            df = pd.DataFrame.from_dict(perf_data, orient='index')
            st.dataframe(df, use_container_width=True)

            fig = px.bar(df, x=df.index, y=['cpu', 'memory'],
                        title="Script Performance Metrics",
                        labels={'index': 'Script', 'value': 'Usage (%)'})
            st.plotly_chart(fig, use_container_width=True)

    # ==================== NETWORK MANAGEMENT TAB ====================
    elif page == "Network Management":
        st.header("🌐 Network Management")
        st.markdown("Automated port forwarding, speed testing, and intelligent provider selection")

        # Get current network status
        network_status = get_network_status()

        # Main tabs for network management
        net_tab1, net_tab2, net_tab3, net_tab4 = st.tabs([
            "📊 Network Overview",
            "🚀 Speed Test",
            "🔗 Port Forwarding",
            "⚡ Auto-Switch"
        ])

        with net_tab1:
            st.subheader("Network Interfaces")

            # Display interfaces
            interfaces = network_status.get('interfaces', {})
            if interfaces:
                interface_data = []
                for name, info in interfaces.items():
                    if info.get('is_up'):
                        interface_data.append({
                            'Interface': name,
                            'IP Address': info.get('ip', 'N/A'),
                            'Gateway': info.get('gateway', 'N/A'),
                            'Speed (Mbps)': f"{info.get('speed_mbps', 0):.2f}" if info.get('speed_mbps') else "Not tested",
                            'Latency (ms)': f"{info.get('latency_ms', 0):.1f}" if info.get('latency_ms') else "Not tested"
                        })

                if interface_data:
                    df = pd.DataFrame(interface_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No active network interfaces found")
            else:
                st.info("No network interfaces discovered")

            # Best interface indicator
            best_iface = network_status.get('best_interface')
            if best_iface:
                st.success(f"✅ Best Connection: **{best_iface}**")
            else:
                st.warning("⚠️ No best interface selected - run speed test first")

            # Service bindings
            st.subheader("Service Bindings")
            services = network_status.get('services', {})
            for name, info in services.items():
                status = "🟢 Running" if info.get('running') else "🔴 Stopped"
                interface = info.get('interface') or "Not bound"
                st.markdown(f"**{name}**: {status} on {interface}")

        with net_tab2:
            st.subheader("Internet Speed Test")

            col1, col2 = st.columns(2)
            with col1:
                selected_iface = st.selectbox("Select Interface", options=["All"] + list(interfaces.keys()))

            with col2:
                st.markdown("")
                if st.button("🚀 Run Speed Test", type="primary"):
                    with st.spinner("Testing speed..."):
                        if selected_iface == "All":
                            result = test_network_speed()
                        else:
                            result = test_network_speed(selected_iface)

                        st.success(f"Download: {result.get('download_mbps', 0):.2f} Mbps")
                        st.success(f"Latency: {result.get('latency_ms', 0):.1f} ms")
                        st.info(f"Interface: {result.get('interface', 'N/A')}")

            # Speed history visualization
            st.subheader("Speed Comparison")
            if interfaces:
                speed_data = []
                for name, info in interfaces.items():
                    if info.get('speed_mbps'):
                        speed_data.append({
                            'Interface': name,
                            'Speed (Mbps)': info.get('speed_mbps', 0),
                            'Latency (ms)': info.get('latency_ms', 0) or 0
                        })

                if speed_data:
                    df = pd.DataFrame(speed_data)
                    fig = px.bar(df, x='Interface', y='Speed (Mbps)',
                               title="Network Speed by Interface",
                               color='Speed (Mbps)',
                               color_continuous_scale='Greens')
                    st.plotly_chart(fig, use_container_width=True)

        with net_tab3:
            st.subheader("SSH Tunnel / Port Forwarding")

            # Create new tunnel
            with st.expander("Create New Port Forward", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    local_port = st.number_input("Local Port", min_value=1024, max_value=65535, value=2222)
                with col2:
                    remote_host = st.text_input("Remote Host", value="localhost")
                with col3:
                    remote_port = st.number_input("Remote Port", min_value=1, max_value=65535, value=22)
                with col4:
                    ssh_host = st.text_input("SSH Host", value="user@server.com")

                if st.button("Create Tunnel"):
                    result = create_port_forward(local_port, remote_host, remote_port, ssh_host)
                    if result.get('success'):
                        st.success(f"Tunnel created: localhost:{local_port} -> {remote_host}:{remote_port}")
                    else:
                        st.error("Failed to create tunnel")

            # Active tunnels
            st.subheader("Active Tunnels")
            tunnels = network_status.get('tunnels', {})
            if tunnels:
                tunnel_data = []
                for port, info in tunnels.items():
                    tunnel_data.append({
                        'Local Port': info.get('local_port'),
                        'Remote': info.get('remote'),
                        'SSH Host': info.get('ssh_host'),
                        'Status': info.get('status')
                    })

                df = pd.DataFrame(tunnel_data)
                st.dataframe(df, use_container_width=True)

                # Close tunnel
                col1, col2 = st.columns(2)
                with col1:
                    close_port = st.selectbox("Select Tunnel to Close", options=list(tunnels.keys()))
                with col2:
                    st.markdown("")
                    if st.button("Close Tunnel"):
                        result = close_port_forward(int(close_port))
                        if result.get('success'):
                            st.success("Tunnel closed")
                            st.rerun()
                        else:
                            st.error("Failed to close tunnel")
            else:
                st.info("No active SSH tunnels")

            # Common port forwards
            st.subheader("Quick Connect")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("SSH to Server"):
                    st.code("ssh user@server.com -p 22", language="bash")
            with col2:
                if st.button("SFTP Transfer"):
                    st.code("sftp user@server.com", language="bash")
            with col3:
                if st.button("Git Clone"):
                    st.code("git clone git@github.com:user/repo.git", language="bash")

        with net_tab4:
            st.subheader("Auto-Switch to Best Provider")
            st.markdown("""
            This feature automatically switches all services to the fastest
            available network interface for optimal performance.
            """)

            # Current status
            is_monitoring = network_status.get('monitoring_active', False)
            best = network_status.get('best_interface')

            col1, col2 = st.columns(2)
            with col1:
                if is_monitoring:
                    st.success("✅ Auto-switch is ACTIVE")
                else:
                    st.warning("⚠️ Auto-switch is INACTIVE")

            with col2:
                if best:
                    st.info(f"Current best: **{best}**")
                else:
                    st.info("No best interface identified")

            # Controls
            st.subheader("Controls")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄 Switch Now"):
                    result = switch_to_best_interface()
                    st.success(f"Switched to {result.get('interface')}")
                    st.rerun()

            with col2:
                if st.button("▶️ Start Monitoring"):
                    network_mgr.start_monitoring()
                    st.success("Monitoring started")
                    st.rerun()

            with col3:
                if st.button("⏹️ Stop Monitoring"):
                    network_mgr.stop_monitoring()
                    st.success("Monitoring stopped")
                    st.rerun()

            # Monitoring settings
            with st.expander("Monitoring Settings"):
                interval = st.slider("Test Interval (seconds)", 60, 900, 300)
                st.caption(f"Network speed will be tested every {interval} seconds")

            # Failover settings
            st.subheader("⚡ Failover Configuration")
            st.markdown("Configure automatic failover when the primary connection fails")

            col1, col2 = st.columns(2)
            with col1:
                failover_enabled = st.toggle("Enable Failover", value=False)
            with col2:
                st.markdown("")
                if failover_enabled:
                    st.success("Failover protection is ENABLED")
                else:
                    st.warning("Failover protection is DISABLED")

            if failover_enabled:
                st.info("When enabled, services will automatically switch to the next fastest interface if the current one fails.")

    elif page == "Pagination Demo":
        st.header("Advanced Pagination Demo")
        st.markdown("Demonstration of pagination features for large datasets")

        # Generate sample data for pagination demo
        sample_data = []
        for i in range(1000):
            sample_data.append({
                'id': i + 1,
                'name': f'Item {i + 1}',
                'category': f'Category {(i % 10) + 1}',
                'value': i * 1.5,
                'status': 'Active' if i % 3 != 0 else 'Inactive',
                'timestamp': datetime.now() - timedelta(minutes=i)
            })

        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            items_per_page = st.selectbox("Items per page", [10, 25, 50, 100], index=2)
        with col2:
            search_term = st.text_input("Search items", placeholder="Type to search...")
        with col3:
            status_filter = st.selectbox("Status filter", ["All", "Active", "Inactive"])

        # Filter data
        filtered_data = sample_data
        if search_term:
            filtered_data = [item for item in filtered_data if search_term.lower() in item['name'].lower()]
        if status_filter != "All":
            filtered_data = [item for item in filtered_data if item['status'] == status_filter]

        # Initialize pagination state
        if 'pagination_page' not in st.session_state:
            st.session_state.pagination_page = 0

        # Calculate pagination
        total_items = len(filtered_data)
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

        # Page navigation
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 2, 1, 1])

        with col1:
            if st.button("⏮️ First", key="first_page"):
                st.session_state.pagination_page = 0
                st.rerun()

        with col2:
            if st.button("◀️ Prev", key="prev_page"):
                if st.session_state.pagination_page > 0:
                    st.session_state.pagination_page -= 1
                    st.rerun()

        with col3:
            page_input = st.number_input("Page", min_value=1, max_value=total_pages,
                                       value=st.session_state.pagination_page + 1, step=1)
            if page_input != st.session_state.pagination_page + 1:
                st.session_state.pagination_page = page_input - 1
                st.rerun()

        with col4:
            st.markdown(f"**of {total_pages}** (Total: {total_items} items)")

        with col5:
            if st.button("Next ▶️", key="next_page"):
                if st.session_state.pagination_page < total_pages - 1:
                    st.session_state.pagination_page += 1
                    st.rerun()

        with col6:
            if st.button("Last ⏭️", key="last_page"):
                st.session_state.pagination_page = total_pages - 1
                st.rerun()

        # Display current page data
        start_idx = st.session_state.pagination_page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_data = filtered_data[start_idx:end_idx]

        if page_data:
            df = pd.DataFrame(page_data)
            st.dataframe(df, use_container_width=True)

            # Summary statistics
            st.subheader("Page Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Items on page", len(page_data))
            with col2:
                active_count = sum(1 for item in page_data if item['status'] == 'Active')
                st.metric("Active items", active_count)
            with col3:
                avg_value = sum(item['value'] for item in page_data) / len(page_data)
                st.metric("Avg value", f"{avg_value:.2f}")
            with col4:
                categories = set(item['category'] for item in page_data)
                st.metric("Categories", len(categories))

            # Visualization
            st.subheader("Data Visualization")
            fig = px.scatter(df, x='id', y='value', color='status',
                           title=f"Items {start_idx + 1} - {end_idx} of {total_items}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data matches the current filters")

    # ==================== Real-Time Dashboard Pages ====================

    elif page == "Real-Time Overview":
        st.header("Real-Time Overview")

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

        stats = get_system_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("CPU Usage", f"{stats.get('cpu_percent', 0):.1f}%")
        with col2:
            st.metric("Memory Usage", f"{stats.get('memory_percent', 0):.1f}%")
        with col3:
            st.metric("Disk Usage", f"{stats.get('disk_usage', 0):.1f}%")
        with col4:
            processes = get_processes()
            st.metric("Processes", len(processes) if processes else 0)

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

    elif page == "Real-Time System Monitor":
        st.header("Real-Time System Monitor")

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

    elif page == "Real-Time Processes":
        st.header("Real-Time Running Processes")

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

    elif page == "Real-Time GitHub":
        st.header("Real-Time GitHub Repository")

        gh_status = get_github_status_realtime()

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

    elif page == "Real-Time Logs":
        st.header("Real-Time Overall Logs")
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

    elif page == "Real-Time Connections":
        st.header("Real-Time WebSocket Connections")

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

    # Auto-refresh for real-time pages
    if page.startswith("Real-Time") and st.session_state.auto_refresh:
        time.sleep(5)
        st.rerun()

    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: 30s")

if __name__ == "__main__":
    main()
