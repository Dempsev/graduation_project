import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ========== 1) 读入 ==========
CSV_PATH = "D:\\graduation_project\\model\\tbl1_exports\\tbl1_20260125_204217874.csv"   # <- 改成你的路径/文件名
OUT_DIR = "post_out"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "bands_by_amp"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "plots"), exist_ok=True)

# 你的 csv 没表头，且可能有以 % 开头的注释行
df = pd.read_csv(
    CSV_PATH,
    header=None,
    comment="%",
    names=["k", "amp", "eigfreq", "freq"]
)

# ========== 2) 处理复数（把 i 换成 j），取实部 ==========
def to_real(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    # COMSOL 常见格式：...E-14i 或 ...+...i
    s = s.replace("i", "j")
    try:
        z = complex(s)
        return float(np.real(z))
    except Exception:
        # 有时就是纯实数
        try:
            return float(s)
        except Exception:
            return np.nan

df["freq_real"] = df["freq"].apply(to_real)
df = df.dropna(subset=["k", "amp", "freq_real"]).copy()

# 保险：转成 float
df["k"] = df["k"].astype(float)
df["amp"] = df["amp"].astype(float)
df["freq_real"] = df["freq_real"].astype(float)

# ========== 3) 给每个 (amp,k) 内的频率排序并编号为 band_index ==========
# band_index 从 1 开始：band1 最低频
df = df.sort_values(["amp", "k", "freq_real"]).copy()
df["band_index"] = df.groupby(["amp", "k"]).cumcount() + 1

# 每个 (amp,k) 实际有多少条带（一般是你设置的“所需特征频率数”，比如 8）
band_count = int(df["band_index"].max())
print(f"[INFO] Detected band_count = {band_count}")

# ========== 4) 生成每个 amp 的 band 表（k 为行，band1..bandM 为列） ==========
bands = (
    df.pivot_table(index=["amp", "k"], columns="band_index", values="freq_real", aggfunc="min")
    .reset_index()
    .sort_values(["amp", "k"])
)

# 统一列名：band1...bandM
bands.columns = ["amp", "k"] + [f"band{int(c)}" for c in bands.columns[2:]]

# ========== 5) 计算带隙 + 画图 ==========
summary_rows = []

for amp_val, g in bands.groupby("amp"):
    g = g.sort_values("k").reset_index(drop=True)

    band_cols = [c for c in g.columns if c.startswith("band")]
    M = len(band_cols)
    if M < 2:
        continue

    # --- 画能带图 ---
    plt.figure()
    for c in band_cols:
        plt.plot(g["k"].values, g[c].values)
    plt.xlabel("k")
    plt.ylabel("Frequency (Hz)")
    plt.title(f"Band structure (amp={amp_val:g})")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "plots", f"bands_amp_{amp_val:g}.png"), dpi=200)
    plt.close()

    # --- 计算相邻带隙 ---
    # gap_j = min(band_{j+1}) - max(band_j)
    gaps = []
    for j in range(1, M):
        lower = g[f"band{j}"].values
        upper = g[f"band{j+1}"].values
        if np.all(np.isnan(lower)) or np.all(np.isnan(upper)):
            continue
        lower_max = np.nanmax(lower)
        upper_min = np.nanmin(upper)
        gap = upper_min - lower_max
        gaps.append((j, gap, lower_max, upper_min))

    # 正带隙（>0）才算 bandgap
    pos_gaps = [t for t in gaps if t[1] > 0]

    # 保存该 amp 的 band 表
    g.to_csv(os.path.join(OUT_DIR, "bands_by_amp", f"bands_amp_{amp_val:g}.csv"), index=False)

    if not pos_gaps:
        summary_rows.append({
            "amp": amp_val,
            "has_gap": False,
            "max_gap_Hz": 0.0,
            "gap_between_bands": "",
            "gap_lower_edge_Hz": np.nan,
            "gap_upper_edge_Hz": np.nan,
            "gap_center_Hz": np.nan,
            "relative_gap": np.nan
        })
        continue

    # 取最大带隙
    j_best, gap_best, lower_edge, upper_edge = max(pos_gaps, key=lambda x: x[1])
    center = 0.5 * (lower_edge + upper_edge)
    rel_gap = gap_best / center if center != 0 else np.nan

    summary_rows.append({
        "amp": amp_val,
        "has_gap": True,
        "max_gap_Hz": gap_best,
        "gap_between_bands": f"{j_best} - {j_best+1}",
        "gap_lower_edge_Hz": lower_edge,
        "gap_upper_edge_Hz": upper_edge,
        "gap_center_Hz": center,
        "relative_gap": rel_gap
    })

summary = pd.DataFrame(summary_rows).sort_values("amp")
summary.to_csv(os.path.join(OUT_DIR, "bandgap_summary.csv"), index=False)

print("[DONE] Outputs written to:", OUT_DIR)
print(" - bandgap_summary.csv")
print(" - bands_by_amp/*.csv")
print(" - plots/*.png")