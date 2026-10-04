# analyze.py —— 数据分析：统计 + 可视化
import os
import sqlite3

import matplotlib
matplotlib.use("Agg")            # 不弹窗，直接存图片文件
import matplotlib.pyplot as plt

import config

# 中文字体（Windows 自带）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

CHART_DIR = os.path.join(config.BASE_DIR, "charts")
os.makedirs(CHART_DIR, exist_ok=True)


def dur_to_sec(s):
    """把 '09:43' 转成秒"""
    try:
        p = [int(x) for x in s.split(":")]
        return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]
    except Exception:
        return None


def main():
    conn = sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True)

    n_v, n_c = conn.execute("SELECT (SELECT COUNT(*) FROM videos), (SELECT COUNT(*) FROM comments)").fetchone()
    lo, hi, total = conn.execute("SELECT MIN(created), MAX(created), SUM(play) FROM videos").fetchone()
    print(f"视频 {n_v} 个 | 评论 {n_c} 条 | 总播放 {total:,}")
    print(f"时间跨度: {lo} ~ {hi}\n")

    # ===== ① 年度趋势：投稿量 + 平均播放量 =====
    rows = conn.execute("""
        SELECT strftime('%Y', datetime(created,'unixepoch','localtime')) AS y,
               COUNT(*), AVG(play)
        FROM videos GROUP BY y ORDER BY y
    """).fetchall()
    years = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    avg_play = [int(r[2]) for r in rows]

    print("=== 年度趋势 ===")
    for y, c, a in rows:
        print(f"  {y}: {c:>3} 个视频，平均播放 {a:>12,.0f}")

    fig, ax1 = plt.subplots(figsize=(11, 5))
    ax1.bar(years, counts, color="#8ab4f8", label="投稿数")
    ax1.set_ylabel("投稿数", color="#3b6fd4")
    ax1.set_xlabel("年份")
    ax2 = ax1.twinx()
    ax2.plot(years, avg_play, color="#e05c5c", marker="o", linewidth=2, label="平均播放量")
    ax2.set_ylabel("平均播放量", color="#e05c5c")
    plt.title("影视飓风 投稿量与平均播放量趋势（2015-至今）")
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "01_yearly_trend.png"), dpi=130)
    plt.close(fig)

    # ===== ② 时长 vs 播放量 =====
    data = [(dur_to_sec(l), p) for l, p in
            conn.execute("SELECT length, play FROM videos").fetchall()]
    data = [(d / 60, p) for d, p in data if d and p]
    xs = [d for d, _ in data]
    ys = [p for _, p in data]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(xs, ys, s=14, alpha=0.5, color="#2e9e6b")
    ax.set_xlabel("视频时长（分钟）")
    ax.set_ylabel("播放量")
    ax.set_title("视频时长 vs 播放量")
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "02_duration_vs_play.png"), dpi=130)
    plt.close(fig)

    # ===== ③ 播放量 Top 10 =====
    top = conn.execute("SELECT title, play FROM videos ORDER BY play DESC LIMIT 10").fetchall()
    titles = [t[:18] + "…" if len(t) > 18 else t for t, _ in top][::-1]
    plays = [p for _, p in top][::-1]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(titles, plays, color="#f4a261")
    ax.set_xlabel("播放量")
    ax.set_title("播放量 Top 10 视频")
    for i, v in enumerate(plays):
        ax.text(v, i, f" {v/10000:.0f}万", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "03_top10_play.png"), dpi=130)
    plt.close(fig)

    # ===== ④ 热门评论 Top 10 =====
    print("\n=== 评论点赞 Top 10 ===")
    for u, c, l in conn.execute(
            "SELECT user_name, content, like_cnt FROM comments ORDER BY like_cnt DESC LIMIT 10"):
        print(f"  {l:>6} 赞 | {u}: {c[:36]}")

    print(f"\n图表已保存到: {CHART_DIR}")
    conn.close()


if __name__ == "__main__":
    main()
