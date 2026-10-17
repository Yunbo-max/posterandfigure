# GPU enhancement and large-image operations

Use this reference when the task actually needs super-resolution or a high-RAM remote machine. PDF-only work does not require GPU setup.

## Environment and source

Inspect source dimensions/mode/profile, target pixels, free CPU RAM, GPU VRAM, disk, and existing jobs. Use an isolated environment with `torch`, `spandrel`, `numpy`, and `Pillow`; verify `torch.cuda.is_available()` on the selected host. The old `realesrgan` pip wrapper is unnecessary: the bundled script uses Spandrel. Install a PyTorch build compatible with the actual driver, not a copied CUDA version.

Prefer a lossless original; repeated JPEG re-encoding compounds artifacts. The bundled script follows Mariano215's upstream tiled, feather-blended Real-ESRGAN implementation (actual attribution/source below). Model choice: `realesrgan-x4plus-anime` for flat illustration/line art; inspect sample lettering since AI can distort mathematical or textual content.

## Explicit, bounded inference

The upstream auto-pass rule can choose **three** 4× passes for high-DPI targets, creating a 64× intermediate. Avoid that surprise: set `--passes 2` explicitly for a small poster like 1055 × 1491. Two passes produce 16880 × 23856 before final Lanczos resampling; a 900-DPI export then includes interpolation, not newly recovered true detail.

```bash
python scripts/upscale_for_print.py --src original.png \
  --pixels 9933x14043 --dpi 300 --passes 2 \
  --model realesrgan-x4plus-anime --models-dir ./models \
  --device cuda --out poster_300dpi.tif
```

Do not apply two more passes to an already huge master. Estimate the largest inference intermediate at roughly **40 bytes per output pixel** for the bundled float buffers, plus live input images, resampling copies, and model/tile memory. Keep headroom. This estimate is conservative guidance, not a measured guarantee. Read container/cgroup memory limits too: host RAM totals can be misleading.

Check aspect ratio before using the upstream default `cover` mode, which center-crops mismatches. Its `contain` mode pads black. Resolve a real mismatch explicitly (white padded source or an agreed crop); never silently stretch poster text.

GPU OOM: reduce tile size and retain overlap; do not repeatedly restart the same oversized configuration. A bounded retry after an evidenced fix is enough; report persistent failure with logs. CPU RAM OOM requires changing the image-memory strategy, not only the GPU tile size.

## Deflate master for lossless PDF

The upstream script writes LZW TIFF. For giant-image PDF export, convert on a high-RAM machine:

```python
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # only after validating the trusted input and RAM
with Image.open('poster_900dpi.tif') as im:
    im.save('poster_900dpi_deflate.tif', compression='tiff_adobe_deflate',
            tiffinfo={317: 2}, dpi=(900, 900),
            icc_profile=im.info.get('icc_profile', b''))
```

For 600 DPI from a larger enhanced master, resize once to 19866 × 28087 with Lanczos and save Deflate TIFF with `(600,600)`. This operation decodes the full source; do it where RAM is sufficient. The PDF helper itself streams TIFF strips and does not allocate a full gigapixel RGB image.

## China-host downloads and transfer

Prefer an already cached, verified model. A reachable package mirror can be supplied to pip with `--index-url https://pypi.tuna.tsinghua.edu.cn/simple`; don't weaken TLS verification. Model mirrors must match an independently established upstream digest before loading PyTorch weights.

For `RealESRGAN_x4plus_anime_6B.pth`, the validated digest is:

`f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da`

Upstream release: https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.2.4

Mirror repository used in this workflow: https://huggingface.co/amd/realesrgan-x4plus-anime-6b

Inspect its file listing for the exact path; a reachable `hf-mirror.com` endpoint can replace the host. Verify the local file using `sha256sum` before inference; do not trust a matching filename alone.

For remote execution, use the user's current authorized SSH configuration and verify host identity. Keep passwords, tokens, private keys, and login files out of this skill, its logs, and Git. Follow applicable project rules. Run detached jobs with logs and an exit-code file, then monitor the actual process; a launched command is not proof of completion. Do not interrupt unrelated jobs or delete other projects to free space.

If large-file SFTP is slow, measure a bounded transfer before changing transport. Resumable `rsync` or a small bounded set of SSH range downloads may help. Cap retries, retain completed ranges, and verify the assembled SHA-256. Never embed a particular user's host/password in the reusable skill.

## Provenance

Bundled `scripts/upscale_for_print.py` is from https://github.com/Mariano215/ai-image-upscaler, revision recorded in `validation.md`. Its MIT notice is in [UPSTREAM_LICENSE.txt](UPSTREAM_LICENSE.txt). Real-ESRGAN model/code have their own upstream licenses. The PDF helper is independent and requires only Pillow. No model weights, private poster, or credentials are distributed here.
