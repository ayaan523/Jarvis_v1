"""
Global stylesheet for JARVIS Application (Iron Man Red & Gold Armor Theme).
"""

# JARVIS Red & Gold Palette
# Main Background: #120204 (Deep Crimson Black)
# Sidebar / Surface: #1F0407 (Mark LXXXV Dark Crimson)
# Cards & Panels: #2E070C (Crimson Metallic Glass)
# Accent Gold: #FFD700 (Vibrant Metallic Gold)
# Secondary Gold: #D4AF37 (Warm Gold)
# Text Primary: #FFF8E7 (Warm Pearl White)
# Text Gold: #FFD700 (Gold Highlight)

JARVIS_RED_GOLD_STYLESHEET = """
/* Global Window Background */
FluentWindow {
    background-color: #120204;
    color: #FFF8E7;
}

/* Stacked Widget Background (Content Area) */
StackedWidget {
    background-color: #120204;
    border: none;
}

/* Navigation Interface (Sidebar) */
NavigationInterface {
    background-color: #1F0407;
    border-right: 1px solid rgba(255, 215, 0, 0.3);
}

/* Cards (Surface) */
CardWidget {
    background-color: #2E070C;
    border: 1px solid rgba(255, 215, 0, 0.35);
    border-radius: 10px;
}

/* Labels */
TitleLabel, SubtitleLabel, StrongBodyLabel {
    color: #FFD700;
    font-weight: bold;
}

BodyLabel, CaptionLabel {
    color: #E5C158;
}

/* Standard QWidget containers */
QWidget#chatContent, QWidget#plannerPanel, QWidget#briefingView, QFrame#homeAutomationView {
    background-color: transparent;
}

/* List Items (Session List) */
ListWidget {
    background-color: transparent;
    border: none;
}

ListWidget::item {
    color: #E5C158;
    border-radius: 6px;
    padding: 8px;
    margin: 2px;
}

ListWidget::item:hover {
    background-color: rgba(255, 215, 0, 0.15); /* Gold tint */
    color: #FFD700;
}

ListWidget::item:selected {
    background-color: rgba(255, 215, 0, 0.25);
    color: #FFD700;
    border-left: 3px solid #FFD700;
}

/* Input Fields */
LineEdit, TextEdit, PlainTextEdit {
    background-color: #230408;
    border: 1px solid rgba(255, 215, 0, 0.4);
    border-radius: 8px;
    color: #FFF8E7;
    selection-background-color: #FFD700;
    selection-color: #120204;
}

LineEdit:focus, TextEdit:focus {
    border: 1px solid #FFD700;
    background-color: #30060B;
}

/* ScrollBars */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255, 215, 0, 0.3);
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #FFD700;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Primary Action Buttons */
QPushButton, PrimaryPushButton {
    background-color: #8B0000;
    color: #FFD700;
    border: 1px solid #FFD700;
    border-radius: 6px;
    font-weight: bold;
    padding: 6px 12px;
}

QPushButton:hover, PrimaryPushButton:hover {
    background-color: #A00000;
    color: #FFFFFF;
    border: 1px solid #FFF8E7;
}

QPushButton:pressed, PrimaryPushButton:pressed {
    background-color: #660000;
    color: #FFD700;
}
"""

AURA_STYLESHEET = JARVIS_RED_GOLD_STYLESHEET

