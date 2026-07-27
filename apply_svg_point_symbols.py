# apply_svg_point_symbols.py
#
# Author / Maintainer: Jonathan Kolterman
# Contact: jkolterman13@gmail.com
# LinkedIn: https://www.linkedin.com/in/jonathan-kolterman-1808342b8
#
# First create a folder of SVGs with names the same as your point layers.
# Then use the "ImportSVGsToStyle" ArcGIS Pro add-in to turn that folder
# into a style (.stylx). 
# https://www.arcgis.com/home/item.html?id=c25ab2da6ae343af9acc632120c7cf01#overview
# Now run this script.
#
# ============================================================
# Apply Vector Symbols from a Custom Style to Matching Layers
# ============================================================
#
# WHAT THIS SCRIPT DOES:
# For every point feature layer in the active map, this script looks for
# a symbol in the project's added styles that has the EXACT SAME NAME as
# the layer, and applies it as that layer's symbology.
#
# HOW TO USE THIS:
#   1. Build (or copy) a .stylx file containing your icons, where each
#      symbol's name matches a layer name exactly (case doesn't matter).
#      -> This was created using the "ImportSVGsToStyle" ArcGIS Pro add-in,
#         which bulk-converts a folder of SVGs into a vector-editable style.
#   2. Open your ArcGIS Pro project (.aprx).
#   3. Add the .stylx to the project:
#        Insert tab -> Style -> Add -> browse to the .stylx file
#      (This step MUST be done first, or the script won't find any symbols -
#       applySymbolFromGallery only searches styles that are already added
#       to the current project.)
#   4. Make sure the map you want to update is the ACTIVE map (the one
#      currently open/visible in the view).
#   5. Open the Python window in ArcGIS Pro (bottom of the screen, or
#      View tab -> Python Window).
#   6. Paste this whole script in and press Enter to run it.
#
# REQUIREMENTS / ASSUMPTIONS:
#   - Layer names in the map must exactly match the symbol names in the
#     style (case-insensitive) for a match to be found.
#   - This targets point feature layers. Line/polygon layers are skipped
#     automatically (isFeatureLayer will still be True for them, but a
#     point-symbol style item won't apply meaningfully -- adjust the
#     symbol type check below if you need line/polygon support later).
#   - This forces every matched layer to use a "SimpleRenderer" (a single
#     symbol for the whole layer). If a layer currently uses a different
#     renderer type (e.g. Unique Values, with different symbols per
#     category), that renderer will be REPLACED. Back up your project or
#     be aware of this before running on layers with complex symbology.
#
# ============================================================

import arcpy

# ------------------------------------------------------------
# STEP 1: Connect to the current ArcGIS Pro project and get the
# active map (the map currently open/visible in the view).
# ------------------------------------------------------------
aprx = arcpy.mp.ArcGISProject("CURRENT")
m = aprx.activeMap

# Safety check: if no map is open/active, stop here with a clear error
# instead of failing later with a confusing message.
if m is None:
    raise RuntimeError("No active map found. Make sure a map view is active.")

# ------------------------------------------------------------
# STEP 2: Set up tracking lists so we can report a summary at the end.
# ------------------------------------------------------------
applied = 0       # counts how many layers were successfully updated
skipped = []      # keeps track of layer names that were NOT updated (and why, via printed errors)

# ------------------------------------------------------------
# STEP 3: Loop through every layer in the active map.
# ------------------------------------------------------------
for lyr in m.listLayers():

    # Skip anything that isn't a feature layer (e.g. group layers,
    # basemaps, or non-feature layers don't have symbology to update).
    if not lyr.isFeatureLayer:
        continue

    try:
        # Get the current symbology object for this layer.
        # This is a "simplified" symbology object (not raw CIM) that
        # ArcPy exposes for easy editing.
        sym = lyr.symbology

        # Some layers (e.g. certain raster/annotation-like feature layers)
        # might not expose a "renderer" property at all. If so, skip safely.
        if not hasattr(sym, "renderer"):
            skipped.append(lyr.name)
            continue

        # If the layer isn't already using a SimpleRenderer (single symbol
        # for the whole layer), force it to one. This is required because
        # the code below sets sym.renderer.symbol directly, which only
        # exists on a SimpleRenderer.
        # NOTE: This will discard any existing Unique Values / other
        # multi-symbol renderer setup on that layer.
        if sym.renderer.type != "SimpleRenderer":
            sym.updateRenderer("SimpleRenderer")

        # ------------------------------------------------------------
        # STEP 4: Check whether a symbol with this layer's name actually
        # exists in any style currently added to the project.
        # ------------------------------------------------------------
        # listSymbolsFromGallery searches ALL styles added to the project
        # (system styles like ArcGIS 2D, plus any custom .stylx files you
        # added via Insert > Style > Add) for symbols matching the given
        # name/wildcard.
        matches = sym.renderer.symbol.listSymbolsFromGallery(lyr.name)

        # listSymbolsFromGallery can return partial/wildcard-ish matches,
        # so we filter down to an EXACT name match (case-insensitive)
        # to avoid accidentally grabbing the wrong symbol.
        exact = [s for s in matches if s.name.lower() == lyr.name.strip().lower()]

        # If no exact match was found, this layer has no corresponding
        # icon in the style -- skip it and move on.
        if not exact:
            skipped.append(lyr.name)
            continue

        # ------------------------------------------------------------
        # STEP 5: Apply the matching symbol to this layer.
        # ------------------------------------------------------------
        # applySymbolFromGallery pulls the named symbol in from the
        # project's added styles and applies it as a REAL, fully editable
        # vector CIM symbol (not a flattened picture/raster) -- meaning
        # you can still tweak color, size, etc. in the Symbology pane
        # afterward.
        sym.renderer.symbol.applySymbolFromGallery(lyr.name)

        # Changes to a symbology object don't take effect until you
        # assign it back to the layer's .symbology property.
        lyr.symbology = sym

        applied += 1
        print(f"Applied vector symbol to layer: {lyr.name}")

    except Exception as e:
        # Catch any unexpected error on a per-layer basis so one bad
        # layer doesn't stop the whole script -- just log it and continue.
        print(f"FAILED on layer '{lyr.name}': {e}")
        skipped.append(lyr.name)

# ------------------------------------------------------------
# STEP 6: Print a final summary so you can see what happened at a glance.
# ------------------------------------------------------------
print(f"\nDone. Applied to {applied} layer(s).")
if skipped:
    print("Skipped/unmatched layers:", skipped)
