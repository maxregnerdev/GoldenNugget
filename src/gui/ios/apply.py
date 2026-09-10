from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea
)
from src.gui.ios.components import IOSSectionHeader, IOSCard, IOSPrimaryButton


class IOSApplyPage(QWidget):
    """Apply page \u2014 a single Apply button. On iPhone 16e it enables the
    real fold tweaks and applies them in one click."""
    FOLD_TWEAK_IDS = (
        "SBEnableFoldMode",
        "SBForceFoldState",
        "SBEnableFlexMode",
        "SBEnableMultiDisplay",
        "SBEnableAdaptiveMultitasking",
        "SBEnableSplitView",
        "SBEnableHingeAwareness",
        "SBEnableOptimizedWidgets",
    )

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e1e; border: none;")
        content = QWidget()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 32)
        content_layout.setSpacing(8)

        content_layout.addWidget(IOSSectionHeader(
            QCoreApplication.translate("Nugget", "Apply Tweaks")))

        apply_card = IOSCard()
        apply_layout = QVBoxLayout(apply_card)
        apply_layout.setContentsMargins(16, 12, 16, 12)
        apply_layout.setSpacing(8)
        apply_desc = QLabel(QCoreApplication.translate(
            "Nugget",
            "Applies every enabled tweak to your device. The device reboots "
            "when done \u2014 remember to turn Find My back on afterwards."))
        apply_desc.setWordWrap(True)
        apply_desc.setStyleSheet("color: #8E8E93; font-size: 13px;")
        apply_layout.addWidget(apply_desc)

        self.apply_btn = IOSPrimaryButton(QCoreApplication.translate(
            "Nugget", "Apply"))
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        apply_layout.addWidget(self.apply_btn)
        content_layout.addWidget(apply_card)

        # --- Progress status ---
        content_layout.addWidget(IOSSectionHeader(
            QCoreApplication.translate("Nugget", "Progress")))
        status_card = IOSCard()
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(16, 12, 16, 12)
        status_layout.setSpacing(0)
        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        status_layout.addWidget(self.status_lbl)
        content_layout.addWidget(status_card)
        content_layout.addStretch()

    def _is_iphone_16e(self) -> bool:
        dm = self.window.device_manager
        return bool(getattr(dm, "get_current_device_is_iphone_16e", lambda: False)())

    def _on_apply_clicked(self):
        """Single Apply button. On iPhone 16e the real fold changes are
        enabled automatically, then applied in one shot."""
        from src.tweaks.tweaks import tweaks, TweakID
        from src.tweaks.tweak_loader import load_plist_tweaks

        # Ensure the registry tweaks (including the fold tweaks) are loaded.
        load_plist_tweaks()

        if self._is_iphone_16e():
            # Enable every fold tweak; set the fold-state value to unfolded.
            tweak_id_lookup = {member.name: member for member in TweakID}
            for key in self.FOLD_TWEAK_IDS:
                tid = tweak_id_lookup.get(key)
                tweak = tweaks.get(tid) if tid is not None else None
                if tweak is not None:
                    tweak.set_enabled(True)
            fold_value = tweaks.get(TweakID.SBFoldStateValue)
            if fold_value is not None:
                fold_value.set_value(0, toggle_enabled=True)
            mechanical_angle = tweaks.get(TweakID.SBMechanicalAngleDegrees)
            if mechanical_angle is not None:
                mechanical_angle.set_value(90, toggle_enabled=True)

        # Apply all enabled tweaks (the standard apply flow).
        self.window.on_applyTweaksBtn_clicked()

    def set_status(self, text: str):
        self.status_lbl.setText(text or "")

    def set_busy(self, busy: bool):
        self.apply_btn.setEnabled(not busy)

