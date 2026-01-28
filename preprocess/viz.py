# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt


def plot_preview(
    A,
    raw_rc,
    approx_rc,
    post_rc,
    out_png,
    title,
    show_legend=True,
):
    plt.figure()
    plt.imshow(A, origin="upper")
    if post_rc is not None:
        plt.plot(post_rc[:, 1], post_rc[:, 0], linewidth=2, label="postprocessed")
    if raw_rc is not None:
        plt.plot(raw_rc[:, 1], raw_rc[:, 0], linewidth=1, label="raw")
    if approx_rc is not None:
        plt.plot(approx_rc[:, 1], approx_rc[:, 0], linewidth=1, label="approx")
    if show_legend:
        plt.legend(loc="best", fontsize=8)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()
