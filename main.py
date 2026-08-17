"""
Pocket AI - Main Entry Point
"""

import warnings
import sys
import argparse

# Suppress ALL warnings globally before any other imports
# This is aggressive but ensures clean console output
warnings.simplefilter("ignore")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PySide6.QtGui import QFont, QColor, QIcon
from gui.app import MainWindow
from qfluentwidgets import qconfig, Theme, SplashScreen
from config import ULTRA_LIGHT_MODE

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch Jarvis")
    parser.add_argument("--listen", action="store_true", help="start push-to-talk listening immediately")
    args = parser.parse_args()
    app = QApplication([sys.argv[0]])
    
    # Configure Aura Theme
    qconfig.theme = Theme.DARK
    
    # Set default font
    app.setFont(QFont("Segoe UI", 10))
    
    # Create SplashScreen
    splash = SplashScreen(QIcon("gui/assets/logo.png" if "gui/assets/logo.png" else None), None)
    splash.setIconSize(QSize(100, 100))
    splash.show()
    
    # Create main window
    window = MainWindow(listen_on_start=args.listen)
    
    # Show window and finish splash
    window.show()
    splash.finish()

    if ULTRA_LIGHT_MODE:
        app.setQuitOnLastWindowClosed(False)
        tray = QSystemTrayIcon(QIcon("icon.png"), app)
        menu = QMenu()
        show_action = menu.addAction("Show Chat")
        show_action.triggered.connect(window.showNormal)
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(lambda: (window.showNormal(), window._navigate_to_tab("settingsInterface")))
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        def quit_app():
            window._quitting = True
            app.quit()
        quit_action.triggered.connect(quit_app)
        tray.setContextMenu(menu)
        tray.activated.connect(lambda reason: window.showNormal() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        tray.show()
        window.hide()
    
    sys.exit(app.exec())
