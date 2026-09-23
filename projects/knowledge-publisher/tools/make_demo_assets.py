"""生成示例文章用到的演示图片（梯度下降示意）。

用法：kp 环境下 python tools/make_demo_assets.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "assets" / "images"
TARGET.mkdir(parents=True, exist_ok=True)


def gradient_descent() -> None:
    x = np.arange(-4, 4.01, 0.01)
    y = x ** 2
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot(x, y, color="#1667d9", lw=2.5)
    pts = [3.0, 2.0, 1.2, 0.6, 0.2, 0.05]
    ax.scatter(pts, [p * p for p in pts], color="#f04438", zorder=5, s=46)
    for i in range(len(pts) - 1):
        ax.annotate(
            "", xy=(pts[i + 1], pts[i + 1] ** 2), xytext=(pts[i], pts[i] ** 2),
            arrowprops=dict(arrowstyle="-|>", color="#f04438", lw=1.6),
        )
    ax.set_title("梯度下降：沿最陡方向一步步下山", fontsize=13)
    ax.set_xlabel("参数 θ")
    ax.set_ylabel("损失 J(θ)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(TARGET / "gradient.png")
    plt.close(fig)
    print("✓ assets/images/gradient.png")


if __name__ == "__main__":
    import numpy as np  # noqa: PLC0415

    gradient_descent()
