#!/usr/bin/env python3
"""
NetFlux5G Editor - Main Application Entry Point

A network topology editor for 5G networks with support for:
- Visual network design with drag-and-drop components
- 5G Core component configuration
- Mininet script generation
- Docker Compose export
- Automated deployment
"""

import sys
import os
import argparse
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_application():
    """Setup the QApplication with proper configuration."""
    app = QApplication(sys.argv)
    app.setApplicationName("NetFlux5G Editor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NetFlux5G Project")
    
    # Set application icon if available
    icon_path = os.path.join(os.path.dirname(__file__), "gui", "Icon", "app-icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    return app

def show_splash_screen():
    """Show splash screen during application startup."""
    splash_path = os.path.join(os.path.dirname(__file__), "gui", "Icon", "splash.png")
    
    if os.path.exists(splash_path):
        pixmap = QPixmap(splash_path)
        splash = QSplashScreen(pixmap)
        splash.setMask(pixmap.mask())
        splash.show()
        splash.showMessage("Loading NetFlux5G Editor...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        return splash
    return None

def check_system_requirements():
    """Check basic system requirements."""
    try:
        # Check Python version
        if sys.version_info < (3, 6):
            QMessageBox.critical(
                None, 
                "System Requirements", 
                "Python 3.6 or higher is required to run NetFlux5G Editor."
            )
            return False
        
        # Check PyQt5 availability
        from PyQt5.QtCore import QT_VERSION_STR
        print(f"Using PyQt5 version: {QT_VERSION_STR}")
        
        return True
        
    except ImportError as e:
        QMessageBox.critical(
            None,
            "Missing Dependencies", 
            f"Required dependencies are missing:\n{str(e)}\n\nPlease install requirements using:\npip install -r requirements.txt"
        )
        return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="NetFlux5G Editor - 5G Network Topology Designer")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--file", type=str, help="Open a topology file on startup")
    parser.add_argument("--version", action="version", version="NetFlux5G Editor 1.0.0")
    parser.add_argument("--no-splash", action="store_true", help="Disable splash screen")
    parser.add_argument("--check-prereq", action="store_true", help="Check prerequisites and exit")
    
    return parser.parse_args()

def main():
    """Main application entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Setup QApplication
        app = setup_application()
        
        # Check system requirements
        if not check_system_requirements():
            return 1
        
        # Enable debug mode if requested
        if args.debug:
            from gui.debug_manager import set_debug_enabled
            set_debug_enabled(True)
            print("Debug mode enabled")
        
        # Check prerequisites if requested
        if args.check_prereq:
            from gui.prerequisites_checker import PrerequisitesChecker
            all_ok, checks = PrerequisitesChecker.check_all_prerequisites()
            
            print("Prerequisites Check:")
            print("=" * 40)
            for tool, status in checks.items():
                status_str = "✓ OK" if status else "✗ MISSING"
                print(f"{tool:15} : {status_str}")
            
            if not all_ok:
                print("\nInstallation instructions:")
                instructions = PrerequisitesChecker.get_installation_instructions()
                missing = [tool for tool, ok in checks.items() if not ok]
                for tool in missing:
                    print(f"\n{tool.upper()}:")
                    print(instructions[tool])
                return 1
            else:
                print("\n✓ All prerequisites are satisfied!")
                return 0
        
        # Show splash screen
        splash = None
        if not args.no_splash:
            splash = show_splash_screen()
            if splash:
                app.processEvents()
        
        # Import and create main window
        try:
            from gui.main_window import MainWindow
            
            # Add small delay for splash screen
            if splash:
                QTimer.singleShot(1500, lambda: splash.close() if splash else None)
                QTimer.singleShot(2000, lambda: create_and_show_main_window(app, args))
                
                return app.exec_()
            else:
                return create_and_show_main_window(app, args)
                
        except ImportError as e:
            if splash:
                splash.close()
            QMessageBox.critical(
                None,
                "Import Error",
                f"Failed to import main window:\n{str(e)}\n\nPlease check your installation."
            )
            return 1
            
    except Exception as e:
        QMessageBox.critical(
            None,
            "Startup Error",
            f"An error occurred during startup:\n{str(e)}"
        )
        return 1

def create_and_show_main_window(app, args):
    """Create and show the main application window."""
    try:
        from gui.main_window import MainWindow
        
        # Create main window
        main_window = MainWindow()
        
        # Open file if specified
        if args.file and os.path.exists(args.file):
            # Add timer to load file after window is shown
            QTimer.singleShot(100, lambda: main_window.load_topology_file(args.file))
        
        # Show main window
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()
        
        return app.exec_()
        
    except Exception as e:
        QMessageBox.critical(
            None,
            "Main Window Error", 
            f"Failed to create main window:\n{str(e)}"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())