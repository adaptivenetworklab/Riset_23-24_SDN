import subprocess
import shutil
import platform
import os
from .debug_manager import debug_print, error_print, warning_print

class PrerequisitesChecker:
    """Check if all required tools are installed and accessible."""
    
    @staticmethod
    def check_all_prerequisites():
        """Check all prerequisites and return a report."""
        checks = {
            'docker': PrerequisitesChecker.check_docker(),
            'docker_compose': PrerequisitesChecker.check_docker_compose(),
            'python3': PrerequisitesChecker.check_python3(),
        }
        
        # Only check Mininet and sudo on Linux systems
        if platform.system().lower() == 'linux':
            checks['mininet'] = PrerequisitesChecker.check_mininet()
            checks['sudo'] = PrerequisitesChecker.check_sudo()
        else:
            warning_print("WARNING: Mininet and sudo checks skipped on non-Linux platform")
            checks['mininet'] = True  # Skip check on non-Linux
            checks['sudo'] = True     # Skip check on non-Linux
        
        all_ok = all(checks.values())
        return all_ok, checks
    
    @staticmethod
    def check_docker():
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                debug_print(f"Docker found: {result.stdout.strip()}")
                return True
            else:
                error_print(f"Docker check failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            error_print("Docker check timed out")
            return False
        except FileNotFoundError:
            error_print("Docker command not found")
            return False
        except Exception as e:
            error_print(f"Docker check error: {e}")
            return False
    
    @staticmethod
    def check_docker_compose():
        """Check if Docker Compose is available."""
        # Check for docker-compose command
        if shutil.which("docker-compose"):
            try:
                result = subprocess.run(
                    ["docker-compose", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    debug_print(f"Docker Compose found: {result.stdout.strip()}")
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # Check for docker compose (newer syntax)
        try:
            result = subprocess.run(
                ["docker", "compose", "version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                debug_print(f"Docker Compose (plugin) found: {result.stdout.strip()}")
                return True
            else:
                error_print("Docker Compose not available")
                return False
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            error_print("Docker Compose check failed")
            return False
    
    @staticmethod
    def check_mininet():
        """Check if Mininet is available (Linux only)."""
        if platform.system().lower() != 'linux':
            return True  # Skip on non-Linux
            
        try:
            result = subprocess.run(
                ["mn", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                debug_print(f"Mininet found: {result.stdout.strip()}")
                return True
            else:
                error_print(f"Mininet check failed: {result.stderr}")
                return False
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            error_print("Mininet not found or check failed")
            return False
    
    @staticmethod
    def check_python3():
        """Check if Python 3 is available."""
        try:
            result = subprocess.run(
                ["python3", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                debug_print(f"Python3 found: {result.stdout.strip()}")
                return True
            else:
                # Try python on Windows
                if platform.system().lower() == 'windows':
                    result = subprocess.run(
                        ["python", "--version"], 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    if result.returncode == 0 and "Python 3" in result.stdout:
                        debug_print(f"Python found: {result.stdout.strip()}")
                        return True
                error_print("Python 3 not found")
                return False
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            error_print("Python 3 check failed")
            return False
    
    @staticmethod
    def check_sudo():
        """Check if sudo is available (Linux only)."""
        if platform.system().lower() != 'linux':
            return True  # Skip on non-Linux
            
        return shutil.which("sudo") is not None
    
    @staticmethod
    def get_installation_instructions():
        """Get installation instructions for missing prerequisites."""
        system = platform.system().lower()
        
        instructions = {
            'docker': f"""
Install Docker:
{PrerequisitesChecker._get_docker_install_cmd(system)}
Or visit: https://docs.docker.com/get-docker/
""",
            'docker_compose': f"""
Install Docker Compose:
{PrerequisitesChecker._get_docker_compose_install_cmd(system)}
Or visit: https://docs.docker.com/compose/install/
""",
            'python3': f"""
Install Python 3:
{PrerequisitesChecker._get_python_install_cmd(system)}
""",
        }
        
        if system == 'linux':
            instructions.update({
                'mininet': """
Install Mininet:
Ubuntu/Debian: sudo apt-get install mininet
Or visit: http://mininet.org/download/
""",
                'sudo': """
sudo should be available on most Linux systems.
If not available, run as root or install sudo package.
"""
            })
        
        return instructions
    
    @staticmethod
    def _get_docker_install_cmd(system):
        if system == 'linux':
            return "Ubuntu/Debian: sudo apt-get install docker.io\nCentOS/RHEL: sudo yum install docker"
        elif system == 'windows':
            return "Download Docker Desktop from https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        elif system == 'darwin':
            return "Download Docker Desktop from https://desktop.docker.com/mac/main/amd64/Docker.dmg"
        else:
            return "Visit https://docs.docker.com/get-docker/ for installation instructions"
    
    @staticmethod
    def _get_docker_compose_install_cmd(system):
        if system == 'linux':
            return """sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose"""
        else:
            return "Docker Compose is included with Docker Desktop"
    
    @staticmethod
    def _get_python_install_cmd(system):
        if system == 'linux':
            return "Ubuntu/Debian: sudo apt-get install python3\nCentOS/RHEL: sudo yum install python3"
        elif system == 'windows':
            return "Download from https://www.python.org/downloads/windows/"
        elif system == 'darwin':
            return "Download from https://www.python.org/downloads/mac-osx/ or use Homebrew: brew install python3"
        else:
            return "Visit https://www.python.org/downloads/ for installation instructions"