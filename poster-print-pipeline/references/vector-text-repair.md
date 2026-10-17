# Hybrid poster repair: raster artwork + vector scientific text

Use this mode when super-resolution or compression has left small text unreadable. The result is a PDF with retained raster illustrations and real text/vector charts. Vector text has no fixed DPI; report image PPI separately. This is re-typesetting, not a generative image redraw.

## Inspect and transcribe

1. Identify the original raster/design file, best enhanced master, existing upload PDF, desired paper size, exact byte limit and destination from the current task. Preserve existing files. A later section repair builds on the latest accepted PDF.
2. View the original and enhanced crops side by side. Distinguish blurry source pixels, AI-deformed letters and JPEG artifacts. A better encoder cannot correct a malformed glyph in the enhanced master.
3. Record a working content manifest with section IDs, exact text, formulas/subscripts, data labels/values and source provenance. Mark uncertain words explicitly. Prefer supplied editable source or verified manuscript/data; OCR is a draft, not authority. Do not silently correct grammar, infer a quotation, fill in a metric or replace an experimental claim. Resolve material ambiguity with the user while progressing on independent panels; an unchanged uncertain transcription may be delivered only with that limitation disclosed.
4. Record protected illustration regions, editable regions, and any title/author block that is part of the requested edit. A request to preserve the upper cartoon does not authorize rewriting its speech bubbles. Resolve genuinely ambiguous scope before changing those areas.

## Compose without damaging artwork

- Work in a reference coordinate system matching a rendered proof; map it exactly to the PDF page, respecting margins and aspect ratio. Do not conflate source-image pixels with full-page coordinates.
- Paint an opaque background over the entire old text footprint, including descenders, superscripts and antialiasing fringes, before adding the replacement. Otherwise two layers of letters remain visible.
- For dense panels, rebuilding the panel background, header and body is usually cleaner than dozens of tiny patches. Keep the user's color hierarchy, reading order and scientific relationships.
- Keep illustration cutouts tight. Rectangular crops around a robot can accidentally restore neighboring old captions and speech bubbles. Inspect the actual contour; use a precise clip path in a task-specific compositor when necessary. Paint masks and restored artwork in an order that does not bring old letters back or clip the illustration.
- Reconstruct chart labels and, when requested, vector bars using the verified values. Keep a separate table of original and transcribed values; check every value, method/domain label, sign and unit. Do not estimate numeric results from bar lengths or confuse a callout result with a plotted baseline.
- Use clean fonts and sufficient size. Prefer an embedded, licensed TrueType font for consistent printing; confirm glyph coverage for Greek, mathematical symbols and non-Latin text. Lay out subscripts/superscripts as separate text runs. Never silently remove a missing glyph or squeeze overflowing text until unreadable.
- Preserve existing PDF vector content. Do not render the completed page into a giant JPEG as the last export step; that would turn the repaired lettering back into pixels.
- When replacing text that was already vectorized, edit its retained manifest/spec and rebuild a consolidated overlay from the retained base PDF. Repeated opaque overlays can leave stale searchable text underneath. If the source/spec is unavailable and actual text replacement is needed, use genuine PDF content editing/removal and verify it independently; masking is only visual concealment. Adding a new section may build on the latest accepted PDF without replacing earlier text.

## Bundled compositor

Install dependencies in the task's environment, not by modifying a global CUDA/Python installation:

```bash
python -m pip install reportlab pypdf
python scripts/vector_overlay.py --src poster_A0_upload.pdf \
  --spec overlay.json --out poster_A0_text_clear.pdf --max-mb 20
```

Start from [example-overlay.json](example-overlay.json), a small coordinate example. **Its masks are not appropriate for an arbitrary poster**; supply coordinates and text from the inspected page. The script accepts one unencrypted, unrotated page with coincident zero-origin MediaBox/CropBox and default UserUnit. Normalize other PDFs with suitable PDF tools before composing.

JSON fields:

- `reference_size`: `[width, height]` of the full-page reference canvas. Origin is top-left; increasing y goes downward. Nonuniform scaling is possible, so use the actual page aspect ratio.
- `fonts`: optional mapping from a new font name to a TrueType font file, resolved relative to the JSON file. Built-in Helvetica/Times/Courier variants require Windows-1252 text. Supply a font with verified glyph coverage for other scripts. This lightweight compositor does not provide complex-script shaping or automatic paragraph layout.
- `operations`: paint order matters. All coordinates, text sizes and stroke widths are in reference units.
- `rect`: `x, y, w, h, fill`; optional `radius, stroke, width`. Creates an opaque mask or panel.
- `line`: `x, y, x2, y2`; optional `color, width`. Supports chart axes, arrows made of segments and rules.
- `text`: `x, y, text, size`; optional `font, color, max_width`. **y is the baseline**, not the top of a text box. One line per operation. `max_width` rejects overflow rather than silently shrinking text. Text positions and mask coverage still require visual review.

The compositor uses ReportLab for new vectors and pypdf to merge them onto the source PDF. It does not decode/recompress the background image. It refuses to overwrite without `--force` and only publishes after the final PDF is strictly smaller than `max_mb * 1,000,000` bytes. A failed export leaves any previous output intact. It does not automatically compress an oversized background.

For more complex shapes, preserve this workflow but use a task-specific ReportLab/SVG compositor. Do not copy hand-coded PDF object numbers from an old poster: object IDs, transforms, ICC resources and cross-reference tables differ between PDFs.

## Memory and size budget

- A 600-DPI A0 RGB image is about 558 million pixels: raw RGB alone is about 1.67 GB before temporary copies. A 900-DPI master is much larger. Header inspection or a small reference proof is safer than `convert`, `resize` or `copy` on the complete master in a 16-GB laptop.
- Prefer crops rendered from the existing PDF at the required scale. For a JPEG, libjpeg-turbo `djpeg -crop` can decode a region; check MCU-aligned coordinates. For TIFF use a region-capable/streaming reader or an adequately provisioned machine. If manually decoding Deflate strips, verify RGB8, layout, orientation, predictor and strip metadata first; do not assume one row per strip.
- Reserve headroom for new vectors and embedded fonts. Treat 20 MB as **20,000,000 bytes**, not 20 MiB. Measure the actual final PDF; rounded Finder sizes are insufficient.
- If over budget, recompress only the raster background and reapply the reviewed overlay. Compare representative text-free artwork crops and avoid repeatedly recompressing JPEG generations. Do not sacrifice the vector text or change the scientific content to meet the cap.

## Acceptance and handoff

1. `pdfinfo`: expected single page, A0/A1 dimensions, exact byte count.
2. `pdftotext -layout`: repaired text is extractable; check transcription against the manifest. Extractability alone does not prove it is visible, correctly positioned or semantically accurate.
3. `pdffonts`: inspect font availability/embedding; render on the target viewer if using unembedded standard fonts. `pdfimages -list`: inspect the retained raster resources.
4. `pdftoppm`: render the final full page and detailed crops of every edited region, including adjacent artwork. Check overlap, clipping, old text fragments, formula indices, punctuation, legends and all chart numbers. Compare protected regions with a render of the input at the same scale.
5. Confirm that the actual delivered file matches the checked artifact; report paper size, exact bytes, repaired scope and any unresolved source wording. Keep the transcript/spec and script for future edits; do not store credentials, SSH host details or personal absolute paths in the reusable skill.

This workflow preserves claims as supplied. It does not establish that a paper's results, affiliation or conference status are correct.
