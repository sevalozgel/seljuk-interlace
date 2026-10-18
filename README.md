# Seljuk Interlace – parametric tile-mosaic component for Grasshopper

GhPython component (Rhinoceros 7, Grasshopper, IronPython 2.7) that reconstructs an Anatolian Seljuk eight-fold interlaced tile-mosaic pattern and splits it into buildable pieces: three-part bands (unglazed brick / turquoise / unglazed brick), joints, over-under cuts and inset polygonal cells.

Accompanies the article "Parametric Reconstruction of Seljuk Interlaced Tile Mosaics: The Gök Madrasa in Sivas" (Seval Özgel Felek, Ordu University).

## Files
- `seljuk_bands.py` – the GhPython component code
- `seljuk_bands_gh_olustur.py` – builder script that places the component with sliders on the Grasshopper canvas
- `KURULUM.md` – installation notes (Turkish)

## Quick start
1. Open Rhino 7 and Grasshopper.
2. Run `seljuk_bands_gh_olustur.py` from Rhino's `EditPythonScript` (or follow `KURULUM.md`).
3. Case-study values: Size 30, BandW 4.8, BlueW 1.45, BlueOffset 0, Joint 0.15, Interlace off, SplitCorners on.

## License
MIT – see `LICENSE`.

## Overlay analysis
`overlay/` holds the Python 3 scripts (numpy, scipy, Pillow, matplotlib) used to fit the module to a photographed knot medallion (Fig. 8 of the article). Set `SRC` in `fit.py` to the photograph path before running.
