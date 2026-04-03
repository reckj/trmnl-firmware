"""
PlatformIO pre-build script: Patches FastEPD for the LilyGo T5-4.7" V2.3 (ESP32-S3).

The upstream FastEPD defines BB_PANEL_LILYGO_T5P4 for the original ESP32 board
(1440x720, data pins 27-34, 40MHz). The T5-4.7" V2.3 uses an ESP32-S3 with
completely different GPIO pins and a 960x540 ED047TC1 display.

Pin mapping sourced from: https://github.com/Xinyuan-LilyGO/LilyGo-EPD47 (esp32s3 branch)
  - ed047tc1.h: D0=8, D1=1, D2=2, D3=3, D4=4, D5=5, D6=6, D7=7
  - CKV=38, STH/SPH=40, CKH/CL=41
  - CFG_DATA=13, CFG_CLK=12, CFG_STR=0
  - STV and OE are controlled via shift register (not direct GPIO)

Two patches applied:
1. PANEL DEF: Replace entire T5P4 panel definition with ESP32-S3 V2.3 pins
2. PANEL PROCS: Change T5P4 callbacks to LilyGo shift-register functions
"""
Import("env")
import os
import re

# GPIO 45 is used as a dummy D/C pin for the ESP LCD I80 bus driver.
# The I80 driver requires a valid DC GPIO even though e-paper doesn't use D/C.
# GPIO 45 is a strapping pin (VDD_SPI) but safe as output after boot, and
# is not connected to any peripheral on the T5-4.7" V2.3 board.
DC_DUMMY_GPIO = 45

def patch_fastepd(env):
    libdeps_dir = os.path.join(env["PROJECT_LIBDEPS_DIR"], env["PIOENV"])
    fastepd_inl = None

    for root, dirs, files in os.walk(libdeps_dir):
        if "FastEPD.inl" in files:
            fastepd_inl = os.path.join(root, "FastEPD.inl")
            break

    if not fastepd_inl:
        print("WARNING: FastEPD.inl not found, skipping patch")
        return

    with open(fastepd_inl, "r") as f:
        content = f.read()

    patched = False

    # --- Patch 1: Replace T5P4 panel definition ---
    # The upstream definition spans 2 lines and uses ESP32 pins (27-34, 1440x720)
    if "PATCHED_T5P4_PINS" not in content:
        # Match the T5P4 panel definition (may span multiple lines)
        # Upstream: {1440, 720, 40000000, BB_PANEL_FLAG_MIRROR_X, {27,28,29,30,31,32,33,34}, 8, ...}, // BB_PANEL_LILYGO_T5P4
        pattern = r'\{1440,\s*720,\s*40000000,\s*BB_PANEL_FLAG_MIRROR_X,\s*\{27,28,29,30,31,32,33,34\}[^}]*\}[^/]*//\s*BB_PANEL_LILYGO_T5P4\s*'

        replacement = (
            "/* PATCHED_T5P4_PINS: ESP32-S3 V2.3 pin mapping (replaces original ESP32 pins) */\n"
            "    {960, 540, 20000000, BB_PANEL_FLAG_SLOW_SPH, {8,1,2,3,4,5,6,7}, 8, "
            "BB_NOT_USED, BB_NOT_USED, 38, 40, BB_NOT_USED, BB_NOT_USED,\n"
            f"      41, BB_NOT_USED, 13, 12, 0, 0, {DC_DUMMY_GPIO}, "
            "u8M5Matrix, sizeof(u8M5Matrix), 16, -1600}, // BB_PANEL_LILYGO_T5P4\n"
        )

        new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
        if count > 0:
            content = new_content
            print(f"Patch 1/2: Replaced T5P4 panel definition with ESP32-S3 V2.3 pins (DC dummy=GPIO {DC_DUMMY_GPIO})")
            patched = True
        else:
            print("WARNING: Could not find upstream T5P4 panel definition to patch")
            print("  (If already patched from a previous run, this is expected)")
    else:
        print("Patch 1/2: T5P4 panel definition already patched")

    # --- Patch 2: Replace T5P4 callback functions ---
    # The upstream uses EPDiy V7 I2C callbacks, but the V2.3 uses a shift register
    if "PATCHED_T5P4_PROCS" not in content:
        old_procs = (
            r'\{EPDiyV7EinkPower,\s*EPDiyV7IOInit,\s*EPDiyV7RowControl,\s*'
            r'EPDiyV7IODeInit,\s*EPDiyV7ExtIO\}'
            r'(,\s*//\s*BB_PANEL_LILYGO_T5P4)'
        )
        new_procs = (
            "/* PATCHED_T5P4_PROCS */ "
            "{LilyGoEinkPower, LilyGoIOInit, LilyGoRowControl, NULL, NULL}"
            r"\1"
        )
        content, count = re.subn(old_procs, new_procs, content)
        if count > 0:
            print("Patch 2/2: Changed T5P4 panelProcs to LilyGo shift-register callbacks")
            patched = True
        else:
            print("WARNING: Could not find T5P4 panelProcs pattern to patch")
    else:
        print("Patch 2/2: T5P4 panelProcs already patched")

    if patched:
        with open(fastepd_inl, "w") as f:
            f.write(content)
        print("Successfully patched FastEPD.inl for LilyGo T5-4.7\" V2.3 (ESP32-S3)")
    else:
        print("No patches needed - FastEPD.inl already up to date")

# Run patch immediately at script load time (this is a pre: script)
patch_fastepd(env)
