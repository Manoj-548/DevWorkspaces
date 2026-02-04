#!/usr/bin/env python3
"""
Master Debug and Run Script for DevWorkspaces
This script provides modular functions to run, debug, and manage all services.
Usage: python run.py [command] [options]
Commands:
    install     - Install all dependencies
    start      - Start all services
    stop       - Stop all services
    restart    - Restart services
    status     - Check service status
    test       - Test all components
    debug      - Debug mode (run main API)
    dashboard  - Run dashboard
    api        - Run API server only
    help       - Show this help message
"""

import os
import sys
import time
import json
import subprocess
import signal
from datetime import datetime
from typing import Optional, Dict, List

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.join(PROJECT_ROOT, "services")
PROJECTS_DIR = os.path.join(PROJECT_ROOT, "projects")


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log(message: str, level: str = "INFO"):
    """Log with timestamp and level"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_colors = {
        "INFO": Colors.OKGREEN,
        "WARNING": Colors.WARNING,
        "ERROR": Colors.FAIL,
        "DEBUG": Colors.OKBLUE
    }
    color = level_colors.get(level, Colors.ENDC)
    print(f"[{timestamp}] [{color}{level}{Colors.ENDC}] {message}")


def run_command(cmd: List[str], cwd: str = None, capture: bool = True, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a shell command"""
    try:
        return subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=capture,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        log(f"Command timed out: {' '.join(cmd)}", "ERROR")
        return subprocess.CompletedProcess(cmd, 1, "", "Timeout")
    except FileNotFoundError:
        log(f"Command not found: {cmd[0]}", "ERROR")
        return subprocess.CompletedProcess(cmd, 1, "", f"{cmd[0]} not found")


def check_command_exists(cmd: str) -> bool:
    """Check if a command exists"""
    result = run_command(["which", cmd], capture=True)
    return result.returncode == 0


def get_docker_cmd() -> List[str]:
    """Get the correct docker command (docker-compose vs docker compose)"""
    if check_command_exists("docker-compose"):
        return ["docker-compose"]
    elif check_command_exists("docker"):
        # Try docker compose (v2)
        result = run_command(["docker", "compose", "version"], capture=True)
        if result.returncode == 0:
            return ["docker", "compose"]
    return None


class ServiceManager:
    """Manages all services"""

    def __init__(self):
        self.services = {
            "redis": {"port": 6379, "status": "stopped"},
            "realtime-api": {"port": 8765, "status": "stopped"},
            "dashboard": {"port": 8501, "status": "stopped"},
        }
        self.processes = {}
        self.docker_cmd = get_docker_cmd()

    def check_port(self, port: int) -> bool:
        """Check if a port is in use"""
        result = run_command(["lsof", "-i", f":{port}"])
        return result.returncode == 0

    def check_redis(self) -> bool:
        """Check if Redis is running"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return True
        except:
            return False

    def start_redis(self) -> bool:
        """Start Redis server"""
        if self.check_port(6379):
            log("Redis already running on port 6379", "WARNING")
            return True

        log("Starting Redis...")
        
        # Try system redis first
        if check_command_exists("redis-server"):
            result = run_command(["redis-server", "--daemonize", "yes"])
            if result.returncode == 0:
                for _ in range(10):
                    if self.check_redis():
                        log("Redis started successfully", "INFO")
                        self.services["redis"]["status"] = "running"
                        return True
                    time.sleep(1)
        
        # Try docker redis as fallback
        if check_command_exists("docker"):
            log("Trying Docker Redis...", "INFO")
            result = run_command(["docker", "run", "-d", "--name", "dev-redis", "-p", "6379:6379", "redis:alpine"])
            if result.returncode == 0:
                time.sleep(3)
                for _ in range(10):
                    if self.check_redis():
                        log("Redis (Docker) started successfully", "INFO")
                        self.services["redis"]["status"] = "running"
                        return True
                    time.sleep(1)

        log("Redis failed to start. Install Redis or Docker.", "ERROR")
        return False

    def start_realtime_api(self, debug: bool = False) -> bool:
        """Start the Real-Time API server"""
        if self.check_port(8765):
            log("Real-Time API already running on port 8765", "WARNING")
            return True

        log("Starting Real-Time API...")

        # Start Redis first if not running
        if not self.check_redis():
            log("Redis not running. Starting it...", "WARNING")
            self.start_redis()

        cmd = [sys.executable, "main.py"]
        if debug:
            cmd.append("--reload")

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=os.path.join(SERVICES_DIR, "realtime_api"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes["realtime-api"] = proc

            for _ in range(15):
                try:
                    response = requests_get("http://localhost:8765/api/health")
                    if response and response.status_code == 200:
                        log("Real-Time API started successfully", "INFO")
                        self.services["realtime-api"]["status"] = "running"
                        return True
                except:
                    pass
                time.sleep(1)

            log("Real-Time API failed to start", "ERROR")
            return False
        except Exception as e:
            log(f"Error starting Real-Time API: {e}", "ERROR")
            return False

    def start_dashboard(self) -> bool:
        """Start the dashboard"""
        if self.check_port(8501):
            log("Dashboard already running on port 8501", "WARNING")
            return True

        log("Starting Dashboard...")

        try:
            proc = subprocess.Popen(
                ["streamlit", "run", "realtime_dashboard.py"],
                cwd=os.path.join(PROJECTS_DIR, "comprehensive-dashboard"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes["dashboard"] = proc

            for _ in range(20):
                try:
                    response = requests_get("http://localhost:8501")
                    if response and response.status_code == 200:
                        log("Dashboard started successfully", "INFO")
                        self.services["dashboard"]["status"] = "running"
                        return True
                except:
                    pass
                time.sleep(1)

            log("Dashboard failed to start", "ERROR")
            return False
        except Exception as e:
            log(f"Error starting Dashboard: {e}", "ERROR")
            return False

    def start_workers(self) -> bool:
        """Start background workers"""
        log("Starting background workers...")

        try:
            proc = subprocess.Popen(
                [sys.executable, "start_workers.py"],
                cwd=os.path.join(SERVICES_DIR, "workers"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes["workers"] = proc
            log("Background workers started", "INFO")
            return True
        except Exception as e:
            log(f"Error starting workers: {e}", "ERROR")
            return False

    def get_status(self) -> Dict:
        """Get status of all services"""
        status = {}
        for name, info in self.services.items():
            status[name] = {
                "port": info["port"],
                "status": info["status"],
                "running": self.check_port(info["port"])
            }
        return status

    def stop_all(self):
        """Stop all services"""
        log("Stopping all services...")

        for name, proc in self.processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass

        self.processes.clear()

        # Stop Docker containers
        if check_command_exists("docker"):
            run_command(["docker", "stop", "dev-redis"], capture=True)
            run_command(["docker", "rm", "dev-redis"], capture=True)

        for name in self.services:
            self.services[name]["status"] = "stopped"

        log("All services stopped", "INFO")


def requests_get(url: str, timeout: int = 5):
    """Simple HTTP GET request"""
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return type('Response', (), {'status_code': 200, 'text': response.read()})()
    except:
        return None


# Commands

def cmd_install():
    """Install dependencies"""
    log("Installing dependencies...")

    req_files = [
        os.path.join(PROJECT_ROOT, "requirements.txt"),
        os.path.join(PROJECTS_DIR, "comprehensive-dashboard", "requirements.txt"),
        os.path.join(SERVICES_DIR, "realtime_api", "requirements.txt"),
    ]

    for req_file in req_files:
        if os.path.exists(req_file):
            log(f"Installing from {req_file}")
            run_command([sys.executable, "-m", "pip", "install", "-r", req_file])

    log("Dependencies installed", "INFO")
    log("Note: If Docker/Redis not found, install them separately or use apt:", "WARNING")
    log("  sudo apt install docker.io docker-compose redis-server", "INFO")


def cmd_build():
    """Build Docker images"""
    docker_cmd = get_docker_cmd()
    if not docker_cmd:
        log("Docker not found. Install Docker first.", "ERROR")
        return

    log("Building Docker images...")

    services_to_build = [
        ("services/realtime_api", "realtime-api"),
        ("projects/comprehensive-dashboard", "dashboard"),
    ]

    for context, tag in services_to_build:
        log(f"Building {tag}...")
        result = run_command(docker_cmd + ["build", "-t", f"devworkspaces:{tag}", context])
        if result.returncode == 0:
            log(f"{tag} built successfully", "INFO")
        else:
            log(f"{tag} build failed: {result.stderr}", "ERROR")

    log("Docker build complete", "INFO")


def cmd_start(detached: bool = True):
    """Start all services"""
    docker_cmd = get_docker_cmd()
    
    if docker_cmd:
        log("Starting all services using Docker Compose...", "INFO")
        result = run_command(docker_cmd + ["up", "-d" if detached else "up"])
        if result.returncode == 0:
            log("Services started via Docker", "INFO")
        else:
            log(f"Docker failed: {result.stderr}", "WARNING")
            log("Falling back to manual start...", "INFO")
    
    # Manual start as fallback or alternative
    manager = ServiceManager()
    
    # Start Redis
    if not manager.check_port(6379):
        manager.start_redis()
    
    # Start API
    manager.start_realtime_api()
    
    # Start Dashboard
    manager.start_dashboard()


def cmd_stop():
    """Stop all services"""
    log("Stopping all services...")
    
    docker_cmd = get_docker_cmd()
    if docker_cmd:
        run_command(docker_cmd + ["down"], capture=True)
    
    manager = ServiceManager()
    manager.stop_all()
    
    log("Services stopped", "INFO")


def cmd_restart():
    """Restart all services"""
    log("Restarting services...")
    cmd_stop()
    time.sleep(2)
    cmd_start(detached=False)


def cmd_status():
    """Check service status"""
    manager = ServiceManager()
    status = manager.get_status()

    print("\n" + "=" * 60)
    print("SERVICE STATUS")
    print("=" * 60)
    
    docker_available = "OK" if check_command_exists("docker") or check_command_exists("docker-compose") else "MISSING"
    redis_available = "OK" if check_command_exists("redis-server") else "MISSING"
    
    print(f"Docker:     {docker_available}")
    print(f"Redis:      {redis_available}")
    print("-" * 60)

    for name, info in status.items():
        running = info["running"]
        status_icon = "[RUNNING]" if running else "[STOPPED]"
        color = Colors.OKGREEN if running else Colors.FAIL

        print(f"{color}{status_icon}{Colors.ENDC} {name:15} port={info['port']}")

    print("=" * 60 + "\n")


def cmd_test():
    """Test all components"""
    log("Testing all components...")

    manager = ServiceManager()

    tests = [
        ("Redis", manager.check_redis),
        ("API Health", lambda: requests_get("http://localhost:8765/api/health") is not None),
        ("Dashboard", lambda: requests_get("http://localhost:8501") is not None),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
            status = Colors.OKGREEN + "PASS" + Colors.ENDC if passed else Colors.FAIL + "FAIL" + Colors.ENDC
            log(f"  {name}: {status}")
        except Exception as e:
            results.append((name, False))
            log(f"  {name}: {Colors.FAIL}ERROR{Colors.ENDC} - {e}")

    passed = sum(1 for _, p in results if p)
    log(f"Tests complete: {passed}/{len(results)} passed", 
        "INFO" if passed == len(results) else "WARNING")


def cmd_debug():
    """Debug mode - run main API in foreground"""
    log("Starting Real-Time API in debug mode...", "INFO")
    
    manager = ServiceManager()
    manager.start_redis()
    manager.start_realtime_api(debug=True)


def cmd_dashboard():
    """Run dashboard only"""
    log("Starting Dashboard...", "INFO")
    
    manager = ServiceManager()
    manager.start_dashboard()


def cmd_api():
    """Run API server only"""
    log("Starting API server...", "INFO")
    
    manager = ServiceManager()
    manager.start_redis()
    manager.start_realtime_api()


def cmd_help():
    """Show help message"""
    print(__doc__)


# Main entry point
def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        cmd_help()
        return

    command = sys.argv[1].lower()

    handlers = {
        "install": cmd_install,
        "build": cmd_build,
        "start": lambda: cmd_start(detached=True),
        "stop": cmd_stop,
        "restart": cmd_restart,
        "status": cmd_status,
        "test": cmd_test,
        "debug": cmd_debug,
        "dashboard": cmd_dashboard,
        "api": cmd_api,
        "help": cmd_help,
        "--help": cmd_help,
        "-h": cmd_help,
    }

    handler = handlers.get(command)
    if handler:
        try:
            handler()
        except KeyboardInterrupt:
            log("Interrupted by user", "WARNING")
            manager = ServiceManager()
            manager.stop_all()
        except Exception as e:
            log(f"Error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
    else:
        log(f"Unknown command: {command}", "ERROR")
        cmd_help()


if __name__ == "__main__":
    main()
