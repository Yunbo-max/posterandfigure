# Validation and provenance

Date: 2026-10-08. This is an artifact-preparation skill, not a research experiment.

- `quick_validate.py` accepted the skill metadata and structure.
- `scripts/smoke_test.py` passed six offline integration checks: independent exact RGB extraction from the lossless PDF; one-page A0 geometry; preservation of existing outputs; rejection of unsupported TIFF compression; strict decimal-MB upload sizing; and clear failures for impossible caps or excessive input decode size. Tests use Pillow and Poppler, without GPU or network.
- Independent forward test on a 9933 × 14043 RGB TIFF produced a 17,887,016-byte A0 upload PDF at 299.998 effective PPI, JPEG quality 88. Poppler verified the single page, ICC image, and dimensions. Overview and text crops preserved the source layout; pre-existing malformed glyphs remained. This is lossy compression.
- The real 19866 × 28087 master was exported as a 240,747,843-byte A0 PDF at approximately 600 PPI. Metadata and rendered page were checked.
- The upstream inference script was exercised earlier in the source workflow on a Tesla T4 using two 4× Real-ESRGAN anime passes. Packaging the script did not constitute a new GPU test; no new hardware-compatibility claim is made.

The unmodified `scripts/upscale_for_print.py` comes from
`Mariano215/ai-image-upscaler` at
`b31e2147a67ff84bd3cdf4d76234a3ab6a6546e4`. Its MIT license is retained in
`UPSTREAM_LICENSE.txt`. The PDF helper and checks are separate additions.

Known limits of raster-only mode: text remains raster text; super-resolution cannot guarantee
correct letters or formulas. Upload mode decodes a bounded-size source and may
lower quality or DPI within its documented range. Huge-image lossless export
requires the stated TIFF format and strip bounds. Peak RAM was not measured in
the forward test because the local OS denied the instrumentation request.

## Vector text repair addition (2026-10-09)

- A real A0 poster was repaired section by section, preserving the upper cartoon and rebuilding the title, scientific text and a four-domain chart as vectors. The final hybrid PDF was **19,929,849 bytes**, below the strict 20,000,000-byte limit. All 32 plotted values were transcribed from the provided poster and checked; this was not an independent verification of the research claims. Full-page and detailed crops were rendered, including illustration boundaries and restored old-letter fragments. This production artifact used task-specific compositing code, not the newly packaged generic JSON helper.
- Baseline independent review of the old skill identified its missing vector compositor, transcription guidance and vector acceptance checks. The new mode addresses those gaps without replacing the existing super-resolution/export tools.
- `scripts/test_vector_overlay.py` passed an offline integration scenario using ReportLab 5.0.1, pypdf 6.20.0 and Poppler. It checks page geometry, extractable literal text, exact original image-stream preservation, pixel equality in a protected upper region, an opaque mask in the edited region, successful TrueType embedding, and safe failures for existing output, an impossible byte cap, text overflow and unsupported built-in-font glyphs. Failed export leaves an existing output unchanged. These checks do not prove automatic layout or transcription accuracy.
- The original six raster-export integration checks still pass. Skill metadata validation passes.
- Independent use of the updated skill on a separate 600 × 800 pt fixture produced a **58,779-byte** hybrid PDF under a 100,000-byte cap, with embedded Arial and a separate subscript text run. The upper region rendered pixel-identically to the source, the compressed image stream SHA-256 was unchanged, and full/detail renders showed complete masking and readable text. The review identified stale searchable text under repeated vector overlays; the reference now instructs consolidating the retained base/spec or performing genuine content edits when replacing previous vector text.

The generic compositor intentionally supports only one unencrypted, unrotated page with zero-origin equal MediaBox/CropBox and default UserUnit. It provides text, rectangles and lines, not OCR, automatic masking, paragraph layout, arbitrary clipping or complex-script shaping. Use a task-specific compositor for those layouts. Retained raster data is not re-encoded; original vector text behind opaque masks may remain extractable. Do not use visual masking when actual content removal is required.
