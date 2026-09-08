"""Single source of truth for the plist-based tweaks - Max Regner Edition.

Only fold mode tweaks are kept. All other tweaks have been removed.
This is a CMD-only version for foldable iPhone features.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from PySide6.QtCore import QT_TRANSLATE_NOOP

from .basic_plist_locations import FileLocation
from .tweak_names import TweakID


class Section(Enum):
    INTERNAL = "Internal Options"


class Kind(Enum):
    SWITCH = "switch"   # boolean toggle
    TEXT = "text"       # free-form text value
    NUMBER = "number"   # numeric value


@dataclass(frozen=True)
class TweakSpec:
    id: TweakID
    section: Section
    title: str
    location: FileLocation
    key: str
    value: any = True          # value written when the tweak is enabled
    kind: Kind = Kind.SWITCH
    min_value: int = 0         # NUMBER kind only
    max_value: int = 999       # NUMBER kind only
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    iphone_only: bool = False
    ipad_only: bool = False
    factory: Optional[Callable[[], object]] = None  # overrides BasicPlistTweak
    description: Optional[str] = None  # detailed "what it does" tooltip
    disabled: bool = False  # True = tweak is cut off: never loaded, never applied, never rendered


def _t(id_: TweakID, section: Section, title: str, location: FileLocation,
       key: str, description: str = "", **kwargs) -> TweakSpec:
    # QT_TRANSLATE_NOOP marks the title for pyside6-lupdate; the actual
    # translation happens at render time (translators are not installed yet
    # when this module is imported).
    return TweakSpec(id=id_, section=section,
                     title=QT_TRANSLATE_NOOP("Nugget", title),
                     description=QT_TRANSLATE_NOOP("Nugget", description) if description else None,
                     location=location, key=key, **kwargs)


# FileLocation.springboard is the springboard plist
SB = FileLocation.springboard

# Max Regner's Fold Mode Tweaks - Only these remain
SPECS: tuple[TweakSpec, ...] = (
    # --- Fold Mode (Max Regner Features) ---
    _t(TweakID.SBEnableFoldMode, Section.INTERNAL, "Enable Fold Mode", SB, "SBEnableFoldMode",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables foldable iPhone mode, allowing foldable device features on any iPhone."),
       min_version="27.0", iphone_only=True),
    _t(TweakID.SBForceFoldState, Section.INTERNAL, "Force Fold State", SB, "SBForceFoldState",
       description=QT_TRANSLATE_NOOP("Nugget", "Forces the device to recognize and use fold state."),
       min_version="27.0", iphone_only=True),
    _t(TweakID.SBFoldStateValue, Section.INTERNAL, "Fold State Value", SB, "SBFoldStateValue", value=0, kind=Kind.NUMBER,
       description=QT_TRANSLATE_NOOP("Nugget", "Sets the fold state value (0=unfolded, 1=folded)."),
       min_value=0, max_value=1, min_version="27.0", iphone_only=True),
    _t(TweakID.SBEnableFlexMode, Section.INTERNAL, "Enable Flex Mode", SB, "SBEnableFlexMode",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables Flex Mode for flexible display configurations."),
       min_version="27.0", iphone_only=True),
    _t(TweakID.SBEnableMultiDisplay, Section.INTERNAL, "Enable Multi-Display", SB, "SBEnableMultiDisplay",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables multi-display support for foldable devices."),
       min_version="27.0", iphone_only=True),
    _t(TweakID.SBEnableAdaptiveMultitasking, Section.INTERNAL, "Enable Adaptive Multitasking", SB, "SBEnableAdaptiveMultitasking",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables adaptive multitasking for foldable screens."),
       min_version="27.0", iphone_only=True),
    _t(TweakID.SBEnableSplitView, Section.INTERNAL, "Enable Split View", SB, "SBEnableSplitView",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables split view mode on foldable devices."),
       min_version="27.0", iphone_only=True),
    _t(TweakID.SBEnableHingeAwareness, Section.INTERNAL, "Enable Hinge Awareness", SB, "SBEnableHingeAwareness",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables hinge angle detection and awareness."),
       min_version="27.0", iphone_only=True),
    _t(TweakID.SBMechanicalAngleDegrees, Section.INTERNAL, "Mechanical Angle Degrees", SB, "SBMechanicalAngleDegrees", value=90, kind=Kind.NUMBER,
       description=QT_TRANSLATE_NOOP("Nugget", "Sets the mechanical hinge angle in degrees."),
       min_value=0, max_value=180, min_version="27.0", iphone_only=True),
    _t(TweakID.SBEnableOptimizedWidgets, Section.INTERNAL, "Enable Optimized Widgets", SB, "SBEnableOptimizedWidgets",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables optimized widgets for foldable displays."),
       min_version="27.0", iphone_only=True),
)

SPECS_BY_SECTION = {section: [s for s in SPECS if s.section == section and not s.disabled] for section in Section}
SPECS_BY_ID = {spec.id: spec for spec in SPECS if not spec.disabled}
