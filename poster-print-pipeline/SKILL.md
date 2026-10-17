---
name: poster-print-pipeline
description: Use when preparing academic posters for A0/A1 printing, repairing blurry or AI-distorted poster text as PDF vectors while preserving illustrations, or meeting conference PDF upload limits such as 20 MB. Also applies to local or remote GPU upscaling; not research-method pipeline design.
---

# Poster Print Pipeline

Turn an existing poster into separately verified print and upload files. Preserve its source, scientific content and user-selected artwork. Prefer the original vector/design file when available. Increasing DPI or AI upscaling does not recover missing text or correct misspellings; reviewed transcription plus vector typesetting can repair the lettering.

## Choose the repair mode

- **Illustration detail:** use the existing Real-ESRGAN workflow below. Compare original and enhanced crops; super-resolution can deform small text even when the original was readable.
- **Warped letters, equations, small chart labels:** read [references/vector-text-repair.md](references/vector-text-repair.md). Reconstruct reviewed text as vector text over opaque masks or rebuilt panels; retain the raster illustrations. Do not solve this by increasing DPI again.
- **Upload size only:** reuse the best existing master or PDF. Preserve existing vector layers; compress the raster background separately, then compose and measure the final file.

The vector mode includes a portable JSON compositor, `scripts/vector_overlay.py` (ReportLab and pypdf). It reuses the input PDF's image streams, checks text width and unsupported glyphs, and fails without publishing if the exact byte cap is exceeded. It does not perform OCR, infer quotations, erase text automatically, or validate chart semantics. The agent supplies reviewed text, masks and positions.

## Decide what to deliver

- Resolve the source, requested paper size, output directory, and any upload byte limit. Use the current conversation's choices. Clarify `1080p` versus `1080 DPI` when ambiguous.
- A0 is 841 × 1189 mm; A1 is 594 × 841 mm. Pixels = round(mm × DPI / 25.4). A0 targets: 300 DPI = 9933 × 14043; 600 = 19866 × 28087; 900 = 29799 × 42130.
- A print master and a capped upload PDF serve different needs. Default upload export starts at 300 DPI; report its actual density if lowered. Preserve the high-resolution master.
- Inspect metadata and an overview before allocating pixels. A 900-DPI A0 image is 1.25 billion pixels; GPU VRAM and CPU RAM are separate constraints. Do not decode it on a memory-constrained laptop merely to create a PDF.

## Enhance only when needed

Read [references/gpu-workflow.md](references/gpu-workflow.md) for the tested Real-ESRGAN pipeline, explicit pass count, model integrity, memory checks, and optional SSH execution. Reuse an existing enhanced master for another output resolution. Inspect lettering, equations, logos, and tile boundaries; do not claim semantic text repair.

For smaller print files, export RGB TIFF with embedded sRGB profile. For huge masters intended for streaming PDF conversion, use **untiled 8-bit RGB Deflate TIFF, predictor 1 or 2, orientation 1**, with strips no larger than 16 MiB compressed or decoded. LZW is not accepted by the streaming helper: convert it on a machine with enough RAM, or use a suitable image/PDF tool instead.

## Export PDF

Only Pillow is required for the raster export helper. Run `python scripts/poster_pdf.py --help` for options. Paths below are examples; resolve them from the user's actual inputs and the skill directory.

```bash
# Full-resolution master: streaming, lossless, no giant full-frame decode.
python scripts/poster_pdf.py lossless --src poster_600dpi.tif \
  --out poster_A0_600dpi.pdf --paper A0

# Separate upload version, using a manageable lossless source.
python scripts/poster_pdf.py upload --src poster_300dpi.tif \
  --out poster_A0_upload.pdf --paper A0 --max-mb 20
```

The helper preserves aspect ratio and centers the image on a white page. Upload export uses 4:4:4 JPEG, measures the final PDF against **20,000,000 bytes**, and leaves a margin. It tries bounded quality/DPI reductions; it fails explicitly if the cap cannot be met. Outputs are never replaced without `--force`. Do not promise that an upload version is lossless.

## Verify and hand off

```bash
pdfinfo poster_A0_upload.pdf
pdfimages -list poster_A0_upload.pdf
pdftoppm -f 1 -singlefile -scale-to 1600 -png poster_A0_upload.pdf check
```

Check the one-page paper size, actual raster DPI, exact bytes, and the rendered overview plus representative small-text crops. For vector repair, also extract text, compare every transcribed chart value with its source, and inspect all touched panel boundaries for residual old letters or cropped artwork. Report unresolved transcription ambiguities; do not equate clearer typography with verified research claims. Provide clickable paths to the actual files, identify the upload file, and use 100%/actual-size printing. Transfer remote files with SHA-256 verification; do not say a file is downloaded until it is complete.

For maintenance, run `python scripts/smoke_test.py` and `python scripts/test_vector_overlay.py` (the latter also needs ReportLab/pypdf; both need Poppler). These are artifact integration checks, not GPU inference or semantic validation. Provenance and limits are in [references/validation.md](references/validation.md).
