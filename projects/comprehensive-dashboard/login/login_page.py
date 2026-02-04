import streamlit as st
import requests
import json
from typing import Optional, Dict, Any

# Django API Configuration
DJANGO_API_BASE = "http://localhost:8000/api"
LOGIN_ENDPOINT = f"{DJANGO_API_BASE}/auth/login/"
LOGOUT_ENDPOINT = f"{DJANGO_API_BASE}/auth/logout/"
USER_ENDPOINT = f"{DJANGO_API_BASE}/auth/user/"

class DjangoAuthenticator:
    """Django API Authentication Handler"""

    def __init__(self, api_base: str = DJANGO_API_BASE):
        self.api_base = api_base
        self.session = requests.Session()

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user with Django API"""
        try:
            payload = {
                'username': username,
                'password': password
            }

            response = self.session.post(LOGIN_ENDPOINT, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Store token in session state
                if 'token' in data:
                    st.session_state['auth_token'] = data['token']
                if 'user' in data:
                    st.session_state['user'] = data['user']
                st.session_state['authenticated'] = True
                return {'success': True, 'message': 'Login successful'}
            elif response.status_code == 401:
                return {'success': False, 'message': 'Invalid credentials'}
            elif response.status_code == 400:
                error_data = response.json()
                return {'success': False, 'message': error_data.get('error', 'Login failed')}
            else:
                return {'success': False, 'message': f'Login failed: {response.status_code}'}

        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'Connection error: {str(e)}'}
        except json.JSONDecodeError:
            return {'success': False, 'message': 'Invalid response from server'}

    def logout(self) -> bool:
        """Logout user"""
        try:
            headers = {}
            if 'auth_token' in st.session_state:
                headers['Authorization'] = f'Bearer {st.session_state["auth_token"]}'

            response = self.session.post(LOGOUT_ENDPOINT, headers=headers, timeout=10)

            # Clear session regardless of response
            if 'auth_token' in st.session_state:
                del st.session_state['auth_token']
            if 'user' in st.session_state:
                del st.session_state['user']
            st.session_state['authenticated'] = False

            return response.status_code in [200, 204]
        except:
            # Clear session even if logout request fails
            if 'auth_token' in st.session_state:
                del st.session_state['auth_token']
            if 'user' in st.session_state:
                del st.session_state['user']
            st.session_state['authenticated'] = False
            return True

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        try:
            headers = {}
            if 'auth_token' in st.session_state:
                headers['Authorization'] = f'Bearer {st.session_state["auth_token"]}'

            response = self.session.get(USER_ENDPOINT, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                return None
        except:
            return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)


def show_login_page() -> bool:
    """Display the login page and return True if logged in"""
    st.title("🔐 Login to DevWorkspaces Dashboard")

    st.markdown("""
    Welcome to the DevWorkspaces Comprehensive Dashboard.
    Please login with your Django API credentials.
    """)

    # Initialize authenticator
    auth = DjangoAuthenticator()

    # Check if already authenticated
    if auth.is_authenticated():
        user = st.session_state.get('user', {})
        st.success(f"✅ Already logged in as **{user.get('username', 'User')}**")
        return True

    # Login form
    username = st.text_input("Username", placeholder="Enter username", key="login_username")
    password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")

    col1, col2 = st.columns([1, 1])
    with col1:
        login_clicked = st.button("Login", type="primary", use_container_width=True)

    if login_clicked:
        if not username or not password:
            st.error("Please enter both username and password")
        else:
            with st.spinner("Authenticating..."):
                result = auth.login(username, password)

            if result['success']:
                st.success("Login successful! Loading dashboard...")
                st.rerun()
            else:
                st.error(result['message'])

    # Test connection
    with st.expander("🔍 Test API Connection"):
        if st.button("Test Django API Connection"):
            try:
                response = requests.get(f"{DJANGO_API_BASE}/health/", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Django API is accessible")
                else:
                    st.warning(f"⚠️ Django API responded with status {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Cannot connect to Django API: {str(e)}")
                st.info("Make sure Django server is running on port 8000")

    # Demo credentials info
    st.info("💡 **Default Credentials:**\n- Username: `admin`\n- Password: `admin123`")

    return False


def show_logout_button():
    """Display logout button in sidebar"""
    auth = DjangoAuthenticator()

    if auth.is_authenticated():
        user = st.session_state.get('user', {})
        username = user.get('username', 'User')

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Logged in as:** {username}")

        if st.sidebar.button("Logout", key="logout_button"):
            auth.logout()
            st.sidebar.success("Logged out successfully")
            st.rerun()


def require_auth():
    """Check if user is authenticated, show login if not"""
    auth = DjangoAuthenticator()

    if not auth.is_authenticated():
        show_login_page()
        return False

    # Token is valid, user is authenticated
    return True


# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'user' not in st.session_state:
    st.session_state['user'] = None

if 'auth_token' not in st.session_state:
    st.session_state['auth_token'] = None


if __name__ == "__main__":
    show_login_page()
