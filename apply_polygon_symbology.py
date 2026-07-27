"""
apply_polygon_symbology.py
---------------------------
Author / Maintainer: Jonathan Kolterman
Contact: jkolterman13@gmail.com
LinkedIn: https://www.linkedin.com/in/jonathan-kolterman-1808342b8

Applies consistent, imagery-safe polygon symbology to named layers in the
CURRENT ArcGIS Pro map.

APPROACH
- "utility"   : solid fill at low opacity (matches Water/Sewer/Storm hues
                used in the line script) + solid outline. Used for actual
                utility facility footprints (plants, pump stations, tanks).
- "hatch"     : diagonal hatch fill, no solid color underneath, so basemap/
                imagery stays visible. Used for regulatory boundaries and
                land-cover/operational zones that overlap heavily.
- "outline"   : no fill at all, colored outline only (often dashed). Used
                for boundary layers that stack directly on top of each
                other (ETJ, zoning, districts, wards) so they don't turn
                to mud when several are on at once.

HOW TO RUN
Same as apply_line_symbology.py -- open the Python window in Pro with the
target map active, and run this script (or exec() it from file).
"""

import arcpy


def rgba(r, g, b, a=100):
    return (r, g, b, a)


# ---------------------------------------------------------------------------
# STYLE DEFINITIONS
# ---------------------------------------------------------------------------
# mode: "utility" | "hatch" | "outline"
# fill_color:   used for "utility" (solid, low opacity) and "hatch" (hatch line color)
# outline_color: outline color (all modes)
# outline_width: outline weight
# outline_dash:  None or [on, off, ...] dash pattern for outline
# hatch_angle:   degrees, only used for "hatch" mode
# hatch_separation: spacing between hatch lines, only used for "hatch" mode

#
# NOTE ON LAYER NAMES: the keys below are placeholders (POLY_LAYER_01, etc.).
# Swap each placeholder for the actual layer name from your own map's Table
# of Contents. The section headers describe what category of real-world
# layer each placeholder was originally mapped to, so you know which
# placeholder to rename to which of your layers.
#
POLY_STYLES = {

    # ============ WATER UTILITY (Blue family #0A3D62) ============
    "POLY_LAYER_01":              {"mode": "utility", "fill_color": rgba(10, 61, 98, 25),  "outline_color": rgba(10, 61, 98, 100), "outline_width": 1.5, "outline_dash": None},
    "POLY_LAYER_02":            {"mode": "utility", "fill_color": rgba(10, 61, 98, 60),  "outline_color": rgba(10, 61, 98, 100), "outline_width": 1.5, "outline_dash": None},

    # ============ WASTEWATER UTILITY (Green family #4CE600) ============
    "POLY_LAYER_10":                    {"mode": "utility", "fill_color": rgba(76, 230, 0, 20),  "outline_color": rgba(58, 168, 0, 100), "outline_width": 1.5, "outline_dash": None},
    "POLY_LAYER_11":                  {"mode": "utility", "fill_color": rgba(76, 230, 0, 60),  "outline_color": rgba(58, 168, 0, 100), "outline_width": 1.5, "outline_dash": None},

    # ============ STORM / DRAINAGE (Brown family #8B5A2B) ============
    "POLY_LAYER_19":  {"mode": "utility", "fill_color": rgba(139, 90, 43, 45), "outline_color": rgba(139, 90, 43, 100), "outline_width": 1.5, "outline_dash": None},
    "POLY_LAYER_20":          {"mode": "hatch",   "fill_color": rgba(41, 128, 185, 100), "outline_color": rgba(41, 128, 185, 100), "outline_width": 1.2, "outline_dash": [6, 3], "hatch_angle": 45, "hatch_separation": 5},

    # ============ LAND COVER (earth-tone hatch, no solid fill) ============
    "POLY_LAYER_24":   {"mode": "hatch", "fill_color": rgba(0, 158, 96, 100),  "outline_color": rgba(0, 158, 96, 100),  "outline_width": 0.8, "outline_dash": None, "hatch_angle": 45,  "hatch_separation": 5},
    "POLY_LAYER_25":    {"mode": "hatch", "fill_color": rgba(154, 205, 50, 100),"outline_color": rgba(154, 205, 50, 100),"outline_width": 0.8, "outline_dash": None, "hatch_angle": 90,  "hatch_separation": 5},

    # ============ PARKS / RECREATION (green fill family, light) ============
    "POLY_LAYER_28":            {"mode": "utility", "fill_color": rgba(46, 204, 113, 30), "outline_color": rgba(30, 132, 73, 100), "outline_width": 1.2, "outline_dash": None},
    "POLY_LAYER_29": {"mode": "utility", "fill_color": rgba(255, 165, 0, 45),  "outline_color": rgba(255, 140, 0, 100), "outline_width": 1.0, "outline_dash": None},

    # ============ OPERATIONAL OVERLAYS (bright hatch, reference-only) ============
    "POLY_LAYER_37":    {"mode": "hatch", "fill_color": rgba(255, 0, 255, 100), "outline_color": rgba(255, 0, 255, 100), "outline_width": 0.8, "outline_dash": None, "hatch_angle": 45,  "hatch_separation": 6},
    "POLY_LAYER_38":  {"mode": "hatch", "fill_color": rgba(0, 229, 255, 100), "outline_color": rgba(0, 229, 255, 100), "outline_width": 0.8, "outline_dash": None, "hatch_angle": 135, "hatch_separation": 6},

    # ============ REGULATORY / JURISDICTIONAL BOUNDARIES (outline only) ============
    "POLY_LAYER_40":            {"mode": "outline", "fill_color": None, "outline_color": rgba(155, 89, 182, 100), "outline_width": 1.5, "outline_dash": [8, 3]},
    "POLY_LAYER_41":           {"mode": "outline", "fill_color": None, "outline_color": rgba(142, 68, 173, 100), "outline_width": 1.2, "outline_dash": None},

    # ============ PROPERTY / INFRASTRUCTURE (neutral, mostly outline) ============
    "POLY_LAYER_58":       {"mode": "outline", "fill_color": None, "outline_color": rgba(255, 20, 147, 100), "outline_width": 0.6, "outline_dash": None},
    "POLY_LAYER_59":     {"mode": "utility", "fill_color": rgba(0, 229, 220, 45), "outline_color": rgba(0, 190, 180, 100), "outline_width": 1.0, "outline_dash": None},

    # ============ MISC ============
    "POLY_LAYER_64":        {"mode": "outline", "fill_color": None, "outline_color": rgba(255, 105, 180, 100), "outline_width": 1.0, "outline_dash": [3, 3]},
    "POLY_LAYER_65":{"mode": "outline", "fill_color": None, "outline_color": rgba(255, 0, 255, 100), "outline_width": 1.2, "outline_dash": [5, 3]},
}

FUZZY_MATCH = True


def _normalize(name):
    return name.lower().replace(" ", "").replace("_", "")


def build_symbol_layers(style):
    """Returns a list of CIM symbol-layer dicts (fill + outline) for the
    given style, ordered bottom-to-top."""
    layers = []

    if style["mode"] == "utility":
        layers.append({
            "type": "CIMSolidFill",
            "enable": True,
            "color": {"type": "CIMRGBColor", "values": list(style["fill_color"])}
        })

    elif style["mode"] == "hatch":
        layers.append({
            "type": "CIMHatchFill",
            "enable": True,
            "rotation": style.get("hatch_angle", 45),
            "separation": style.get("hatch_separation", 5),
            "lineSymbol": {
                "type": "CIMLineSymbol",
                "symbolLayers": [{
                    "type": "CIMSolidStroke",
                    "enable": True,
                    "width": 0.6,
                    "color": {"type": "CIMRGBColor", "values": list(style["fill_color"])}
                }]
            }
        })

    # mode == "outline" adds no fill layer at all

    # Outline (all modes)
    outline_stroke = {
        "type": "CIMSolidStroke",
        "enable": True,
        "capStyle": "Round",
        "joinStyle": "Round",
        "width": style["outline_width"],
        "color": {"type": "CIMRGBColor", "values": list(style["outline_color"])}
    }
    if style.get("outline_dash"):
        outline_stroke["effects"] = [{
            "type": "CIMGeometricEffectDashes",
            "dashTemplate": style["outline_dash"],
            "lineDashEnding": "NoConstraint",
            "controlPointEnding": "NoConstraint"
        }]

    # For polygon symbols, the outline is its own stroke layer sitting on
    # top of the fill/hatch layer(s) in the same symbol layer stack.
    layers.append(outline_stroke)

    return layers


def apply_symbology():
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    active_map = aprx.activeMap

    if active_map is None:
        print("No active map found. Open a map view and try again.")
        return

    lookup = {}
    for key in POLY_STYLES:
        lookup[_normalize(key) if FUZZY_MATCH else key] = key

    applied, skipped = [], []

    for lyr in active_map.listLayers():
        if not lyr.isFeatureLayer:
            continue
        try:
            desc = arcpy.Describe(lyr)
            if desc.shapeType != "Polygon":
                continue
        except Exception:
            continue

        name_key = _normalize(lyr.name) if FUZZY_MATCH else lyr.name
        if name_key not in lookup:
            skipped.append(lyr.name)
            continue

        style = POLY_STYLES[lookup[name_key]]
        symbol_layers = build_symbol_layers(style)

        try:
            cim_layer = lyr.getDefinition("V3")
            renderer = cim_layer.renderer
            renderer.symbol.symbol.symbolLayers = symbol_layers
            lyr.setDefinition(cim_layer)
            applied.append(lyr.name)
        except Exception as e:
            print(f"  Could not apply style to '{lyr.name}': {e}")
            skipped.append(lyr.name)

    print("\n--- Polygon Symbology Apply Summary ---")
    print(f"Applied to {len(applied)} layer(s):")
    for n in applied:
        print(f"   - {n}")
    if skipped:
        print(f"\nSkipped/no match for {len(skipped)} layer(s):")
        for n in skipped:
            print(f"   - {n}")


if __name__ == "__main__":
    apply_symbology()
