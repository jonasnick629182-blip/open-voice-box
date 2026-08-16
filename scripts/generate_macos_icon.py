from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "packaging" / "OpenVoiceBox.icns"


def render_icon(size: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (size, size), (28, 30, 36, 255))
    draw = ImageDraw.Draw(image)

    margin = size // 16
    radius = size // 5
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill=(35, 39, 47, 255),
    )

    stroke = max(8, size // 24)
    left = int(size * 0.38)
    top = int(size * 0.20)
    right = int(size * 0.62)
    bottom = int(size * 0.60)
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=(right - left) // 2,
        outline=(245, 247, 250, 255),
        width=stroke,
    )
    draw.arc(
        (int(size * 0.29), int(size * 0.42), int(size * 0.71), int(size * 0.76)),
        0,
        180,
        fill=(245, 247, 250, 255),
        width=stroke,
    )
    draw.line(
        (size // 2, int(size * 0.76), size // 2, int(size * 0.86)),
        fill=(245, 247, 250, 255),
        width=stroke,
    )
    draw.line(
        (int(size * 0.40), int(size * 0.86), int(size * 0.60), int(size * 0.86)),
        fill=(245, 247, 250, 255),
        width=stroke,
    )
    return image


def build_icns(output: Path = OUTPUT) -> Path:
    if shutil.which("iconutil") is None:
        raise RuntimeError("iconutil is required and is only available on macOS")

    output.parent.mkdir(parents=True, exist_ok=True)
    master = render_icon(1024)
    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        iconset = Path(temp_dir) / "OpenVoiceBox.iconset"
        iconset.mkdir()
        for filename, pixels in sizes.items():
            master.resize((pixels, pixels), Image.Resampling.LANCZOS).save(
                iconset / filename
            )
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(output)],
            check=True,
        )
    return output


if __name__ == "__main__":
    print(build_icns())
