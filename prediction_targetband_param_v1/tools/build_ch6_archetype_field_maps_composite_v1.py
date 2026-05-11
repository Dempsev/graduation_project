from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "output" / "thesis_charts" / "chapter6" / "physical_mechanism" / "ch6_mechanism_field_maps_v1"


CASES = {
    (
        "bilobe",
        "lower",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band220_260__bilobe__ep195"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_lower_strain_energy_density.png",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band220_260__bilobe__ep195"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_lower_von_mises_stress.png",
    ),
    (
        "bilobe",
        "upper",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band220_260__bilobe__ep195"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_upper_strain_energy_density.png",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band220_260__bilobe__ep195"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_upper_von_mises_stress.png",
    ),
    (
        "asym",
        "lower",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band240_280__asym__ep130"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_lower_strain_energy_density.png",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band240_280__asym__ep130"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_lower_von_mises_stress.png",
    ),
    (
        "asym",
        "upper",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band240_280__asym__ep130"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_upper_strain_energy_density.png",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band240_280__asym__ep130"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_upper_von_mises_stress.png",
    ),
    (
        "neck",
        "lower",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band240_280__neck__ep253"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_lower_strain_energy_density.png",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band240_280__neck__ep253"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_lower_von_mises_stress.png",
    ),
    (
        "neck",
        "upper",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band240_280__neck__ep253"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_upper_strain_energy_density.png",
        ROOT
        / "data"
        / "analysis"
        / "ch6_mechanism_field_maps_v1"
        / "shape_archetype_targetband_mode_shapes_v1"
        / "band240_280__neck__ep253"
        / "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_upper_von_mises_stress.png",
    ),
}


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def crop_panel(img: Image.Image) -> Image.Image:
    w, h = img.size
    # Remove the large COMSOL title and outer whitespace, while keeping the plot body.
    left = 70
    top = 58
    right = w - 62
    bottom = h - 68
    return img.crop((left, top, right, bottom))


def make_composite(edge: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    panels: list[list[Image.Image]] = []
    selected_cases = [item for item in CASES if item[1] == edge]
    for _, _, ws_path, mises_path in selected_cases:
        ws = crop_panel(Image.open(ws_path).convert("RGB"))
        mises = crop_panel(Image.open(mises_path).convert("RGB"))
        panels.append([ws, mises])

    target_w = 760
    target_h = 690
    resized: list[list[Image.Image]] = []
    for row in panels:
        resized.append([p.resize((target_w, target_h), Image.Resampling.LANCZOS) for p in row])

    left_margin = 180
    right_margin = 70
    top_margin = 140
    bottom_margin = 70
    col_gap = 40
    row_gap = 58

    canvas_w = left_margin + target_w * 2 + col_gap + right_margin
    canvas_h = top_margin + target_h * 3 + row_gap * 2 + bottom_margin

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    font_title = load_font(42)
    font_row = load_font(36)
    font_col = load_font(32)
    font_note = load_font(24)

    col1_center = left_margin + target_w / 2
    col2_center = left_margin + target_w + col_gap + target_w / 2

    draw.text((canvas_w / 2, 24), "Archetype field maps for Chapter 6", fill="black", font=font_title, anchor="ma")
    draw.text((col1_center, 78), "strain energy density", fill="#222222", font=font_col, anchor="mm")
    draw.text((col2_center, 78), "von Mises stress", fill="#222222", font=font_col, anchor="mm")
    draw.text((canvas_w - right_margin - 6, canvas_h - 24), "Representative lower-edge cases", fill="#666666", font=font_note, anchor="rd")

    y = top_margin
    for (row_label, _, _, _), row in zip(selected_cases, resized):
        x = left_margin
        canvas.paste(row[0], (x, y))
        x += target_w + col_gap
        canvas.paste(row[1], (x, y))
        draw.text((22, y + target_h / 2), row_label, fill="black", font=font_row, anchor="lm")
        y += target_h + row_gap

    out_path = OUT_DIR / f"archetype_field_maps_{edge}_composite_v1.png"
    canvas.save(out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edge", choices=["lower", "upper"], default="lower")
    args = parser.parse_args()
    out = make_composite(args.edge)
    print(out)


if __name__ == "__main__":
    main()
