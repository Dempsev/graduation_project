from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "output" / "thesis_charts" / "chapter6" / "physical_mechanism" / "ep17_bilobe_witness_case_v1"


PANELS = {
    ("lower", "mode shape"): ROOT
    / "output"
    / "thesis_charts"
    / "chapter6"
    / "physical_mechanism"
    / "ep17_bilobe_witness_case_v1"
    / "mode_shapes"
    / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_lower_edge.png",
    ("lower", "strain energy density"): ROOT
    / "data"
    / "analysis"
    / "ch6_mechanism_field_maps_v1"
    / "ep17_bilobe_witness_case_v1"
    / "ep17_bilobe_witness__band220_260"
    / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_lower_strain_energy_density.png",
    ("lower", "von Mises stress"): ROOT
    / "data"
    / "analysis"
    / "ch6_mechanism_field_maps_v1"
    / "ep17_bilobe_witness_case_v1"
    / "ep17_bilobe_witness__band220_260"
    / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_lower_von_mises_stress.png",
    ("upper", "mode shape"): ROOT
    / "output"
    / "thesis_charts"
    / "chapter6"
    / "physical_mechanism"
    / "ep17_bilobe_witness_case_v1"
    / "mode_shapes"
    / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_upper_edge.png",
    ("upper", "strain energy density"): ROOT
    / "data"
    / "analysis"
    / "ch6_mechanism_field_maps_v1"
    / "ep17_bilobe_witness_case_v1"
    / "ep17_bilobe_witness__band220_260"
    / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_upper_strain_energy_density.png",
    ("upper", "von Mises stress"): ROOT
    / "data"
    / "analysis"
    / "ch6_mechanism_field_maps_v1"
    / "ep17_bilobe_witness_case_v1"
    / "ep17_bilobe_witness__band220_260"
    / "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_upper_von_mises_stress.png",
}


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
    abs_path = path.resolve()
    raw = str(abs_path)
    if raw.startswith("D:\\"):
        raw = "\\\\?\\" + raw
    return Image.open(raw).convert("RGB")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    title_font = load_font(40)
    panel_font = load_font(22)
    note_font = load_font(18)
    row_font = load_font(28)

    cell_w = 520
    cell_h = 430
    left_margin = 150
    right_margin = 36
    top_margin = 118
    bottom_margin = 68
    col_gap = 28
    row_gap = 50
    label_h = 36

    canvas_w = left_margin + cell_w * 3 + col_gap * 2 + right_margin
    canvas_h = top_margin + cell_h * 2 + label_h * 2 + row_gap + bottom_margin
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    draw.text((canvas_w / 2, 22), "ep17 witness: mode shapes and field maps", fill="black", font=title_font, anchor="ma")
    draw.text((canvas_w - right_margin, canvas_h - 22), "solid.Ws / solid.mises", fill="#666666", font=note_font, anchor="rd")

    col_centers = [
        left_margin + cell_w / 2,
        left_margin + cell_w + col_gap + cell_w / 2,
        left_margin + 2 * cell_w + 2 * col_gap + cell_w / 2,
    ]
    for x, text in zip(col_centers, ["mode shape", "strain energy density", "von Mises stress"]):
        draw.text((x, 76), text, fill="#222222", font=panel_font, anchor="mm")

    row_specs = ["lower", "upper"]
    for row_idx, edge in enumerate(row_specs):
        draw.text((24, top_margin + row_idx * (cell_h + label_h + row_gap) + cell_h / 2), edge, fill="black", font=row_font, anchor="lm")
        for col_idx, key in enumerate(["mode shape", "strain energy density", "von Mises stress"]):
            x = left_margin + col_idx * (cell_w + col_gap)
            y = top_margin + row_idx * (cell_h + label_h + row_gap)
            img = crop_panel(open_image(PANELS[(edge, key)]))
            img = img.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
            canvas.paste(img, (x, y))
            caption = {
                "mode shape": f"{edge} edge mode shape",
                "strain energy density": f"{edge} edge strain energy density",
                "von Mises stress": f"{edge} edge von Mises stress",
            }[key]
            draw.text((x + cell_w / 2, y + cell_h + 15), caption, fill="#111111", font=note_font, anchor="mm")

    out = OUT_DIR / "ep17_mode_and_field_2x3_composite_v1.png"
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
