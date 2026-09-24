"""One semantic palette for widgets and GPU particles."""
BACKGROUND = "#0b111b"
PANEL = "#111b28"
TEXT = "#e0e8f1"
MUTED = "#8e9fb3"
ACCENT = "#70d8ce"
PROTON = (0.96, 0.43, 0.39)
NEUTRON = (0.49, 0.61, 0.76)
ELECTRON = (0.38, 0.91, 0.88)
SHELL = (0.32, 0.49, 0.64)
CATEGORIES = {
    "alkali metal": "#ce9879", "alkaline earth metal": "#c4b27a",
    "transition metal": "#7ba9c9", "post-transition metal": "#8daab4",
    "metalloid": "#9caf77", "nonmetal": "#76b99e", "halogen": "#b7a1c9",
    "noble gas": "#929dd0", "lanthanide": "#c998b4", "actinide": "#b59acf",
    "unknown": "#8b97a6",
}
STYLESHEET = f"""
QWidget {{ color: {TEXT}; background: {BACKGROUND}; font-family: 'Segoe UI'; font-size: 12px; }}
QMainWindow, QScrollArea {{ border: none; }}
QLabel {{ background: transparent; }}
QLabel#brand {{ font-size: 21px; font-weight: 700; letter-spacing: 3px; }}
QLabel#eyebrow {{ color: {ACCENT}; font-size: 10px; font-weight: 700; letter-spacing: 2px; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#title {{ font-size: 25px; font-weight: 600; }}
QLabel#symbol {{ font-size: 46px; font-weight: 600; color: {ACCENT}; }}
QFrame#panel {{ background: {PANEL}; border: 1px solid #233244; border-radius: 8px; }}
QPushButton, QComboBox, QLineEdit {{ background: #172332; border: 1px solid #2b3e50;
 border-radius: 5px; padding: 6px 10px; min-height: 20px; }}
QPushButton:hover, QComboBox:hover {{ border-color: {ACCENT}; background: #203244; }}
QPushButton:checked {{ background: #284e50; border-color: {ACCENT}; color: #c4fff3; }}
QPushButton:pressed {{ background: #315860; }}
QPushButton:disabled {{ color: #566376; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{ background: #172332; selection-background-color: #315860; }}
QCheckBox {{ spacing: 6px; background: transparent; }}
QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid #526477; border-radius: 3px; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; }}
QSplitter::handle {{ background: #1c2b3b; height: 4px; width: 4px; }}
QToolTip {{ color: {TEXT}; background: #223447; border: 1px solid #537384; padding: 5px; }}
QScrollBar:vertical {{ background: {BACKGROUND}; width: 8px; }}
QScrollBar::handle:vertical {{ background: #33495e; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QStatusBar {{ color: {MUTED}; border-top: 1px solid #233244; }}
"""
