# ArcGIS Pro Symbology Toolkit

A set of standalone ArcPy scripts for applying consistent, imagery-safe
symbology to lines, polygons, and points in an ArcGIS Pro map without
manually re-styling every layer by hand.

## Overview

These scripts loop through the layers in the **active map** of the
**current** ArcGIS Pro project and apply pre-defined symbology to any
layer whose name matches an entry in a lookup dictionary. The goal is to
make utility, boundary, and land-cover layers easy to read over any
basemap — including satellite/aerial imagery — instead of blending into
brown/gray ground tones.

| Script | Geometry | What it does |
|---|---|---|
| `apply_line_symbology.py` | Polyline | APWA-aligned colors, widths, dash patterns, and optional halo/casing effects for utility and non-utility line layers. |
| `apply_polygon_symbology.py` | Polygon | Solid fill, diagonal hatch, or outline-only styling depending on layer type (facility footprint, land-cover, or regulatory boundary). |
| `apply_svg_point_symbols.py` | Point | Applies vector point symbols from a custom `.stylx` style (built from a folder of SVGs) to point layers whose name exactly matches a symbol name. |

## Requirements

- ArcGIS Pro with ArcPy (scripts are run from **inside** Pro, not a
  standalone Python install)
- An active map in the current project
- Layer names in your Table of Contents that match (or fuzzy-match) the
  keys defined in each script's style dictionary

## Usage

### Line and polygon symbology

1. Open your ArcGIS Pro project and make sure the map you want to style
   is the **active** map view.
2. Open the Python window (**View > Python Window**), or add the script
   as a standalone script tool.
3. Paste in the contents of `apply_line_symbology.py` or
   `apply_polygon_symbology.py` and run it.
4. Review the summary printed at the end — it lists which layers were
   restyled and which were skipped (no matching name found).

If a layer in your map doesn't match a dictionary key, either rename the
layer or add/adjust an entry in `LAYER_STYLES` / `POLY_STYLES`.

### Point symbols from SVGs

1. Build a folder of SVG icons, one per point layer, named to match your
   layer names exactly (case-insensitive).
2. Use the **ImportSVGsToStyle** ArcGIS Pro add-in to bulk-convert that
   folder into a `.stylx` style file.
3. In your ArcGIS Pro project: **Insert > Style > Add**, and browse to the
   `.stylx` file. This step must happen before running the script.
4. Make sure the target map is active, open the Python window, and run
   `apply_svg_point_symbols.py`.
5. Matched layers are converted to a `SimpleRenderer` and given the
   corresponding vector symbol — fully editable afterward in the
   Symbology pane, not a flattened raster icon.

⚠️ Forcing a `SimpleRenderer` will replace any existing multi-symbol
renderer (e.g. Unique Values) on a matched layer. Back up your project
first if you need to preserve that.

## Customizing

Each script's style dictionary (`LAYER_STYLES`, `POLY_STYLES`) is meant to
be edited directly — add, remove, or re-color entries to match your own
layer names and cartographic standards. `FUZZY_MATCH` controls whether
layer-name matching ignores case, spaces, and underscores (`True`) or
requires an exact match (`False`).

**Note:** the dictionary keys shipped here (`LINE_LAYER_01`, `POLY_LAYER_01`,
etc.) are placeholders, not real layer names. Rename each one to match the
actual layer names in your own map's Table of Contents — the category
comments above each group indicate what kind of layer (water, storm sewer,
zoning boundary, etc.) each placeholder was originally styled for.

## License
GNU GENERAL PUBLIC LICENSE
