"""
apply_line_symbology.py
------------------------
Author / Maintainer: Jonathan Kolterman
Contact: jkolterman13@gmail.com
LinkedIn: https://www.linkedin.com/in/jonathan-kolterman-1808342b8

Applies a consistent, APWA-aligned, imagery-safe line symbology to a set of
named layers in the CURRENT ArcGIS Pro map.

WHAT THIS DOES
- Loops through every layer in the active map.
- If a layer's name matches one of the entries in LAYER_STYLES below, it
  builds a CIM line symbol (color, width, dash pattern) and, where
  specified, adds a "halo"/casing effect underneath so the line stays
  visible on satellite/aerial imagery instead of blending into brown/gray
  ground tones.
- Applies that symbol to the layer's symbology (simple renderer).

HOW TO RUN
1. Open your ArcGIS Pro project.
2. Open the Python window (View > Python Window), or add this as a
   standalone script tool.
3. Paste/run this script. It automatically targets the CURRENT project
   and the active map.
4. Layer names must match what's in your Table of Contents (case-insensitive,
   partial match supported -- see MATCH_MODE below).

NOTES
- If a layer name in your map doesn't exactly match the dictionary keys,
  either rename the layer, or add it to LAYER_STYLES / adjust MATCH_MODE.
- This only restyles LINE layers with a simple (single symbol) renderer.
  If a layer already has categorical/graduated symbology you want to keep,
  remove it from LAYER_STYLES before running.
- Halo/casing is implemented as two stacked stroke symbol layers: a wider
  "halo" layer underneath, and the true color on top, so the line reads
  clearly over any basemap (imagery, gray canvas, topo, etc).
"""

import arcpy


# ---------------------------------------------------------------------------
# STYLE DEFINITIONS
# ---------------------------------------------------------------------------
# Each entry:
#   "Layer Name": {
#       "color": (R, G, B, A)          -- the true line color
#       "width": float                  -- line width in points
#       "dash":  None or [on, off, ...] -- dash pattern in points, None = solid
#       "halo_color": None or (R,G,B,A) -- set to add a casing/halo effect
#       "halo_extra_width": float       -- how much wider the halo is than the line
#   }

#
# NOTE ON LAYER NAMES: the keys below are placeholders (LINE_LAYER_01, etc.).
# Swap each placeholder for the actual layer name from your own map's Table
# of Contents. The category comments describe what kind of real-world
# layer each placeholder was originally mapped to, so you know which
# placeholder to rename to which of your layers.
#
LAYER_STYLES = {

    # ---------------- WATER (APWA Blue family) ----------------
    "LINE_LAYER_01": {  # e.g. water main line
        "color": (10, 61, 98, 100), "width": 2.5, "dash": None,
    },
    "LINE_LAYER_02": {  # e.g. water flow-direction arrow
        "color": (10, 61, 98, 100), "width": 1.2, "dash": None,
    },

    # ---------------- SEWER / WASTEWATER (Green family) ----------------
    "LINE_LAYER_03": {  # e.g. wastewater/sewer main line
        "color": (76, 230, 0, 100), "width": 2.5, "dash": None,
    },
    "LINE_LAYER_04": {  # e.g. wastewater flow-direction arrow
        "color": (76, 230, 0, 100), "width": 1.2, "dash": None,
    },

    # ---------------- STORM SEWER (Brown family) ----------------
    "LINE_LAYER_05": {  # e.g. storm sewer main line
        "color": (139, 90, 43, 100), "width": 2.5, "dash": None,
    },
    "LINE_LAYER_06": {  # e.g. storm open drainage line
        "color": (139, 90, 43, 100), "width": 2.0, "dash": [6, 2, 1, 2],

    # ---------------- GAS (APWA Yellow) ----------------
    "LINE_LAYER_11": {  # e.g. gas line
        "color": (255, 232, 0, 100), "width": 2.5, "dash": None,
    },

    # ---------------- POWER (APWA Red) ----------------
    "LINE_LAYER_12": {  # e.g. power line
        "color": (228, 0, 43, 100), "width": 2.5, "dash": None,
    },

    # ---------------- NON-UTILITY LAYERS (imagery-safe swaps) ----------------
    "LINE_LAYER_13": {  # e.g. extraterritorial jurisdiction boundary
        "color": (0, 229, 255, 100), "width": 2.0, "dash": [10, 3, 1, 3, 1, 3],
    },
    "LINE_LAYER_14": {  # e.g. street centerline schema
        "color": (255, 255, 255, 100), "width": 2.0, "dash": None,

}

# Set to True to match layer names loosely (ignore case/underscores/spaces).
# Set to False to require exact (case-sensitive) matches to LAYER_STYLES keys.
FUZZY_MATCH = True


# ---------------------------------------------------------------------------
# SYMBOL BUILDING
# ---------------------------------------------------------------------------

def _normalize(name):
    return name.lower().replace(" ", "").replace("_", "")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def apply_symbology():
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    active_map = aprx.activeMap

    if active_map is None:
        print("No active map found. Open a map view and try again.")
        return

    lookup = {}
    for key in LAYER_STYLES:
        lookup[_normalize(key) if FUZZY_MATCH else key] = key

    applied, skipped = [], []

    for lyr in active_map.listLayers():
        if not lyr.isFeatureLayer:
            continue

        try:
            desc = arcpy.Describe(lyr)
            if desc.shapeType not in ("Polyline",):
                continue
        except Exception:
            continue

        name_key = _normalize(lyr.name) if FUZZY_MATCH else lyr.name
        if name_key not in lookup:
            skipped.append(lyr.name)
            continue

        style_key = lookup[name_key]
        style = LAYER_STYLES[style_key]

        sym = lyr.symbology
        if not hasattr(sym, "renderer"):
            skipped.append(lyr.name)
            continue

        # Build CIM symbol layers
        cim_layer = lyr.getDefinition("V3")

        symbol_layers = []
        if style.get("halo_color"):
            symbol_layers.append({
                "type": "CIMSolidStroke",
                "enable": True,
                "capStyle": "Round",
                "joinStyle": "Round",
                "width": style["width"] + style["halo_extra_width"] * 2,
                "color": {"type": "CIMRGBColor", "values": list(style["halo_color"])}
            })

        main_stroke = {
            "type": "CIMSolidStroke",
            "enable": True,
            "capStyle": "Round",
            "joinStyle": "Round",
            "width": style["width"],
            "color": {"type": "CIMRGBColor", "values": list(style["color"])}
        }
        if style.get("dash"):
            main_stroke["effects"] = [{
                "type": "CIMGeometricEffectDashes",
                "dashTemplate": style["dash"],
                "lineDashEnding": "NoConstraint",
                "controlPointEnding": "NoConstraint"
            }]
        symbol_layers.append(main_stroke)

        try:
            renderer = cim_layer.renderer
            renderer.symbol.symbol.symbolLayers = symbol_layers
            lyr.setDefinition(cim_layer)
            applied.append(lyr.name)
        except Exception as e:
            print(f"  Could not apply style to '{lyr.name}': {e}")
            skipped.append(lyr.name)

    print("\n--- Symbology Apply Summary ---")
    print(f"Applied to {len(applied)} layer(s):")
    for n in applied:
        print(f"   - {n}")
    if skipped:
        print(f"\nSkipped/no match for {len(skipped)} layer(s):")
        for n in skipped:
            print(f"   - {n}")


if __name__ == "__main__":
    apply_symbology()