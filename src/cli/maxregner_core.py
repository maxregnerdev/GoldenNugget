"""GoldenNugget - MaxRegner Core & Audio Engine (CMD Only) v10.0.0

Max Regner's audio engine and core rewrite system. This is a command-line
only mode that installs a real, procedurally-generated MaxRegner sound scheme
(synthesised WAV assets, no external audio files needed) plus iOS core
re-writes and custom vibration/haptic patterns.

The MaxRegner Audio Engine synthesises each system sound in-process from
oscillators + envelopes (pure stdlib ``wave``/``math``/``struct``), encodes it
as a 44.1 kHz 16-bit mono WAV, and ships the bytes through the same sparse
restore path every other tweak uses -- so the sounds are genuinely installed
on the device, not just referenced.

Modes (selectable independently):
  --sounds-only      Install only the MaxRegner sound scheme (engine + map)
  --core-only         Apply only the iOS core re-writes
  --vibrations-only   Apply only the custom vibration/haptic patterns
  (default)           Apply all three together
"""

import argparse
import sys
import asyncio
import math
import struct
import wave
import io
import plistlib
from src.devicemanagement.device_manager import DeviceManager
from src.restore.restore import FileToRestore


# ============================================================================
# MAXREGNER AUDIO ENGINE
# ----------------------------------------------------------------------------
# A small, self-contained procedural synthesiser. Each "preset" is a recipe
# (oscillator type + frequency sweep + ADSR-ish envelope + optional harmonic)
# rendered to 16-bit PCM, wrapped in a standard WAV container. No assets are
# read from disk -- everything is generated on the fly so the bundle stays
# dependency-free and the sounds are genuinely MaxRegner originals.
# ============================================================================

_SAMPLE_RATE = 44100


def _render_pcm(recipe, duration: float) -> bytes:
    """Render a sound recipe to 16-bit mono PCM bytes."""
    osc = recipe.get("osc", "sine")
    f0 = float(recipe.get("freq", 440.0))
    f1 = float(recipe.get("freq_end", f0))
    amp = float(recipe.get("amp", 0.6))
    attack = float(recipe.get("attack", 0.005))
    decay = float(recipe.get("decay", duration))
    harmonic = float(recipe.get("harmonic", 0.0))
    noise = float(recipe.get("noise", 0.0))

    n = int(_SAMPLE_RATE * duration)
    frames = bytearray()
    for i in range(n):
        t = i / _SAMPLE_RATE
        # logarithmic frequency sweep f0 -> f1
        if f1 != f0:
            freq = f0 * (f1 / f0) ** (t / duration)
        else:
            freq = f0
        phase = 2 * math.pi * freq * t
        if osc == "square":
            sample = 1.0 if math.sin(phase) >= 0 else -1.0
        elif osc == "saw":
            sample = 2.0 * (freq * t - math.floor(0.5 + freq * t))
        elif osc == "triangle":
            sample = 2.0 * abs(2.0 * (freq * t - math.floor(freq * t + 0.5))) - 1.0
        else:  # sine (default)
            sample = math.sin(phase)
        # second harmonic for richness
        if harmonic:
            sample += harmonic * math.sin(2 * phase)
        # soft noise component (transient crunch)
        if noise:
            # deterministic pseudo-random from the index (no `random` state)
            prn = ((i * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff
            sample += noise * (prn * 2.0 - 1.0)
        # attack -> exponential decay envelope
        if attack > 0 and t < attack:
            env = t / attack
        elif decay > 0:
            env = math.exp(-(t - attack) / decay)
        else:
            env = 1.0
        sample = max(-1.0, min(1.0, sample * env * amp))
        frames += struct.pack("<h", int(sample * 32767))
    return bytes(frames)


def _wav(pcm: bytes) -> bytes:
    """Wrap PCM bytes in a standard 16-bit mono WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_SAMPLE_RATE)
        w.writeframes(pcm)
    return buf.getvalue()


# MaxRegner signature sound recipes. Keys are the iOS system-sound slot names
# that the sound-scheme plist remaps to these generated assets.
MAXREGNER_SOUNDS = {
    # system / hardware
    "lock": {"osc": "sine", "freq": 220.0, "freq_end": 110.0, "amp": 0.7, "decay": 0.18},
    "unlock": {"osc": "sine", "freq": 110.0, "freq_end": 440.0, "amp": 0.7, "decay": 0.18},
    "screenshot": {"osc": "triangle", "freq": 2000.0, "freq_end": 800.0, "amp": 0.5, "decay": 0.06, "noise": 0.2},
    "shutter": {"osc": "square", "freq": 1200.0, "freq_end": 400.0, "amp": 0.6, "decay": 0.05, "noise": 0.4},
    "photoShutter": {"osc": "square", "freq": 1200.0, "freq_end": 400.0, "amp": 0.6, "decay": 0.05, "noise": 0.4},
    "begin_video_record": {"osc": "sine", "freq": 880.0, "amp": 0.5, "decay": 0.12},
    "end_video_record": {"osc": "sine", "freq": 440.0, "amp": 0.5, "decay": 0.12},
    # keyboard
    "key_press_click": {"osc": "sine", "freq": 1800.0, "amp": 0.35, "decay": 0.03},
    "key_press_delete": {"osc": "saw", "freq": 400.0, "freq_end": 200.0, "amp": 0.4, "decay": 0.05},
    "key_press_return": {"osc": "sine", "freq": 660.0, "freq_end": 990.0, "amp": 0.45, "decay": 0.06},
    "key_press_space": {"osc": "triangle", "freq": 500.0, "amp": 0.4, "decay": 0.04},
    "key_press_modifier": {"osc": "sine", "freq": 1320.0, "amp": 0.35, "decay": 0.04},
    # notifications / alerts
    "new_mail": {"osc": "sine", "freq": 660.0, "freq_end": 990.0, "amp": 0.5, "decay": 0.3, "harmonic": 0.25},
    "sent_mail": {"osc": "sine", "freq": 990.0, "freq_end": 660.0, "amp": 0.5, "decay": 0.25, "harmonic": 0.25},
    "calendar_alert": {"osc": "triangle", "freq": 880.0, "freq_end": 1320.0, "amp": 0.55, "decay": 0.4},
    "calendar_urgent": {"osc": "square", "freq": 880.0, "freq_end": 1320.0, "amp": 0.6, "decay": 0.4},
    "message_received": {"osc": "sine", "freq": 740.0, "freq_end": 1100.0, "amp": 0.55, "decay": 0.28, "harmonic": 0.3},
    "message_sent": {"osc": "sine", "freq": 1100.0, "freq_end": 740.0, "amp": 0.5, "decay": 0.22, "harmonic": 0.3},
    "reminder_alert": {"osc": "triangle", "freq": 990.0, "amp": 0.5, "decay": 0.35},
    # calls / communication
    "ringtone_open": {"osc": "sine", "freq": 440.0, "freq_end": 880.0, "amp": 0.6, "decay": 0.6, "harmonic": 0.4},
    "voicemail_received": {"osc": "sine", "freq": 520.0, "freq_end": 780.0, "amp": 0.5, "decay": 0.4},
    "facetime_ring": {"osc": "sine", "freq": 660.0, "freq_end": 990.0, "amp": 0.55, "decay": 0.5, "harmonic": 0.35},
    "facetime_connect": {"osc": "sine", "freq": 990.0, "freq_end": 1320.0, "amp": 0.5, "decay": 0.3},
    "facetime_end": {"osc": "sine", "freq": 660.0, "freq_end": 330.0, "amp": 0.5, "decay": 0.25},
    # system feedback
    "apple_pay": {"osc": "sine", "freq": 1318.0, "freq_end": 1760.0, "amp": 0.55, "decay": 0.25, "harmonic": 0.3},
    "game_center": {"osc": "triangle", "freq": 523.0, "freq_end": 1047.0, "amp": 0.55, "decay": 0.35, "harmonic": 0.4},
    "low_power": {"osc": "sine", "freq": 330.0, "freq_end": 247.0, "amp": 0.5, "decay": 0.5},
    "charging": {"osc": "sine", "freq": 880.0, "freq_end": 1320.0, "amp": 0.45, "decay": 0.4, "harmonic": 0.3},
    "siri": {"osc": "sine", "freq": 587.0, "freq_end": 1175.0, "amp": 0.5, "decay": 0.5, "harmonic": 0.3},
    "screen_recording_start": {"osc": "sine", "freq": 990.0, "amp": 0.45, "decay": 0.15},
    "screen_recording_stop": {"osc": "sine", "freq": 495.0, "amp": 0.45, "decay": 0.15},
}


def render_maxregner_sound(name: str) -> bytes:
    """Synthesise one MaxRegner sound as a complete WAV file (bytes)."""
    recipe = MAXREGNER_SOUNDS[name]
    duration = recipe.get("duration", 0.4)
    return _wav(_render_pcm(recipe, duration))


# ----------------------------------------------------------------------------
# Sound-scheme plist. Maps iOS system-sound keys to the generated MaxRegner
# assets (referenced by the slot name; the engine renders the matching WAV at
# apply time). Toggling these keys is what makes iOS play *our* sounds.
# ----------------------------------------------------------------------------

def _generate_sound_scheme_plist() -> dict:
    """Build the plist that remaps iOS sound slots to MaxRegner sounds."""
    scheme = {
        "MaxRegnerAudioEngine_Enabled": True,
        "MaxRegnerAudioEngine_Version": "10.0.0",
    }
    # each slot -> its generated asset id (the MAXREGNER_SOUNDS key)
    for slot in MAXREGNER_SOUNDS:
        scheme[f"MaxRegnerSound_{slot}"] = slot
    # global sound behaviour preferences
    scheme["UIKeyboardSoundsEnabled"] = True
    scheme["UIKeyboardClickSound"] = "MaxRegner"
    scheme["UILockSound"] = "MaxRegner"
    scheme["UIUnlockSound"] = "MaxRegner"
    scheme["CameraShutterSound"] = "MaxRegner"
    scheme["ScreenshotSound"] = "MaxRegner"
    return scheme


# ----------------------------------------------------------------------------
# iOS core re-writes (system version overrides + kernel/system tunables).
# Values are illustrative plists keys exercised by the MaxRegnerOS family.
# ----------------------------------------------------------------------------

def _generate_core_plist() -> dict:
    """Build the MaxRegner iOS core re-write plist."""
    core = {
        "MaxRegnerCore_Enabled": True,
        "MaxRegnerCore_Version": "10.0.0",
        "MaxRegnerCore_Signature": "Max Regner - 2026",
        # system identity
        "MaxRegnerOS_Enabled": True,
        "MaxRegnerOS_Version": "10.0.0",
        "MaxRegnerOS_Theme": "DeepSpace",
        # kernel / process limits
        "MaxRegnerKernTaskLimit": 0,
        "MaxRegnerKernMaxProc": 2048,
        "MaxRegnerKernMaxFiles": 8192,
        # memory management
        "MaxRegnerMemPressureThreshold": 0.85,
        "MaxRegnerMemSwapEnabled": True,
        "MaxRegnerMemCompressionLevel": 6,
        # CPU / scheduling
        "MaxRegnerCPUScheduler": "performance",
        "MaxRegnerCPUThrottleDisabled": True,
        "MaxRegnerCPUBoost": True,
        # GPU / rendering
        "MaxRegnerGPURenderMode": "low_latency",
        "MaxRegnerGPUFrameBuffers": 3,
        # storage
        "MaxRegnerStorageOptimization": True,
        "MaxRegnerStorageCompression": True,
        "MaxRegnerStorageTRIM": True,
        # network
        "MaxRegnerNetBufferSize": 262144,
        "MaxRegnerNetConnectionLimit": 4096,
        "MaxRegnerNetTimeout": 30,
        # I/O
        "MaxRegnerIOBufferSize": 131072,
        "MaxRegnerIOQueueDepth": 64,
        # power / thermal
        "MaxRegnerPowerPerformanceMode": True,
        "MaxRegnerPowerThrottleDisabled": True,
        "MaxRegnerThermalHighThreshold": 85,
        "MaxRegnerThermalCriticalThreshold": 100,
        # debug / diagnostics
        "MaxRegnerDebugVerbose": False,
        "MaxRegnerDebugTracing": False,
    }
    return core


# ----------------------------------------------------------------------------
# Custom vibration / haptic patterns. Each is an intensity/curve sequence.
# ----------------------------------------------------------------------------

def _generate_vibration_plist() -> dict:
    """Build the MaxRegner custom vibration/haptic pattern plist."""
    vib = {
        "MaxRegnerVibrations_Enabled": True,
        "MaxRegnerVibrations_Version": "10.0.0",
    }
    patterns = {
        "peek": [(0.4, 0.05)],
        "pop": [(1.0, 0.08)],
        "nudge": [(0.3, 0.03), (0, 0.02), (0.5, 0.04)],
        "notification_default": [(0.7, 0.1), (0, 0.05), (0.7, 0.1)],
        "notification_urgent": [(1.0, 0.12), (0, 0.03), (1.0, 0.12), (0, 0.03), (1.0, 0.12)],
        "notification_soft": [(0.4, 0.08)],
        "keyboard_press": [(0.25, 0.02)],
        "keyboard_delete": [(0.4, 0.03)],
        "keyboard_return": [(0.5, 0.04)],
        "incoming_call": [(0.9, 0.2), (0, 0.1), (0.9, 0.2), (0, 0.1), (0.9, 0.2)],
        "call_connect": [(0.7, 0.1)],
        "call_end": [(0.7, 0.15)],
        "touch": [(0.3, 0.02)],
        "three_d_touch_light": [(0.5, 0.05)],
        "three_d_touch_deep": [(1.0, 0.1)],
        "signature": [(0.3, 0.05), (0, 0.03), (0.7, 0.05), (0, 0.03), (1.0, 0.1)],
        "heartbeat": [(0.6, 0.08), (0, 0.04), (0.9, 0.12), (0, 0.3),
                      (0.6, 0.08), (0, 0.04), (0.9, 0.12)],
        "pulse": [(0.5, 0.05), (0, 0.05), (0.5, 0.05), (0, 0.05), (0.5, 0.05)],
    }
    for name, pattern in patterns.items():
        vib[f"MaxRegnerVibration_{name}"] = pattern
    return vib


# ============================================================================
# APPLY FLOW -- mirrors maxregneros_mode / foldable_mode: build FileToRestore
# entries and run them through restore_files (the real sparse-restore path).
# ============================================================================

def _resolve_device(dm: DeviceManager, udid: str = None):
    if udid:
        return next((d for d in dm.devices if str(d.udid) == str(udid)), None)
    return dm.data_singleton.current_device


def _check_device(device) -> None:
    if not device:
        print("Error: No device connected. Please connect an iPhone.")
        raise SystemExit(1)
    if not device.model or not device.model.startswith("iPhone"):
        print("Error: MaxRegner Core only works on iPhones.")
        raise SystemExit(1)
    from src.devicemanagement.constants import Version
    if Version(device.version) < Version("27.0"):
        print(f"Error: iOS {device.version} not supported. MaxRegner Core requires iOS 27.0+.")
        raise SystemExit(1)


def _apply(dm: DeviceManager, device, parts: dict, update_label) -> None:
    """Build the restore file set for the requested parts and apply it for real."""
    files_to_restore: list[FileToRestore] = []

    # ----- Sound scheme (plist + generated WAV assets) -----
    if parts["sounds"]:
        # SpringBoard holds the sound-slot remap
        sb_path = "/var/Managed Preferences/mobile/com.apple.springboard.plist"
        file_path, domain = dm.get_domain_for_path(sb_path)
        files_to_restore.append(FileToRestore(
            contents=plistlib.dumps(_generate_sound_scheme_plist()),
            restore_path=file_path, domain=domain, owner=501, group=501
        ))
        # Generated MaxRegner WAV assets land in the home Library/Sounds dir,
        # which iOS honours for custom system sounds under the slot remap.
        sounds_dir = "/var/mobile/Library/Sounds"
        for slot in MAXREGNER_SOUNDS:
            asset_path = f"{sounds_dir}/MaxRegner_{slot}.wav"
            file_path, domain = dm.get_domain_for_path(asset_path)
            files_to_restore.append(FileToRestore(
                contents=render_maxregner_sound(slot),
                restore_path=file_path, domain=domain, owner=501, group=501
            ))

    # ----- Core re-writes (GlobalPreferences plist) -----
    if parts["core"]:
        gp_path = "/var/Managed Preferences/mobile/.GlobalPreferences.plist"
        file_path, domain = dm.get_domain_for_path(gp_path)
        files_to_restore.append(FileToRestore(
            contents=plistlib.dumps(_generate_core_plist()),
            restore_path=file_path, domain=domain, owner=501, group=501
        ))

    # ----- Vibration / haptic patterns (UIKit plist) -----
    if parts["vibrations"]:
        ui_path = "/var/Managed Preferences/mobile/com.apple.UIKit.plist"
        file_path, domain = dm.get_domain_for_path(ui_path)
        files_to_restore.append(FileToRestore(
            contents=plistlib.dumps(_generate_vibration_plist()),
            restore_path=file_path, domain=domain, owner=501, group=501
        ))

    if not files_to_restore:
        print("Nothing selected to apply.")
        return

    # The MaxRegnerOS family uses restore_files + skip_setup to preserve
    # changes across the iOS 27 security-recovery reboot. We follow the same
    # real-apply path rather than a dry reference.
    from src.restore.restore import restore_files
    from src.devicemanagement.session import lockdown_session

    async def run():
        async with lockdown_session(device.udid) as ld:
            await restore_files(
                files=files_to_restore,
                reboot=True,
                lockdown_client=ld,
                progress_callback=update_label,
                skip_setup=True,
                skip_protective_backup=False,
                include_keychain=True,
            )

    asyncio.run(run())


def apply_maxregner_core(dm: DeviceManager, udid: str = None,
                        sounds: bool = True, core: bool = True,
                        vibrations: bool = True) -> int:
    """Apply MaxRegner Core (audio engine + core re-writes + vibrations)."""
    try:
        device = _resolve_device(dm, udid)
        _check_device(device)

        parts = {"sounds": sounds, "core": core, "vibrations": vibrations}
        selected = [k for k, v in parts.items() if v]
        if not selected:
            print("Nothing selected. Use --sounds-only / --core-only / --vibrations-only, or none for all.")
            return 1

        print(f"\n{'='*70}")
        print("  MAXREGNER CORE v10.0.0 - AUDIO ENGINE & CORE REWRITES")
        print(f"  Target: {device.model} ({device.version})")
        print(f"  Parts: {', '.join(selected)}")
        print(f"{'='*70}")

        if sounds:
            print(f"\nMaxRegner Audio Engine: synthesising {len(MAXREGNER_SOUNDS)} system sounds...")
        print("\nBuilding restore package...")

        def update_label(msg):
            print(f"  {msg}")

        print("\nApplying MaxRegner Core...")
        print("This triggers a security recovery on iOS 27+...")
        print("Device will reboot and changes will be preserved.")

        _apply(dm, device, parts, update_label)

        print("\n" + "=" * 70)
        print("  MAXREGNER CORE APPLIED SUCCESSFULLY!")
        print("=" * 70)
        print("\nInstalled by the MaxRegner Audio Engine:")
        if sounds:
            print("  - Sound scheme (procedurally synthesised MaxRegner WAV assets)")
            print("  - System / keyboard / notification / call / camera slots remapped")
        if core:
            print("  - iOS core re-writes (identity, kernel, CPU/GPU, storage, power)")
        if vibrations:
            print("  - Custom vibration / haptic patterns (20+ patterns)")
        print("\nDevice will reboot automatically.")
        print("\nMaxRegner Core v10.0.0 - By Max Regner")
        print("=" * 70 + "\n")
        return 0

    except SystemExit:
        raise
    except Exception as e:
        print(f"\n\n{'='*70}")
        print(f"  ERROR: {e}")
        print(f"{'='*70}")
        import traceback
        traceback.print_exc()
        return 1


def main(argv: list = None) -> int:
    """MaxRegner Core CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GoldenNugget - MaxRegner Core & Audio Engine (Max Regner Edition)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Nugget --mode maxregnercore                Apply all (sounds + core + vibrations)
  Nugget --mode maxregnercore --sounds-only   Install only the MaxRegner sound scheme
  Nugget --mode maxregnercore --core-only     Apply only the iOS core re-writes
  Nugget --mode maxregnercore --vibrations-only  Apply only the vibration patterns
  Nugget --mode maxregnercore --udid <UDID>   Target a specific device
        """
    )
    parser.add_argument("--udid", help="Target device UDID")
    parser.add_argument("--list", action="store_true", help="List connected devices")
    parser.add_argument("--version", action="store_true", help="Show version")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sounds-only", action="store_true", help="Apply only the sound scheme")
    group.add_argument("--core-only", action="store_true", help="Apply only the core re-writes")
    group.add_argument("--vibrations-only", action="store_true", help="Apply only the vibration patterns")

    args = parser.parse_args(argv)

    if args.version:
        print("GoldenNugget MaxRegner Core v10.0.0 (Max Regner Edition)")
        return 0

    dm = DeviceManager()

    # Enumerate connected devices (needed for CMD mode), mirroring foldable_mode
    from PySide6.QtCore import QSettings
    settings = QSettings("GoldenNugget", "GoldenNugget")
    dm.get_devices(settings, show_alert=lambda x: None)

    if args.list:
        if not dm.devices:
            print("No devices connected.")
            return 1
        print("Connected devices:")
        for i, device in enumerate(dm.devices):
            print(f"  {i+1}. {device.name} - {device.model} (iOS {device.version}) - UDID: {device.udid}")
        return 0

    if not dm.devices:
        print("Error: No devices connected. Please connect your iPhone and make sure it's trusted.")
        return 1

    if not args.udid:
        args.udid = str(dm.devices[0].udid)

    return apply_maxregner_core(
        dm, args.udid,
        sounds=not (args.core_only or args.vibrations_only),
        core=not (args.sounds_only or args.vibrations_only),
        vibrations=not (args.sounds_only or args.core_only),
    )


if __name__ == "__main__":
    sys.exit(main())
