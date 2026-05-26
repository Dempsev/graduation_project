from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / "output" / "thesis_charts" / "chapter6" / "physical_mechanism" / "ch6_mechanism_field_maps_v1"


def p(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


PANELS = [
    [
        (
            "band180_220 ep248 lower",
            p(
                "data",
                "analysis",
                "ch6_mechanism_field_maps_v1",
                "canonical_mode_shapes_v1",
                "band180_220_ep248",
                "stage4_validation_targetband_local_robustness_v1_band180_220_ep248_center_lower_strain_energy_density.png",
            ),
        ),
        (
            "band200_240 ep193 lower",
            p(
                "data",
                "analysis",
                "ch6_mechanism_field_maps_v1",
                "canonical_mode_shapes_v1",
                "band200_240_ep193",
                "stage4_validation_targetband_local_robustness_v1_band200_240_ep193_center_lower_strain_energy_density.png",
            ),
        ),
        (
            "band220_260 ep253 lower",
            p(
                "data",
                "analysis",
                "ch6_mechanism_field_maps_v1",
                "canonical_mode_shapes_v1",
                "band220_260_ep253",
                "stage4_validation_targetband_local_robustness_v1_band220_260_ep253_center_lower_strain_energy_density.png",
            ),
        ),
        (
            "band240_280 ep253 lower",
            p(
                "data",
                "analysis",
                "ch6_mechanism_field_maps_v1",
                "canonical_mode_shapes_v1",
                "band240_280_ep253",
                "stage4_validation_targetband_local_robustness_v1_band240_280_ep253_center_lower_strain_energy_density.png",
            ),
        ),
    ],
    [
        (
            "ep17 lower",
            p(
                "output",
                "thesis_charts",
                "chapter6",
                "physical_mechanism",
                "ep17_bilobe_witness_case_v1",
                "mode_shapes",
                "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_lower_edge.png",
            ),
        ),
        (
            "ep17 upper",
            p(
                "output",
                "thesis_charts",
                "chapter6",
                "physical_mechanism",
                "ep17_bilobe_witness_case_v1",
                "mode_shapes",
                "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center_upper_edge.png",
            ),
        ),
        (
            "bilobe lower",
            p(
                "output",
                "thesis_charts",
                "chapter6",
                "physical_mechanism",
                "shape_archetype_targetband_mode_shapes_v1",
                "band220_260__bilobe__ep195",
                "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_lower_edge.png",
            ),
        ),
        (
            "bilobe upper",
            p(
                "output",
                "thesis_charts",
                "chapter6",
                "physical_mechanism",
                "shape_archetype_targetband_mode_shapes_v1",
                "band220_260__bilobe__ep195",
                "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center_upper_edge.png",
            ),
        ),
    ],
    [
        (
            "asym lower",
            p(
                "output",
                "thesis_charts",
                "chapter6",
                "physical_mechanism",
                "shape_archetype_targetband_mode_shapes_v1",
                "band240_280__asym__ep130",
                "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_lower_edge.png",
            ),
        ),
        (
            "asym upper",
            p(
                "output",
                "thesis_charts",
                "chapter6",
                "physical_mechanism",
                "shape_archetype_targetband_mode_shapes_v1",
                "band240_280__asym__ep130",
                "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center_upper_edge.png",
            ),
        ),
        (
            "neck lower",
            p(
                "output",
                "thesis_charts",
                "chapter6",
                "physical_mechanism",
                "shape_archetype_targetband_mode_shapes_v1",
                "band240_280__neck__ep253",
                "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_lower_edge.png",
            ),
        ),
        (
            "neck upper",
            p(
                "output",
                "thesis_charts",
                "chapter6",
                "physical_mechanism",
                "shape_archetype_targetband_mode_shapes_v1",
                "band240_280__neck__ep253",
                "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_upper_edge.png",
            ),
        ),
    ],
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
    # Trim COMSOL's long title and the extra outer whitespace.
    return img.crop((70, 58, w - 62, h - 68))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    title_font = load_font(40)
    row_font = load_font(28)
    panel_font = load_font(18)
    note_font = load_font(20)

    thumb_w = 500
    thumb_h = 455
    left_margin = 180
    right_margin = 35
    top_margin = 118
    bottom_margin = 70
    row_gap = 56
    col_gap = 28
    label_h = 42

    canvas_w = left_margin + thumb_w * 4 + col_gap * 3 + right_margin
    canvas_h = top_margin + (thumb_h + label_h) * 3 + row_gap * 2 + bottom_margin
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (canvas_w / 2, 24),
        "Representative strain energy density maps for Chapter 6",
        fill="black",
        font=title_font,
        anchor="ma",
    )
    draw.text(
        (canvas_w - right_margin, canvas_h - 24),
        "solid.Ws",
        fill="#666666",
        font=note_font,
        anchor="rd",
    )

    row_labels = ["canonical cases", "ep17 + bilobe", "asym + neck"]

    y = top_margin
    for row_idx, row in enumerate(PANELS):
        draw.text((24, y + thumb_h / 2), row_labels[row_idx], fill="black", font=row_font, anchor="lm")
        x = left_margin
        for label, path in row:
            img = crop_panel(Image.open(path).convert("RGB"))
            img = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            canvas.paste(img, (x, y))
            draw.text((x + thumb_w / 2, y + thumb_h + 16), label, fill="black", font=panel_font, anchor="mm")
            x += thumb_w + col_gap
        y += thumb_h + label_h + row_gap

    out = OUT_DIR / "archetype_ws_12panel_composite_v1.png"
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
