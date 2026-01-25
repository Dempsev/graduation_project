# -*- coding: utf-8 -*-
import os  
import numpy as np
import matplotlib.pyplot as plt

# 需要：pip install scikit-image
from skimage import measure

txt_path = r"D:\graduation_project\discrete_database\states\ep31288_step75.txt"   
csv_dir = r"D:\graduation_project\discrete_database\data_point"
png_dir = r"D:\graduation_project\discrete_database\shape"

base_name = os.path.splitext(os.path.basename(txt_path))[0]
out_csv  = os.path.join(csv_dir, f"{base_name}_contour_xy.csv")
out_png  = os.path.join(png_dir, f"{base_name}_preview.png")



# 像素尺寸（把“1个格子”映射成多少米/毫米）
# 先用 1.0（无量纲）测试
pixel_size = 1.0

# 是否把坐标原点平移到矩阵中心（建议 True：更方便叠加到单胞中心）
center_origin = True

# 轮廓简化开关：True 时会简单抽稀点（更利于 COMSOL）
simplify = True
keep_every = 2  # 抽稀：每隔几个点保留一个（2~5 之间试）
# =================================


def load_binary_txt(path: str) -> np.ndarray:
    #"""读取 txt 0/1 矩阵（支持空格分隔）"""
    A = np.loadtxt(path)
    # 容错：有些文件可能是 0/1 浮点
    A = (A > 0.5).astype(float)
    return A


def choose_largest_contour(contours):
    #"""选择最长的一条轮廓（通常就是主结构外边界）"""
    if not contours:
        return None
    lengths = [len(c) for c in contours]
    return contours[int(np.argmax(lengths))]


def contour_to_xy(contour_rc: np.ndarray,
                  shape_hw,
                  pixel_size: float,
                  center_origin: bool) -> np.ndarray:
    """
    skimage.find_contours 返回 (row, col) 的浮点点列（沿像素边界插值）。
    转成 (x, y);
      x 对应 col,y 对应 row(但我们习惯 y 轴向上，所以给 y 一个负号更直观)
    """
    H, W = shape_hw
    r = contour_rc[:, 0]
    c = contour_rc[:, 1]

    if center_origin:
        # 把(0,0)移到矩阵中心
        x = (c - (W - 1) / 2.0) * pixel_size
        y = - (r - (H - 1) / 2.0) * pixel_size
    else:
        x = c * pixel_size
        y = -r * pixel_size

    xy = np.column_stack([x, y])
    return xy


def main():
    A = load_binary_txt(txt_path)

    # 提轮廓：level=0.5 代表 0/1 交界线
    contours = measure.find_contours(A, level=0.5)
    main_contour = choose_largest_contour(contours)

    if main_contour is None:
        raise RuntimeError("没有找到轮廓：检查 txt 是否为 0/1 矩阵，或矩阵里是否存在 1。")

    # 简单抽稀（可选）
    if simplify and keep_every > 1:
        main_contour = main_contour[::keep_every]

    xy = contour_to_xy(main_contour, A.shape, pixel_size, center_origin)

    # 导出 CSV（两列：x,y）
    np.savetxt(out_csv, xy, delimiter=",", header="x,y", comments="", fmt="%.8g")

    # 画预览图
    plt.figure()
    plt.imshow(A, origin="upper")  # 原矩阵显示
    plt.plot(main_contour[:, 1], main_contour[:, 0], linewidth=2)  # 注意这里还是 (col,row)
    plt.title("Binary matrix + extracted contour")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()

    print("Done!")
    print(f"CSV saved to: {out_csv}")
    print(f"Preview saved to: {out_png}")
    print(f"Contour points: {xy.shape[0]}")


if __name__ == "__main__":
    main()
