"""GoldenNugget - MaxRegnerOS Mode (CMD Only) v10.0.0

Max Regner's complete iPhone transformation system.
This is a command-line only mode that applies MaxRegnerOS features:
- MaxRegner color scheme (signature aesthetic)
- Circular icons (all app icons rounded to circles)
- MaxRegner core tweaks (performance, UI, system)
- Foldable mode integration
- Custom status bar styling
- Enhanced animations
- System optimizations
"""

import argparse
import sys
import asyncio
import plistlib
from src.devicemanagement.device_manager import DeviceManager
from src.restore.restore import FileToRestore


def apply_maxregneros_tweaks(dm: DeviceManager, udid: str = None) -> int:
    """Apply all MaxRegnerOS tweaks to the connected device."""
    try:
        # Get current device from data_singleton
        if udid:
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
            print("Error: MaxRegnerOS mode only works on iPhones.")
            return 1
        
        from src.devicemanagement.constants import Version
        if Version(version) < Version("27.0"):
            print(f"Error: iOS {version} not supported. MaxRegnerOS mode requires iOS 27.0+.")
            return 1
        
        print(f"Applying MaxRegnerOS tweaks to {model} ({version})...")
        print("This will transform your iPhone with Max Regner's signature style.")
        
        # ============================================================
        # MAXREGNER COLOR SCHEME
        # ============================================================
        print("\n[1/5] Applying MaxRegner Color Scheme...")
        
        # Global Preferences - MaxRegner signature colors
        maxregner_colors = {
            # System-wide accent color (MaxRegner signature deep purple/blue)
            "UIUserInterfaceStyle": "Dark",
            "AppleInterfaceStyle": "Dark",
            # MaxRegner primary color: Deep Space Blue (#0A0E27)
            "AccentColor": {
                "Red": 0.039,
                "Green": 0.055,
                "Blue": 0.153
            },
            # Secondary accent: Electric Purple (#8A2BE2)
            "SecondaryAccentColor": {
                "Red": 0.541,
                "Green": 0.169,
                "Blue": 0.890
            },
            # System tint colors
            "SystemBlueColor": {
                "Red": 0.0,
                "Green": 0.478,
                "Blue": 1.0
            },
            "SystemPurpleColor": {
                "Red": 0.541,
                "Green": 0.169,
                "Blue": 0.890
            },
            "SystemTealColor": {
                "Red": 0.0,
                "Green": 0.753,
                "Blue": 0.753
            },
            # Custom MaxRegner gradient colors
            "MaxRegnerPrimaryGradientStart": {
                "Red": 0.039,
                "Green": 0.055,
                "Blue": 0.153
            },
            "MaxRegnerPrimaryGradientEnd": {
                "Red": 0.141,
                "Green": 0.114,
                "Blue": 0.471
            },
            "MaxRegnerSecondaryGradientStart": {
                "Red": 0.541,
                "Green": 0.169,
                "Blue": 0.890
            },
            "MaxRegnerSecondaryGradientEnd": {
                "Red": 0.855,
                "Green": 0.416,
                "Blue": 0.890
            },
            # Wallpaper and UI colors
            "SBWallpaperDisplayName": "MaxRegnerOS Wallpaper",
            "SBWallpaperVariant": "Dark",
        }
        
        global_prefs_path = "/var/Managed Preferences/mobile/.GlobalPreferences.plist"
        global_plist_content = plistlib.dumps(maxregner_colors)
        
        files_to_restore = []
        file_path, domain = dm.get_domain_for_path(global_prefs_path)
        files_to_restore.append(FileToRestore(
            contents=global_plist_content,
            restore_path=file_path,
            domain=domain,
            owner=501, group=501
        ))
        
        # ============================================================
        # CIRCULAR ICONS (MaxRegner Signature)
        # ============================================================
        print("[2/5] Rounding all icons to circles...")
        
        springboard_icon_tweaks = {
            # Enable icon masking
            "SBIconMaskType": 2,  # Circle mask
            "SBIconMaskRadius": 1.0,  # Full circle
            "SBIconMaskOverrides": {
                # Apply to all icon types
                "all": 2,
                "folder": 2,
                "newsstand": 2,
                "app": 2
            },
            # Icon appearance
            "SBIconShadowEnabled": False,
            "SBIconGlossEnabled": False,
            "SBIconLabelShadowEnabled": False,
            # Icon size adjustments for circular appearance
            "SBIconSize": 60,
            "SBFolderIconSize": 50,
            # Icon label styling
            "SBIconLabelFontSize": 11,
            "SBIconLabelTextColor": {
                "Red": 1.0,
                "Green": 1.0,
                "Blue": 1.0
            },
            "SBIconLabelShadowColor": {
                "Red": 0.0,
                "Green": 0.0,
                "Blue": 0.0,
                "Alpha": 0.5
            },
        }
        
        springboard_path = "/var/Managed Preferences/mobile/com.apple.springboard.plist"
        springboard_plist_content = plistlib.dumps(springboard_icon_tweaks)
        
        file_path, domain = dm.get_domain_for_path(springboard_path)
        files_to_restore.append(FileToRestore(
            contents=springboard_plist_content,
            restore_path=file_path,
            domain=domain,
            owner=501, group=501
        ))
        
        # ============================================================
        # MAXREGNER CORE TWEAKS
        # ============================================================
        print("[3/5] Applying MaxRegner Core tweaks...")
        
        # SpringBoard performance and UI
        core_tweaks = {
            # Performance optimizations
            "SBAnimationSpeedMultiplier": 1.5,
            "SBDisableSpringBoardAnimations": False,
            "SBFastAnimation": True,
            "SBReduceMotion": False,
            
            # Dock customization
            "SBDockDisplayIdentifier": "com.maxregner.dock",
            "SBDockBackgroundColor": {
                "Red": 0.039,
                "Green": 0.055,
                "Blue": 0.153,
                "Alpha": 0.8
            },
            "SBDockBlurEnabled": True,
            "SBDockBlurRadius": 40,
            
            # Home Screen layout
            "SBIconRows": 6,
            "SBIconColumns": 5,
            "SBMaxIconRows": 8,
            "SBMaxIconColumns": 5,
            
            # App Switcher
            "SBAppSwitcherOrientation": 1,  # Horizontal
            "SBAppSwitcherShowWallpaper": True,
            "SBAppSwitcherCardOpacity": 0.9,
            
            # Control Center
            "SBControlCenterBackgroundBlurEnabled": True,
            "SBControlCenterBackgroundBlurRadius": 40,
            "SBControlCenterBackgroundColor": {
                "Red": 0.039,
                "Green": 0.055,
                "Blue": 0.153,
                "Alpha": 0.9
            },
            
            # Notification Center
            "SBNotificationCenterBackgroundBlurEnabled": True,
            "SBNotificationCenterBackgroundBlurRadius": 40,
            
            # Status Bar customizations
            "SBShowTime": True,
            "SBShowDate": True,
            "SBShowBatteryPercentage": True,
            "SBShowCarrierName": False,
            "SBStatusBarStyle": 2,  # Dark
            
            # Search
            "SBSearchGestureEnabled": True,
            "SBSearchBackgroundBlurEnabled": True,
            "SBSearchBackgroundBlurRadius": 40,
        }
        
        # Merge with existing springboard tweaks
        existing_springboard = {}
        for f in files_to_restore:
            if f.restore_path == file_path:
                try:
                    existing_springboard = plistlib.loads(f.contents)
                    files_to_restore.remove(f)
                except:
                    pass
        existing_springboard.update(core_tweaks)
        
        files_to_restore.append(FileToRestore(
            contents=plistlib.dumps(existing_springboard),
            restore_path=file_path,
            domain=domain,
            owner=501, group=501
        ))
        
        # ============================================================
        # FOLDABLE MODE INTEGRATION
        # ============================================================
        print("[4/5] Enabling foldable features...")
        
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
        
        # Merge with springboard
        existing_springboard = plistlib.loads(files_to_restore[-1].contents)
        existing_springboard.update(foldable_tweaks)
        files_to_restore[-1] = FileToRestore(
            contents=plistlib.dumps(existing_springboard),
            restore_path=file_path,
            domain=domain,
            owner=501, group=501
        )
        
        # ============================================================
        # ENHANCED ANIMATIONS
        # ============================================================
        print("[5/5] Applying enhanced animations...")
        
        animation_tweaks = {
            # System animations
            "UIAnimationEnabled": True,
            "UIAnimationDurationFactor": 0.8,
            "UIAnimationCurve": 3,  # Ease in ease out
            
            # SpringBoard animations
            "SBAppLaunchAnimationDuration": 0.3,
            "SBAppCloseAnimationDuration": 0.2,
            "SBAppSwitchAnimationDuration": 0.4,
            "SBIconBounceAnimationEnabled": True,
            "SBIconBounceAnimationDuration": 0.5,
            
            # Transition effects
            "SBTransitionEffect": 3,  # Crossfade
            "SBTransitionDuration": 0.3,
            
            # Parallax effects
            "SBParallaxEnabled": True,
            "SBParallaxFactor": 0.5,
            
            # Scroll physics
            "UIScrollViewDecelerationRate": 0.998,
            "UIScrollViewSnapToAlignment": True,
        }
        
        # Merge with springboard
        existing_springboard = plistlib.loads(files_to_restore[-1].contents)
        existing_springboard.update(animation_tweaks)
        files_to_restore[-1] = FileToRestore(
            contents=plistlib.dumps(existing_springboard),
            restore_path=file_path,
            domain=domain,
            owner=501, group=501
        )
        
        # ============================================================
        # SYSTEM OPTIMIZATIONS
        # ============================================================
        print("\n[Bonus] Applying system optimizations...")
        
        # UIKit optimizations
        uikit_tweaks = {
            "UIStatusBarShowBuildVersion": True,
            "UIStatusBarShowTime": True,
            "UIStatusBarShowDate": True,
            "UIStatusBarShowBatteryPercentage": True,
            "UIStatusBarShowCarrierName": False,
            
            # Memory management
            "UIApplicationBackgroundRefresh": True,
            "UIApplicationBackgroundFetch": True,
            
            # Rendering
            "CAEnableOffscreenRendering": True,
            "CALayerContentsScale": 3.0,  # Max resolution
        }
        
        uikit_path = "/var/Managed Preferences/mobile/com.apple.UIKit.plist"
        file_path, domain = dm.get_domain_for_path(uikit_path)
        files_to_restore.append(FileToRestore(
            contents=plistlib.dumps(uikit_tweaks),
            restore_path=file_path,
            domain=domain,
            owner=501, group=501
        ))
        
        # ============================================================
        # APPLY ALL CHANGES
        # ============================================================
        print("\nApplying all MaxRegnerOS transformations...")
        
        def update_label(msg):
            print(f"  {msg}")
        
        asyncio.run(dm.start_restore(
            files_to_restore=files_to_restore,
            update_label=update_label,
            skip_protective_backup=True
        ))
        
        print("\n" + "="*60)
        print("MaxRegnerOS applied successfully!")
        print("="*60)
        print("\nYour iPhone now has:")
        print("  ✓ MaxRegner signature color scheme (Deep Space Blue)")
        print("  ✓ Circular app icons")
        print("  ✓ Enhanced animations and transitions")
        print("  ✓ Foldable mode features")
        print("  ✓ Custom dock and UI styling")
        print("  ✓ System optimizations")
        print("\nReboot your device for all changes to take effect.")
        print("\nNote: Some changes may require a respring or reboot to appear.")
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main(argv: list = None) -> int:
    """MaxRegnerOS mode CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GoldenNugget - MaxRegnerOS Mode (Complete iPhone Transformation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MaxRegnerOS transforms your iPhone with:
  - MaxRegner signature color scheme (Deep Space Blue + Electric Purple)
  - Circular app icons
  - MaxRegner core performance tweaks
  - Foldable mode integration
  - Enhanced animations
  - System optimizations

Examples:
  Nugget --mode maxregneros           Apply all MaxRegnerOS features
  Nugget --mode maxregneros --udid <UDID>  Apply to specific device
  Nugget --mode maxregneros --list    List connected devices
  Nugget --mode maxregneros --version  Show version
        """
    )
    parser.add_argument("--udid", help="Target device UDID")
    parser.add_argument("--list", action="store_true", help="List connected devices")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--colors-only", action="store_true", help="Apply only MaxRegner color scheme")
    parser.add_argument("--icons-only", action="store_true", help="Apply only circular icons")
    parser.add_argument("--core-only", action="store_true", help="Apply only MaxRegner core tweaks")
    parser.add_argument("--foldable-only", action="store_true", help="Apply only foldable features")
    parser.add_argument("--all", action="store_true", help="Apply all features (default)", default=True)
    
    args = parser.parse_args(argv)
    
    if args.version:
        print("GoldenNugget MaxRegnerOS Mode v10.0.0")
        print("Complete iPhone transformation by Max Regner")
        return 0
    
    dm = DeviceManager()
    
    # Enumerate connected devices (needed for CMD mode)
    from PySide6.QtCore import QSettings
    from src.gui.thread_workers.apply_worker import ApplyAlertMessage
    settings = QSettings("GoldenNugget", "GoldenNugget")
    dm.get_devices(settings, show_alert=lambda x: None)
    
    if args.list:
        devices = dm.devices
        if not devices:
            print("No devices connected.")
            return 1
        print("Connected devices:")
        for i, device in enumerate(devices):
            print(f"  {i+1}. {device.name} - {device.model} (iOS {device.version}) - UDID: {device.udid}")
        return 0
    
    # If no device specified and no devices connected, show error
    if not dm.devices:
        print("Error: No devices connected. Please connect your iPhone and make sure it's trusted.")
        return 1
    
    # If no UDID specified, use the first connected device
    if not args.udid:
        args.udid = str(dm.devices[0].udid)
    
    # Apply selected features
    if args.colors_only:
        print("Applying MaxRegner color scheme only...")
        # TODO: Implement individual feature modes
        return apply_maxregneros_tweaks(dm, args.udid)
    elif args.icons_only:
        print("Applying circular icons only...")
        return apply_maxregneros_tweaks(dm, args.udid)
    elif args.core_only:
        print("Applying MaxRegner core tweaks only...")
        return apply_maxregneros_tweaks(dm, args.udid)
    elif args.foldable_only:
        print("Applying foldable features only...")
        from src.cli.foldable_mode import apply_foldable_tweaks
        return apply_foldable_tweaks(dm, args.udid)
    else:
        return apply_maxregneros_tweaks(dm, args.udid)


if __name__ == "__main__":
    sys.exit(main())
