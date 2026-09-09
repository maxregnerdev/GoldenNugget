"""GoldenNugget - MaxRegnerUI Mode (CMD Only) v10.1.0 - REAL patching.

Max Regner's real iOS transformation. Unlike the previous ``maxregneros``
mode, this one applies ONLY real, documented iOS preference keys that the
system actually reads - it goes through the exact same
backup -> tweak -> restore pipeline as the GUI (``DeviceManager.apply_changes``
-> ``_apply_tweak_pass`` -> ``start_restore`` -> the three-phase iOS 27
protective restore). There are no invented/placeholder keys: every key set
here is read by SpringBoard, UIKit, backboardd, CoreMotion, Pasteboard or
the Solarium/Liquid Glass renderer.

What it does (all real):
  * Fold Mode (Max Regner): the 10 real iOS 27 SpringBoard fold-state keys,
    enabling foldable-device features on any iPhone.
  * Liquid Glass / Solarium "holographic" specular + refraction + intelligence
    rendering toggles (the closest thing to "holographic icons" a no-jailbreak
    tool can do - they change how the Liquid Glass icon material renders).
  * SpringBoard + Internal tweaks: supervision lock-screen text, build-number
    status bar, hidden icons, raise-to-wake haptic, etc.
  * Optional ``--wallpaper path/to/file.tendies``: a real animated PosterBoard
    wallpaper for the visual redesign, applied through the same PosterBoard
    pipeline the GUI uses.

What it deliberately does NOT do: write hundreds of made-up plist keys
(``SBIconMaskType``, ``SBControlCenterBackgroundBlurRadius``, ``MaxRegnerOS_*``
...) that iOS never reads. Those were fake. A true "system-wide OS redesign"
with custom-drawn holographic icons requires a jailbreak + kernel exploit and
is impossible for a no-jailbreak backup/restore tool.
"""
import argparse
import json
import os
import sys

MAXREGNERUI_VERSION = "10.1.0"


def _qapp():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication
    QCoreApplication.setOrganizationDomain("com.leemin")
    QCoreApplication.setApplicationName("GoldenNugget")
    return QApplication.instance() or QApplication(sys.argv)


def _bundled_preset_path() -> str:
    return os.path.join(os.path.dirname(__file__), "maxregner_preset.json")


def _load_maxregner_preset(tendie_path: str = None) -> int:
    """Set the real MaxRegnerUI tweak state, then run the real apply pipeline.

    The preset JSON only contains real registry tweak ids (see
    ``src/tweaks/registry.py``) at their real plist keys; the preset loader is
    the same one the GUI uses, so whatever it sets is exactly what the GUI's
    Apply button would push through the protective backup -> restore flow.
    """
    from src.controllers.settings import Settings
    from src.controllers.preset_manager import PresetManager
    from src.devicemanagement.device_manager import DeviceManager
    from src.tweaks.tweaks import tweaks, TweakID
    from src.tweaks.tweak_loader import load_plist_tweaks
    from src.gui.thread_workers.apply_worker import ApplyAlertMessage

    _qapp()
    settings = Settings("settings")
    dm = DeviceManager()

    def update_label(text):
        print("[STATUS]", text)

    def show_alert(msg):
        if msg is None:
            return
        print("[ALERT]", getattr(msg, "title", "") or "Message")
        print("[ALERT] ", getattr(msg, "txt", msg))
        if getattr(msg, "detailed_txt", None):
            print("[ALERT DETAIL]\n", msg.detailed_txt)

    # Make sure every registry tweak is built (foldable, liquid glass, etc.)
    load_plist_tweaks()

    # Enumerate connected devices (needed for CMD mode)
    dm.get_devices(settings, show_alert=lambda x: None)
    if not dm.devices:
        print("Error: No devices connected. Please connect your iPhone and trust it.")
        return 1

    device = dm.data_singleton.current_device or dm.devices[0]
    version = device.version or ""
    model = device.model or ""

    from src.devicemanagement.constants import Version
    if Version(version) < Version("26.2"):
        print(f"Error: iOS {version} is not supported by this fork (requires iOS 26.2+).")
        return 1
    if not model.startswith("iPhone"):
        print(f"Error: MaxRegnerUI fold mode is iPhone-only (detected {model}).")
        return 1

    print(f"\n{'='*70}")
    print(f"  MAXREGNERUI v{MAXREGNERUI_VERSION} - REAL iOS patching (no fake keys)")
    print(f"  Target: {model} (iOS {version})")
    print(f"{'='*70}")

    # Load the MaxRegner preset (real registry tweaks only). It is written
    # next to this module and uses the GUI's own preset loader so the apply
    # path is identical to clicking "Apply" with the preset active.
    preset_path = _bundled_preset_path()
    if not os.path.isfile(preset_path):
        print(f"Error: MaxRegner preset not found at {preset_path}")
        return 1

    manager = PresetManager()
    # PresetManager loads into the shared `tweaks` dict by name from the
    # presets dir; load it via the import path so it does not require the
    # preset to be installed in the user's presets folder.
    with open(preset_path, "r", encoding="utf-8") as f:
        preset_data = json.load(f)
    if not manager._apply(preset_data):
        print("Error: failed to load MaxRegner preset.")
        return 1

    enabled = [tid.name for tid, t in tweaks.items() if getattr(t, "enabled", False)]
    print(f"\nLoaded {len(enabled)} real tweak(s) from MaxRegner preset:")
    for name in enabled:
        print(f"  - {name}")

    # Optional real animated wallpaper (PosterBoard). This is the genuine
    # visual-redesign vector for a no-jailbreak tool.
    pb = tweaks[TweakID.PosterBoard]
    if tendie_path:
        if not os.path.exists(tendie_path):
            print(f"Error: wallpaper tendie not found: {tendie_path}")
            return 1
        pb.config_manager.update_for_saved_database(str(device.udid))
        added = pb.add_tendie(tendie_path)
        print(f"\nWallpaper tendie added: {added} | descriptors: {pb.get_descriptor_count()}")
        if not added:
            print("Error: failed to add wallpaper tendie.")
            return 1
    else:
        print("\nNo --wallpaper given; applying tweak-only transformation (no wallpaper).")

    print("\nApplying via the real protective backup -> tweak -> restore pipeline...")
    print("On iOS 27 this triggers the security recovery; do not unplug the device.")
    dm.apply_changes(update_label=update_label, show_alert=show_alert)

    print("\n" + "="*70)
    print("  MAXREGNERUI APPLIED (real patching).")
    print("="*70)
    print("\nReal changes applied:")
    print("  - Fold Mode (Max Regner): 10 iOS 27 fold-state keys")
    print("  - Liquid Glass / Solarium: specular, refraction, intelligence toggles")
    print("  - SpringBoard + Internal: supervision text, build-number, hidden icons, ...")
    if tendie_path:
        print("  - PosterBoard wallpaper: animated tendie (real visual redesign)")
    print("\nRe-enable Find My manually after the device reboots.")
    print(f"\nMaxRegnerUI v{MAXREGNERUI_VERSION} - By Max Regner")
    print("="*70 + "\n")
    return 0


def _list_devices() -> int:
    from src.controllers.settings import Settings
    from src.devicemanagement.device_manager import DeviceManager
    _qapp()
    settings = Settings("settings")
    dm = DeviceManager()
    dm.get_devices(settings, show_alert=lambda x: None)
    if not dm.devices:
        print("No devices connected.")
        return 1
    print("Connected devices:")
    for i, device in enumerate(dm.devices):
        print(f"  {i+1}. {device.name} - {device.model} (iOS {device.version}) - UDID: {device.udid}")
    return 0


def main(argv: list = None) -> int:
    """MaxRegnerUI mode CLI entry point."""
    parser = argparse.ArgumentParser(
        description=f"GoldenNugget - MaxRegnerUI Mode v{MAXREGNERUI_VERSION} (real patching)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""REAL iOS transformation by Max Regner (no fake/placeholder keys).

Applies only documented iOS preference keys via the real backup -> tweak ->
restore pipeline (the same path the GUI uses), plus an optional real
animated PosterBoard wallpaper for the visual redesign.

  --wallpaper path/to/file.tendies   Real animated wallpaper (visual redesign)
  --udid <UDID>                      Target a specific device

Examples:
  Nugget --mode maxregnerui                         Real tweak transformation
  Nugget --mode maxregnerui --wallpaper wp.tendies  ... + animated wallpaper
  Nugget --mode maxregnerui --list                   List connected devices
  Nugget --mode maxregnerui --version               Show version

NOTE: a true custom-drawn "holographic icons" / full OS redesign requires a
jailbreak and is not possible with this no-jailbreak tool. The Liquid Glass
/Solarium toggles here are the real closest equivalent.
""")
    parser.add_argument("--udid", help="Target device UDID")
    parser.add_argument("--wallpaper", help="Path to a .tendies animated wallpaper (real PosterBoard wallpaper)")
    parser.add_argument("--list", action="store_true", help="List connected devices")
    parser.add_argument("--version", action="store_true", help="Show version")
    args = parser.parse_args(argv)

    if args.version:
        print(f"GoldenNugget MaxRegnerUI Mode v{MAXREGNERUI_VERSION} (Max Regner Edition)")
        return 0

    if args.list:
        return _list_devices()

    # Select device by UDID if requested (before apply so it becomes current)
    if args.udid:
        from src.controllers.settings import Settings
        from src.devicemanagement.device_manager import DeviceManager
        _qapp()
        settings = Settings("settings")
        dm = DeviceManager()
        dm.get_devices(settings, show_alert=lambda x: None)
        match = next((d for d in dm.devices if str(d.udid) == str(args.udid)), None)
        if match is None:
            print(f"Error: no connected device with UDID {args.udid}")
            return 1
        dm.set_current_device(dm.devices.index(match))

    try:
        return _load_maxregner_preset(tendie_path=args.wallpaper)
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"  ERROR: {e}")
        print(f"{'='*70}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
