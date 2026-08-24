"""Visual language of the JARVIS HUD: colors, fonts, glow metrics, stylesheet.

Design intent: a dark, translucent cockpit. One luminous accent (arc-reactor
cyan) carries hierarchy; gold is reserved for secondary highlights so it stays
special. Typography is monospaced throughout — readouts, chat and controls
share one voice, which is what makes the HUD read as an instrument rather
than a chat app.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QFont, QFontDatabase

from jarvis.core.config import GuiConfig

_MONO_CANDIDATES = (
    "JetBrains Mono",
    "Cascadia Code",
    "Fira Code",
    "Consolas",
    "DejaVu Sans Mono",
    "Menlo",
    "Monospace",
)


def _pick_mono_family() -> str:
    """Return the first installed monospace family from the candidate list."""
    installed = set(QFontDatabase.families())
    for family in _MONO_CANDIDATES:
        if family in installed:
            return family
    return "Monospace"


def _rgba(color: QColor, alpha: float) -> str:
    """Format a QColor as a CSS ``rgba()`` string with the given alpha (0..1)."""
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.2f})"


@dataclass(slots=True)
class Theme:
    """Resolved visual tokens for every HUD widget, built from :class:`GuiConfig`."""

    accent: QColor
    secondary: QColor
    background: QColor
    panel: QColor
    text: QColor
    text_dim: QColor
    mono_family: str
    title_font: QFont
    body_font: QFont
    small_font: QFont
    glow_radius: float
    core_glow_radius: float
    transparency: float
    fps: int

    @classmethod
    def from_config(cls, config: GuiConfig) -> Theme:
        """Build the theme from GUI configuration (dark mode only, by design)."""
        accent = QColor(config.accent_color)
        secondary = QColor(config.secondary_color)
        family = _pick_mono_family()

        title_font = QFont(family, 16)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3.0)
        title_font.setWeight(QFont.Weight.DemiBold)
        body_font = QFont(family, 10)
        small_font = QFont(family, 8)
        for font in (title_font, body_font, small_font):
            font.setStyleHint(QFont.StyleHint.Monospace)

        return cls(
            accent=accent,
            secondary=secondary,
            background=QColor(6, 10, 18),
            panel=QColor(10, 18, 30),
            text=QColor(214, 236, 248),
            text_dim=QColor(120, 150, 170),
            mono_family=family,
            title_font=title_font,
            body_font=body_font,
            small_font=small_font,
            glow_radius=18.0,
            core_glow_radius=42.0,
            transparency=config.transparency,
            fps=max(config.fps, 1),
        )

    def with_alpha(self, color: QColor, alpha: int) -> QColor:
        """Copy ``color`` with the given 0..255 alpha."""
        result = QColor(color)
        result.setAlpha(alpha)
        return result

    def stylesheet(self) -> str:
        """QSS for panels, chat bubbles and controls (translucent dark surfaces)."""
        accent = self.accent
        return f"""
        QWidget {{
            color: {_rgba(self.text, 1.0)};
            font-family: "{self.mono_family}";
            font-size: 10pt;
            background: transparent;
        }}
        QFrame#hudPanel {{
            background-color: {_rgba(self.panel, 0.72)};
            border: 1px solid {_rgba(accent, 0.35)};
            border-radius: 10px;
        }}
        QLabel#wordmark {{
            color: {_rgba(accent, 0.95)};
            font-size: 17pt;
            letter-spacing: 4px;
        }}
        QLabel#clock {{
            color: {_rgba(self.text, 0.92)};
            font-size: 13pt;
        }}
        QLabel#sectionTitle {{
            color: {_rgba(self.secondary, 0.90)};
            font-size: 8pt;
            letter-spacing: 2px;
        }}
        QLabel#dimText {{
            color: {_rgba(self.text_dim, 1.0)};
        }}
        QPlainTextEdit#activityFeed {{
            background-color: {_rgba(self.background, 0.55)};
            border: 1px solid {_rgba(accent, 0.22)};
            border-radius: 6px;
            color: {_rgba(self.text_dim, 1.0)};
            font-size: 8pt;
        }}
        QScrollArea#chatScroll {{
            border: none;
        }}
        QLabel#userBubble {{
            background-color: {_rgba(accent, 0.16)};
            border: 1px solid {_rgba(accent, 0.45)};
            border-radius: 9px;
            padding: 7px 10px;
        }}
        QLabel#assistantBubble {{
            background-color: {_rgba(self.panel, 0.85)};
            border: 1px solid {_rgba(accent, 0.20)};
            border-radius: 9px;
            padding: 7px 10px;
        }}
        QLabel#systemBubble {{
            color: {_rgba(self.secondary, 0.85)};
            font-size: 8pt;
            padding: 2px 6px;
        }}
        QLineEdit {{
            background-color: {_rgba(self.background, 0.65)};
            border: 1px solid {_rgba(accent, 0.40)};
            border-radius: 8px;
            padding: 7px 10px;
            selection-background-color: {_rgba(accent, 0.45)};
        }}
        QLineEdit:focus {{
            border: 1px solid {_rgba(accent, 0.85)};
        }}
        QPushButton {{
            background-color: {_rgba(accent, 0.18)};
            border: 1px solid {_rgba(accent, 0.55)};
            border-radius: 8px;
            padding: 7px 14px;
            color: {_rgba(self.text, 1.0)};
        }}
        QPushButton:hover {{
            background-color: {_rgba(accent, 0.32)};
        }}
        QPushButton:pressed {{
            background-color: {_rgba(accent, 0.48)};
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {_rgba(accent, 0.35)};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        QMessageBox {{
            background-color: {_rgba(self.panel, 1.0)};
        }}
        """
