# Metadata-Driven Synthetic Data Workflow figure

This example preserves the supplied diagram layout and illustrations while replacing reviewed labels and table text with embedded vector text. The PDF page keeps the source image as its background; vector text remains selectable.

- `source.jpg`: source background at 1672 x 941 px (high-quality JPEG to keep the repository compact).
- `metadata_synthetic_workflow_vector.pdf`: 1672 x 941 pt hybrid PDF with embedded Times New Roman subsets.
- `metadata_synthetic_workflow_4x.png`: 6688 x 3764 indexed-color preview, optimized for compact sharing.
- `content_manifest.json`: transcribed text runs and tables.
- `rebuild.py`: rebuilds the PDF and manifest from `source.jpg`; requires Pillow and ReportLab.

Run `python rebuild.py` from this directory in an environment with Pillow and ReportLab installed. The script uses the local `source.jpg` and writes the PDF plus manifest beside itself.
