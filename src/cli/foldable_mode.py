"""GoldenNugget - Foldable iPhone Mode (CMD Only) v10.0.0

Max Regner's foldable iPhone feature implementation.
This is a command-line only mode that enables foldable iPhone features on ANY iPhone.
All foldable features are enabled automatically.
"""

import argparse
import sys
from src.devicemanagement.device_manager import DeviceManager


def apply_foldable_tweaks(dm: DeviceManager, udid: str = None) -> int:
    """Apply all foldable iPhone tweaks to the connected device."""
    try:
        # Get current device from data_singleton
        if udid:
            # Find device by UDID
            device = next((d for d in dm.devices if str(d.udid) == str(udid)), None)
        else:
            device = dm.data_singleton.current_device
        
        if not device:
            print("Error: No device connected. Please connect an iPhone.")
            return 1
        
        version = device.version
        model = device.model
        
        # Check if device is iPhone on iOS 27+
        if not model or not model.startswith("iPhone"):
            print("Error: Foldable mode only works on iPhones.")
            return 1
        
        from src.devicemanagement.constants import Version
        if Version(version) < Version("27.0"):
            print(f"Error: iOS {version} not supported. Foldable mode requires iOS 27.0+.")
            return 1
        
        print(f"Applying foldable tweaks to {model} ({version})...")
        
        # Max Regner's foldable features - write directly to springboard plist
        from src.controllers.plist_handler import PlistHandler
        ph = PlistHandler(dm)
        
        springboard_path = "/var/Managed Preferences/mobile/com.apple.springboard.plist"
        
        foldable_tweaks = {
            "SBEnableFoldMode": True,
            "SBForceFoldState": True,
            "SBFoldStateValue": 0,
            "SBEnableFlexMode": True,
            "SBEnableMultiDisplay": True,
            "SBEnableAdaptiveMultitasking": True,
            "SBEnableSplitView": True,
            "SBEnableHingeAwareness": True,
            "SBMechanicalAngleDegrees": 90,
            "SBEnableOptimizedWidgets": True,
        }
        
        # Read existing plist
        try:
            existing = ph.read_plist(springboard_path)
        except Exception:
            existing = {}
        
        # Merge foldable tweaks
        existing.update(foldable_tweaks)
        
        # Write back
        ph.write_plist(springboard_path, existing)
        print("Foldable tweaks applied successfully!")
        print("Reboot your device for changes to take effect.")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main(argv: list = None) -> int:
    """Foldable mode CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GoldenNugget - Foldable iPhone Mode (Max Regner Features)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Nugget --mode foldable           Apply foldable tweaks to connected device
  Nugget --mode foldable --udid <UDID>  Apply to specific device
        """
    )
    parser.add_argument("--udid", help="Target device UDID")
    parser.add_argument("--list", action="store_true", help="List connected devices")
    parser.add_argument("--version", action="store_true", help="Show version")
    
    args = parser.parse_args(argv)
    
    if args.version:
        print("GoldenNugget Foldable Mode v10.0.0 (Max Regner Edition)")
        return 0
    
    dm = DeviceManager()
    
    if args.list:
        devices = dm.devices
        if not devices:
            print("No devices connected.")
            return 1
        print("Connected devices:")
        for i, device in enumerate(devices):
            print(f"  {i+1}. {device.name} - {device.model} (iOS {device.version}) - UDID: {device.udid}")
        return 0
    
    return apply_foldable_tweaks(dm, args.udid)


if __name__ == "__main__":
    sys.exit(main())
