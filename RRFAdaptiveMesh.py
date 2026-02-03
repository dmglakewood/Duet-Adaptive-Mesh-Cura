# RRFAdaptiveMesh.py - V10 (Negative Coordinate Fix)
from ..Script import Script
import re

class RRFAdaptiveMesh(Script):
    def getSettingDataString(self):
        return """{
            "name": "RRF Adaptive Mesh (Auto)",
            "key": "RRFAdaptiveMesh",
            "metadata": {},
            "version": 2,
            "settings": {
                "x_offset": {
                    "label": "X Offset (mm)",
                    "description": "Shift mesh X. (Default 0)",
                    "type": "int",
                    "default_value": 0
                },
                "y_offset": {
                    "label": "Y Offset (mm)",
                    "description": "Shift mesh Y. (Default 0)",
                    "type": "int",
                    "default_value": 0
                }
            }
        }"""

    def execute(self, data):
        # --- CONFIG ---
        PADDING = 10
        TARGET_SPACING = 50
        # --------------

        try:
            user_offset_x = self.getSettingValueByKey("x_offset")
            user_offset_y = self.getSettingValueByKey("y_offset")
        except:
            user_offset_x = 0
            user_offset_y = 0

        min_x = 9999.0
        max_x = -9999.0
        min_y = 9999.0
        max_y = -9999.0
        
        bed_x = 300.0
        bed_y = 300.0
        
        found_model = False
        valid_feature = False
        parsing_layer_0 = False
        
        # Regex: Now includes '-' to catch negative coords properly
        p_move = re.compile(r'[Gg][01].*[Xx]([-\d\.]+).*[Yy]([-\d\.]+)')
        p_limit = re.compile(r';BED_LIMITS.*X([\d\.]+).*Y([\d\.]+)')

        allowed_types = [
            "WALL-OUTER", "WALL-INNER", "SKIN", "FILL", 
            "SUPPORT", "SUPPORT-INTERFACE", "PRIME-TOWER"
        ]

        for layer in data:
            if ";LAYER:0" in layer:
                parsing_layer_0 = True

            for line in layer.split("\n"):
                if ";BED_LIMITS" in line:
                    m = p_limit.search(line)
                    if m:
                        bed_x = float(m.group(1))
                        bed_y = float(m.group(2))

                if line.startswith(";TYPE:"):
                    feature_type = line.split(":")[1].strip()
                    if feature_type in allowed_types:
                        valid_feature = True
                    else:
                        valid_feature = False
                
                # STRICT FILTERING:
                # 1. Must be after Layer 0 started (Ignores Start Gcode)
                # 2. Must be a "Model" feature (Ignores Skirt/Brim)
                # 3. Must have Extrusion 'E' (Ignores Travel)
                if parsing_layer_0 and valid_feature:
                    if "E" in line and (line.startswith("G1") or line.startswith("G0")):
                        m = p_move.search(line)
                        if m:
                            found_model = True
                            x = float(m.group(1))
                            y = float(m.group(2))
                            if x < min_x: min_x = x
                            if x > max_x: max_x = x
                            if y < min_y: min_y = y
                            if y > max_y: max_y = y

        if not found_model:
            return data

        # Apply Padding
        min_x = max(0, min_x - PADDING)
        max_x = min(bed_x, max_x + PADDING)
        min_y = max(0, min_y - PADDING)
        max_y = min(bed_y, max_y + PADDING)
        
        # Apply Offsets
        min_x += user_offset_x
        max_x += user_offset_x
        min_y += user_offset_y
        max_y += user_offset_y

        # Dynamic Spacing
        x_span = max_x - min_x
        y_span = max_y - min_y
        spacing = TARGET_SPACING
        if x_span < spacing: spacing = x_span / 2
        if y_span < spacing: 
            tmp = y_span / 2
            if tmp < spacing: spacing = tmp
        if spacing < 10: spacing = 10
        spacing = int(spacing)
        
        cmd = "M557 X{:.1f}:{:.1f} Y{:.1f}:{:.1f} S{:d}".format(min_x, max_x, min_y, max_y, spacing)
        
        # Add a Debug Comment to the G-code so we can verify what it found
        debug_info = "; [RRFAdaptiveMesh] DEBUG: Found Bounds X{:.1f}:{:.1f} Y{:.1f}:{:.1f}".format(min_x - user_offset_x, max_x - user_offset_x, min_y - user_offset_y, max_y - user_offset_y)

        new_data = []
        for layer in data:
            if ";MESH_CALC" in layer:
                layer = layer.replace(";MESH_CALC", debug_info + "\n" + cmd)
            new_data.append(layer)
            
        return new_data