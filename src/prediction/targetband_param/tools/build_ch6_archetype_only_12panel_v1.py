from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / "output" / "thesis_charts" / "chapter6" / "physical_mechanism" / "ch6_mechanism_field_maps_v1"


def p(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


ROWS = [
    (
        "bilobe",
        [
            ("lower Ws", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band220_260__bilobe__ep195", "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_lower_strain_energy_density.png")),
            ("lower mises", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band220_260__bilobe__ep195", "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_lower_von_mises_stress.png")),
            ("upper Ws", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band220_260__bilobe__ep195", "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_upper_strain_energy_density.png")),
            ("upper mises", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band220_260__bilobe__ep195", "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_upper_von_mises_stress.png")),
        ],
    ),
    (
        "asym",
        [
            ("lower Ws", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band240_280__asym__ep130", "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_lower_strain_energy_density.png")),
            ("lower mises", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band240_280__asym__ep130", "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_lower_von_mises_stress.png")),
            ("upper Ws", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band240_280__asym__ep130", "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_upper_strain_energy_density.png")),
            ("upper mises", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band240_280__asym__ep130", "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_upper_von_mises_stress.png")),
        ],
    ),
    (
        "neck",
        [
            ("lower Ws", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band240_280__neck__ep253", "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_lower_strain_energy_density.png")),
            ("lower mises", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band240_280__neck__ep253", "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_lower_von_mises_stress.png")),
            ("upper Ws", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band240_280__neck__ep253", "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_upper_strain_energy_density.png")),
            ("upper mises", p("data", "analysis", "ch6_mechanism_field_maps_v1", "shape_archetype_targetband_mode_shapes_v1", "band240_280__neck__ep253", "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_upper_von_mises_stress.png")),
        ],
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    title_font = load_font(40)
    row_font = load_font(28)
    col_font = load_font(20)
    note_font = load_font(20)

    thumb_w = 360
    thumb_h = 330
    left_margin = 160
    right_margin = 36
    top_margin = 112
    bottom_margin = 66
    row_gap = 48
    col_gap = 26
    label_h = 34

    canvas_w = left_margin + thumb_w * 4 + col_gap * 3 + right_margin
    canvas_h = top_margin + (thumb_h + label_h) * 3 + row_gap * 2 + bottom_margin
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    draw.text((canvas_w / 2, 22), "Archetype field maps for Chapter 6", fill="black", font=title_font, anchor="ma")
    draw.text((canvas_w - right_margin, canvas_h - 22), "solid.Ws / solid.mises", fill="#666666", font=note_font, anchor="rd")

    col_centers = [
        left_margin + thumb_w * 0.5,
        left_margin + thumb_w * 1.5 + col_gap,
        left_margin + thumb_w * 2.5 + col_gap * 2,
        left_margin + thumb_w * 3.5 + col_gap * 3,
    ]
    for x, text in zip(col_centers, ["lower Ws", "lower mises", "upper Ws", "upper mises"]):
        draw.text((x, 74), text, fill="#222222", font=col_font, anchor="mm")

    y = top_margin
    for row_label, panels in ROWS:
        draw.text((20, y + thumb_h / 2), row_label, fill="black", font=row_font, anchor="lm")
        x = left_margin
        for _, path in panels:
            img = crop_panel(Image.open(path).convert("RGB"))
            img = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            canvas.paste(img, (x, y))
            x += thumb_w + col_gap
        y += thumb_h + label_h + row_gap

    out = OUT_DIR / "archetype_field_maps_12panel_composite_v1.png"
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
