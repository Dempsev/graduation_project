from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "output" / "thesis_charts" / "chapter6" / "physical_mechanism" / "ep17_bilobe_witness_case_v1"

PANELS = [
    (
        "lower",
        "strain energy density",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "ep17_bilobe_witness_case_v1"
        / "ep17_bilobe_witness__band220_260"
        / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_lower_strain_energy_density.png",
    ),
    (
        "lower",
        "von Mises stress",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "ep17_bilobe_witness_case_v1"
        / "ep17_bilobe_witness__band220_260"
        / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_lower_von_mises_stress.png",
    ),
    (
        "upper",
        "strain energy density",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "ep17_bilobe_witness_case_v1"
        / "ep17_bilobe_witness__band220_260"
        / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_upper_strain_energy_density.png",
    ),
    (
        "upper",
        "von Mises stress",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "ep17_bilobe_witness_case_v1"
        / "ep17_bilobe_witness__band220_260"
        / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_upper_von_mises_stress.png",
    ),
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def crop_panel(img: Image.Image) -> Image.Image:
    w, h = img.size
    return img.crop((70, 58, w - 62, h - 68))


def open_image(path: Path) -> Image.Image:
    # Windows long-path helper: PIL can be picky on deeply nested thesis artifacts.
    abs_path = path.resolve()
    raw = str(abs_path)
    if raw.startswith("D:\\"):
        raw = "\\\\?\\" + raw
    return Image.open(raw).convert("RGB")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    title_font = load_font(40)
    col_font = load_font(24)
    row_font = load_font(30)
    note_font = load_font(18)

    thumb_w = 760
    thumb_h = 560
    left_margin = 170
    right_margin = 36
    top_margin = 120
    bottom_margin = 68
    row_gap = 42
    col_gap = 30
    label_h = 34

    canvas_w = left_margin + thumb_w * 2 + col_gap + right_margin
    canvas_h = top_margin + thumb_h * 2 + label_h * 2 + row_gap + bottom_margin
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    draw.text((canvas_w / 2, 24), "ep17 bilobe witness field maps", fill="black", font=title_font, anchor="ma")
    draw.text((canvas_w - right_margin, canvas_h - 22), "solid.Ws / solid.mises", fill="#666666", font=note_font, anchor="rd")

    col_x = [left_margin + thumb_w / 2, left_margin + thumb_w + col_gap + thumb_w / 2]
    for x, text in zip(col_x, ["strain energy density", "von Mises stress"]):
        draw.text((x, 78), text, fill="#222222", font=col_font, anchor="mm")

    y = top_margin
    for row_label in ["lower", "upper"]:
        draw.text((24, y + thumb_h / 2), row_label, fill="black", font=row_font, anchor="lm")
        x = left_margin
        for panel_row, panel_col, path in [p for p in PANELS if p[0] == row_label]:
            img = crop_panel(open_image(path))
            img = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            canvas.paste(img, (x, y))
            x += thumb_w + col_gap
        y += thumb_h + label_h + row_gap

    out = OUT_DIR / "ep17_witness_field_maps_composite_v1.png"
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
