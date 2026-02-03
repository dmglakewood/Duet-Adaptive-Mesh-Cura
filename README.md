# Adaptive Mesh For Duet 2/3 Using Cura

A lightweight Python Post-Processing script for Ultimaker Cura that brings **Adaptive Mesh Leveling** to RepRapFirmware (Duet 2/3) printers.

Unlike Klipper, RRF does not yet have a native "Adaptive" flag for mesh generation. This script parses your G-code after slicing, calculates the exact bounding box of your print (ignoring purge lines, skirts, and travel moves), and injects a dynamic `M557` grid definition.

**Result:** Your printer only probes the area where the part is, drastically reducing start times.

## Features
* **Smart Detection:** Ignores purge lines, prime towers, and travel moves to find the *true* print center.
* **Negative Coordinate Support:** Full support for printers with negative wiped zones (like LulzBot Taz 6).
* **Dynamic Spacing:** Automatically tightens the probe grid density for smaller parts to ensure accuracy.
* **Zero-UI Mode:** Can run entirely in the background using Start G-code tags.
* **Offsets:** Supports manual X/Y offsets for printers where the bed origin differs from the homing origin.

## Installation

1.  Download `RRFAdaptiveMesh.py`.
2.  Place the file in your Cura scripts folder:
    * **Windows:** `%APPDATA%\cura\<version>\scripts`
    * **macOS:** `~/Library/Application Support/cura/<version>/scripts`
    * **Linux:** `~/.config/cura/<version>/scripts`
3.  Restart Cura.

## Configuration

### 1. Enable the Script
In Cura, go to **Extensions > Post Processing > Modify G-Code** and add **RRF Adaptive Mesh (Auto)**.

### 2. Do I need an X/Y Offset? (The "0,0" Test)
Some printers (like the **LulzBot Taz 6**) have a physical home position that is far away from the actual print bed. If your mesh is probing the air or hitting frame limits, perform this simple test:

1.  **Home your printer** (`G28`).
2.  **Send the command:** `G1 X0 Y0` (Move to 0,0).
3.  **Look at the Nozzle:**
    * **Is the nozzle exactly on the front-left corner of the bed?**
        * ✅ **No Offset Needed.** Leave settings at `0`.
    * **Is the nozzle floating in the air (e.g., to the left of the bed)?**
        * ⚠️ **Offset Needed.**
        * Measure the distance (in mm) from the nozzle to the actual edge of the bed.
        * **Example:** If the nozzle is 40mm to the left of the glass, enter **40** in the **X Offset** field.

### 3. Update Start G-Code (Critical)
You must add two tags to your **Machine Settings > Start G-code** so the script knows the bed limits and where to inject the command.

**Example Start G-Code:**
```gcode
;BED_LIMITS X{machine_width} Y{machine_depth}  <-- Script reads this to know bed size
M140 S{material_bed_temperature_layer_0}
M104 S160
G28 ; Home

;MESH_CALC  <-- Script replaces this line with the calculated M557 command

G29 ; Probe the bed
G1 X0 Y0 F3000
