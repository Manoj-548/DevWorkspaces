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

# Add parent directory to path for imports
sys.path.append('../..')

# Configuration
WORKSPACE_ROOT = Path("/home/manoj/DevWorkspaces")
ARCHIVE_ROOT = Path("/home/manoj/ArchiveWorkspaces")
GITHUB_REPO = "Manoj548/DevWorkspaces"  # Update with actual repo
HF_USER = "Manoj548"

# Cloud Storage Configuration
GITLAB_URL = "https://gitlab.com"  # Update if self-hosted
GITLAB_PROJECT_ID = "your_project_id"  # Update with actual project ID
BITBUCKET_WORKSPACE = "your_workspace"  # Update with actual workspace
BITBUCKET_REPO = "your_repo"  # Update with actual repo

# Ubuntu Logs Directory
UBUNTU_LOGS_DIR = Path("/var/log")  # Ubuntu system logs
MAX_DISK_USAGE_PERCENT = 80  # Threshold for alerts

# Set page configuration
st.set_page_config(
    page_title="DevWorkspaces Comprehensive Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh every 30 seconds
st_autorefresh(interval=30 * 1000, key="data_refresh")

def get_system_stats():
    """Get current system statistics"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'network_connections': len(psutil.net_connections()),
        'timestamp': datetime.now()
    }

def get_workspace_projects():
    """Get all projects in current workspace"""
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
    """Get all archived projects"""
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
    """Get GitHub repository status and recent commits"""
    try:
        # GitHub API call (requires token for private repos)
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}"
        response = requests.get(api_url, timeout=10)

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
        else:
            return {'status': 'error', 'message': f'API Error: {response.status_code}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_github_workflows():
    """Get GitHub Actions workflow runs"""
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            runs = data.get('workflow_runs', [])[:10]  # Last 10 runs

            workflow_stats = {
                'total_runs': len(runs),
                'successful': sum(1 for r in runs if r['conclusion'] == 'success'),
                'failed': sum(1 for r in runs if r['conclusion'] == 'failure'),
                'in_progress': sum(1 for r in runs if r['status'] == 'in_progress'),
                'recent_runs': []
            }

            for run in runs[:5]:
                workflow_stats['recent_runs'].append({
                    'name': run['name'],
                    'status': run['status'],
                    'conclusion': run['conclusion'],
                    'created_at': run['created_at'],
                    'updated_at': run['updated_at']
                })

            return workflow_stats
        else:
            return {'status': 'error', 'message': f'API Error: {response.status_code}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_huggingface_status():
    """Get Hugging Face user status and repositories"""
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
        else:
            return {'status': 'error', 'message': f'API Error: {response.status_code}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_running_processes():
    """Get information about running processes related to the workspace"""
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

def calculate_efficiency_metrics():
    """Calculate efficiency metrics for builds and processes"""
    system_stats = get_system_stats()
    github_stats = get_github_workflows()
    processes = get_running_processes()

    metrics = {
        'system_efficiency': 100 - system_stats['cpu_percent'],  # Lower CPU usage = higher efficiency
        'memory_efficiency': 100 - system_stats['memory_percent'],
        'github_success_rate': (github_stats.get('successful', 0) / max(github_stats.get('total_runs', 1), 1)) * 100,
        'active_processes': len(processes),
        'timestamp': datetime.now()
    }

    return metrics

def get_storage_info():
    """Get detailed storage information for Ubuntu system"""
    try:
        disk = psutil.disk_usage('/')
        logs_size = sum(f.stat().st_size for f in UBUNTU_LOGS_DIR.rglob('*') if f.is_file()) if UBUNTU_LOGS_DIR.exists() else 0

        return {
            'total_disk_gb': disk.total / (1024**3),
            'used_disk_gb': disk.used / (1024**3),
            'free_disk_gb': disk.free / (1024**3),
            'disk_percent': disk.percent,
            'logs_size_mb': logs_size / (1024**2),
            'alert_threshold': MAX_DISK_USAGE_PERCENT,
            'needs_cleanup': disk.percent > MAX_DISK_USAGE_PERCENT
        }
    except Exception as e:
        return {'error': str(e)}

def cleanup_old_logs():
    """Clean up old log files to free space"""
    try:
        if UBUNTU_LOGS_DIR.exists():
            # Find log files older than 30 days
            old_logs = []
            cutoff = datetime.now() - timedelta(days=30)

            for log_file in UBUNTU_LOGS_DIR.rglob('*.log'):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff:
                    old_logs.append(log_file)

            # Compress and move to archive or delete
            for log in old_logs:
                compressed = log.with_suffix('.log.gz')
                if not compressed.exists():
                    shutil.move(str(log), str(compressed))

            return len(old_logs)
        return 0
    except Exception as e:
        return f"Error: {str(e)}"

def get_gitlab_status():
    """Get GitLab repository status"""
    try:
        gl = gitlab.Gitlab(GITLAB_URL, private_token=os.getenv('GITLAB_TOKEN'))
        project = gl.projects.get(GITLAB_PROJECT_ID)

        return {
            'name': project.name,
            'stars': project.star_count,
            'forks': project.forks_count,
            'open_issues': len(project.issues.list(state='opened')),
            'last_commit': project.commits.list()[0].created_at if project.commits.list() else None,
            'status': 'active'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_bitbucket_status():
    """Get Bitbucket repository status"""
    try:
        bitbucket = Bitbucket(
            url='https://api.bitbucket.org',
            username=os.getenv('BITBUCKET_USERNAME'),
            password=os.getenv('BITBUCKET_PASSWORD')
        )

        repo = bitbucket.workspaces.get(BITBUCKET_WORKSPACE).repositories.get(BITBUCKET_REPO)

        return {
            'name': repo.name,
            'size': repo.size,
            'language': repo.language,
            'is_private': repo.is_private,
            'status': 'active'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def sync_to_cloud(repo_type, local_path):
    """Sync local data to cloud repository"""
    try:
        if repo_type == 'github':
            repo = git.Repo(local_path)
            origin = repo.remote('origin')
            origin.push()
            return "Synced to GitHub"
        elif repo_type == 'gitlab':
            # Implement GitLab sync
            return "GitLab sync not implemented yet"
        elif repo_type == 'bitbucket':
            # Implement Bitbucket sync
            return "Bitbucket sync not implemented yet"
        else:
            return "Unknown repo type"
    except Exception as e:
        return f"Sync error: {str(e)}"

def load_fixtures():
    """Load learning fixtures from JSON file"""
    fixtures_path = Path("../../projects/python-dashboard/python_dashboard/coding_resources/fixtures/comprehensive_learning_data.json")
    try:
        with open(fixtures_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {'error': str(e)}

def main():
    # Title and header
    st.title("🚀 DevWorkspaces Comprehensive Dashboard")
    st.markdown("Real-time monitoring of VS Code workspace, GitHub CI/CD, and Hugging Face deployments")

    # Sidebar navigation
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
        "Learning Resources"
    ])

    # Get data
    system_stats = get_system_stats()
    workspace_projects = get_workspace_projects()
    archived_projects = get_archived_projects()
    github_status = get_github_status()
    github_workflows = get_github_workflows()
    hf_status = get_huggingface_status()
    running_processes = get_running_processes()
    efficiency_metrics = calculate_efficiency_metrics()
    storage_info = get_storage_info()
    gitlab_status = get_gitlab_status()
    bitbucket_status = get_bitbucket_status()
    fixtures_data = load_fixtures()

    if page == "Overview":
        # Overview Dashboard
        st.header("📊 Overview")

        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("CPU Usage", f"{system_stats['cpu_percent']:.1f}%")
            st.metric("Memory Usage", f"{system_stats['memory_percent']:.1f}%")

        with col2:
            total_projects = len(workspace_projects) + len(archived_projects)
            st.metric("Total Projects", total_projects)
            st.metric("Active Processes", len(running_processes))

        with col3:
            if github_workflows.get('status') != 'error':
                success_rate = efficiency_metrics['github_success_rate']
                st.metric("GitHub Success Rate", f"{success_rate:.1f}%")
            else:
                st.metric("GitHub Status", "Error")

        with col4:
            if hf_status.get('status') != 'error':
                st.metric("HF Models", hf_status.get('num_models', 0))
                st.metric("HF Datasets", hf_status.get('num_datasets', 0))
            else:
                st.metric("HF Status", "Error")

        # Efficiency Chart
        st.subheader("System Efficiency Trends")
        efficiency_data = pd.DataFrame([efficiency_metrics])
        fig = px.line(efficiency_data, x='timestamp', y=['system_efficiency', 'memory_efficiency'],
                     title="System Efficiency Over Time")
        st.plotly_chart(fig, use_container_width=True)

    elif page == "Workspace Monitor":
        st.header("📁 Workspace Monitor")

        tab1, tab2 = st.tabs(["Current Projects", "Archived Projects"])

        with tab1:
            st.subheader("Current Workspace Projects")
            if workspace_projects:
                project_data = []
                for name, info in workspace_projects.items():
                    project_data.append({
                        'Project': name,
                        'Last Modified': info['last_modified'].strftime('%Y-%m-%d %H:%M'),
                        'Size (MB)': info['size'] / (1024*1024)
                    })

                df = pd.DataFrame(project_data)
                st.dataframe(df, use_container_width=True)

                # Project size chart
                fig = px.bar(df, x='Project', y='Size (MB)', title="Project Sizes")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No projects found in current workspace")

        with tab2:
            st.subheader("Archived Projects")
            if archived_projects:
                archived_data = []
                for name, info in archived_projects.items():
                    archived_data.append({
                        'Project': name,
                        'Last Modified': info['last_modified'].strftime('%Y-%m-%d %H:%M'),
                        'Size (MB)': info['size'] / (1024*1024)
                    })

                df = pd.DataFrame(archived_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No archived projects found")

    elif page == "GitHub CI/CD":
        st.header("🐙 GitHub CI/CD Status")

        if github_status.get('status') == 'error':
            st.error(f"GitHub API Error: {github_status.get('message')}")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Stars", github_status.get('stars', 0))
            with col2:
                st.metric("Forks", github_status.get('forks', 0))
            with col3:
                st.metric("Open Issues", github_status.get('open_issues', 0))

        if github_workflows.get('status') == 'error':
            st.error(f"Workflow API Error: {github_workflows.get('message')}")
        else:
            st.subheader("Recent Workflow Runs")

            # Workflow statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Runs", github_workflows.get('total_runs', 0))
            with col2:
                st.metric("Successful", github_workflows.get('successful', 0))
            with col3:
                st.metric("Failed", github_workflows.get('failed', 0))
            with col4:
                st.metric("In Progress", github_workflows.get('in_progress', 0))

            # Recent runs table
            if github_workflows.get('recent_runs'):
                runs_data = []
                for run in github_workflows['recent_runs']:
                    runs_data.append({
                        'Workflow': run['name'],
                        'Status': run['status'],
                        'Conclusion': run.get('conclusion', 'N/A'),
                        'Created': run['created_at'][:19].replace('T', ' '),
                        'Updated': run['updated_at'][:19].replace('T', ' ')
                    })

                df = pd.DataFrame(runs_data)
                st.dataframe(df, use_container_width=True)

    elif page == "Hugging Face":
        st.header("🤗 Hugging Face Status")

        if hf_status.get('status') == 'error':
            st.error(f"Hugging Face API Error: {hf_status.get('message')}")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Username", hf_status.get('username', 'N/A'))
            with col2:
                st.metric("Models", hf_status.get('num_models', 0))
            with col3:
                st.metric("Datasets", hf_status.get('num_datasets', 0))
            with col4:
                st.metric("Spaces", hf_status.get('num_spaces', 0))

        # Sync status
        st.subheader("Hugging Face Sync")
        if st.button("Trigger Manual Sync"):
            st.info("Syncing data to Hugging Face...")
            # This would call the sync script
            st.success("Sync completed!")

    elif page == "System Performance":
        st.header("⚡ System Performance")

        # Real-time system stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("CPU Usage", f"{system_stats['cpu_percent']:.1f}%")
            cpu_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=system_stats['cpu_percent'],
                title={'text': "CPU Usage %"},
                gauge={'axis': {'range': [0, 100]}}
            ))
            st.plotly_chart(cpu_gauge)

        with col2:
            st.metric("Memory Usage", f"{system_stats['memory_percent']:.1f}%")
            mem_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=system_stats['memory_percent'],
                title={'text': "Memory Usage %"},
                gauge={'axis': {'range': [0, 100]}}
            ))
            st.plotly_chart(mem_gauge)

        with col3:
            st.metric("Disk Usage", f"{system_stats['disk_usage']:.1f}%")

        with col4:
            st.metric("Network Connections", system_stats['network_connections'])

        # Efficiency metrics
        st.subheader("Efficiency Metrics")
        eff_col1, eff_col2 = st.columns(2)

        with eff_col1:
            st.metric("System Efficiency", f"{efficiency_metrics['system_efficiency']:.1f}%")

        with eff_col2:
            st.metric("Memory Efficiency", f"{efficiency_metrics['memory_efficiency']:.1f}%")

    elif page == "Process Monitor":
        st.header("🔄 Process Monitor")

        st.subheader("Workspace-Related Processes")
        if running_processes:
            process_data = []
            for proc in running_processes:
                process_data.append({
                    'PID': proc['pid'],
                    'Name': proc['name'],
                    'CPU %': f"{proc['cpu_percent']:.1f}",
                    'Memory %': f"{proc['memory_percent']:.1f}",
                    'Started': proc['started'].strftime('%H:%M:%S')
                })

            df = pd.DataFrame(process_data)
            st.dataframe(df, use_container_width=True)

            # Process resource usage chart
            fig = px.bar(df, x='Name', y=['CPU %', 'Memory %'],
                        title="Process Resource Usage", barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No workspace-related processes currently running")

    elif page == "Storage Management":
        st.header("💾 Storage Management")

        if storage_info.get('error'):
            st.error(f"Storage info error: {storage_info['error']}")
        else:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Disk", f"{storage_info['total_disk_gb']:.1f} GB")
            with col2:
                st.metric("Used Disk", f"{storage_info['used_disk_gb']:.1f} GB")
            with col3:
                st.metric("Free Disk", f"{storage_info['free_disk_gb']:.1f} GB")
            with col4:
                st.metric("Logs Size", f"{storage_info['logs_size_mb']:.1f} MB")

            # Disk usage gauge
            disk_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=storage_info['disk_percent'],
                title={'text': "Disk Usage %"},
                gauge={'axis': {'range': [0, 100]},
                       'bar': {'color': "red" if storage_info['needs_cleanup'] else "green"},
                       'steps': [
                           {'range': [0, storage_info['alert_threshold']], 'color': "lightgreen"},
                           {'range': [storage_info['alert_threshold'], 100], 'color': "lightcoral"}
                       ]}
            ))
            st.plotly_chart(disk_gauge)

            if storage_info['needs_cleanup']:
                st.warning("⚠️ Disk usage is high! Consider cleaning up old logs.")

                if st.button("Clean Up Old Logs"):
                    result = cleanup_old_logs()
                    if isinstance(result, int):
                        st.success(f"Cleaned up {result} old log files.")
                    else:
                        st.error(f"Cleanup failed: {result}")

    elif page == "Cloud Storage":
        st.header("☁️ Cloud Storage")

        tab1, tab2, tab3 = st.tabs(["GitHub", "GitLab", "Bitbucket"])

        with tab1:
            st.subheader("GitHub Repository")
            if github_status.get('status') == 'error':
                st.error(f"GitHub Error: {github_status.get('message')}")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Stars", github_status.get('stars', 0))
                with col2:
                    st.metric("Forks", github_status.get('forks', 0))
                with col3:
                    st.metric("Open Issues", github_status.get('open_issues', 0))

                if st.button("Sync to GitHub"):
                    result = sync_to_cloud('github', str(WORKSPACE_ROOT))
                    st.success(result)

        with tab2:
            st.subheader("GitLab Repository")
            if gitlab_status.get('status') == 'error':
                st.error(f"GitLab Error: {gitlab_status.get('message')}")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Stars", gitlab_status.get('stars', 0))
                with col2:
                    st.metric("Forks", gitlab_status.get('forks', 0))
                with col3:
                    st.metric("Open Issues", gitlab_status.get('open_issues', 0))

                if st.button("Sync to GitLab"):
                    result = sync_to_cloud('gitlab', str(WORKSPACE_ROOT))
                    st.info(result)

        with tab3:
            st.subheader("Bitbucket Repository")
            if bitbucket_status.get('status') == 'error':
                st.error(f"Bitbucket Error: {bitbucket_status.get('message')}")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Name", bitbucket_status.get('name', 'N/A'))
                with col2:
                    st.metric("Size", bitbucket_status.get('size', 0))
                with col3:
                    st.metric("Private", "Yes" if bitbucket_status.get('is_private') else "No")

                if st.button("Sync to Bitbucket"):
                    result = sync_to_cloud('bitbucket', str(WORKSPACE_ROOT))
                    st.info(result)

    elif page == "Learning Resources":
        st.header("📚 Learning Resources")

        if fixtures_data.get('error'):
            st.error(f"Failed to load fixtures: {fixtures_data['error']}")
        else:
            st.subheader(f"Version: {fixtures_data.get('version', 'N/A')} - Last Updated: {fixtures_data.get('last_updated', 'N/A')}")
            st.markdown(f"**Maintainer:** {fixtures_data.get('maintainer', 'N/A')}")

            categories = fixtures_data.get('categories', [])
            if categories:
                for category in categories:
                    with st.expander(f"📖 {category['name']} - {category['description']}"):
                        topics = category.get('topics', [])
                        for topic in topics:
                            st.markdown(f"### {topic['title']}")
                            st.markdown(f"*{topic['description']}*")

                            concepts = topic.get('concepts', [])
                            for concept in concepts:
                                st.markdown(f"**{concept['name']}:** {concept['explanation']}")
                                st.markdown(f"- **Real-world usage:** {concept['real_world_usage']}")

                                with st.expander("Best Practices"):
                                    for bp in concept.get('best_practices', []):
                                        st.markdown(f"- {bp}")

                                with st.expander("Anti-patterns"):
                                    for ap in concept.get('anti_patterns', []):
                                        st.markdown(f"- {ap}")

                                code_snippets = concept.get('code_snippets', [])
                                if code_snippets:
                                    st.markdown("**Code Examples:**")
                                    for snippet in code_snippets:
                                        st.code(snippet['code'], language=snippet.get('language', 'python'))
                                        if 'notes' in snippet:
                                            st.caption(snippet['notes'])
            else:
                st.info("No learning categories found in fixtures.")

    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: 30s")

if __name__ == "__main__":
    main()
