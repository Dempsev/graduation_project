import pandas as pd
import matplotlib.pyplot as plt

bg = pd.read_csv("D:\\graduation_project\\post_out\\bandgap_summary.csv")

# 1) 带隙宽度 vs amp
plt.figure()
plt.plot(bg["amp"], bg["max_gap_Hz"], marker="o")
plt.xlabel("amp")
plt.ylabel("Bandgap width (Hz)")
plt.title("Bandgap width vs amp")
plt.grid(True)
plt.savefig("bandgap_width_vs_amp.png", dpi=300, bbox_inches="tight")
plt.show()

# 2) 带隙上下边界 vs amp
plt.figure()
plt.plot(bg["amp"], bg["gap_lower_edge_Hz"], marker="o", label="Lower edge")
plt.plot(bg["amp"], bg["gap_upper_edge_Hz"], marker="o", label="Upper edge")
plt.xlabel("amp")
plt.ylabel("Frequency (Hz)")
plt.title("Bandgap edges vs amp")
plt.legend()
plt.grid(True)
plt.savefig("bandgap_edges_vs_amp.png", dpi=300, bbox_inches="tight")
plt.show()