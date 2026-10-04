# config.py —— 项目配置
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # 脚本所在目录，路径不依赖运行目录

# ===== ① 接口地址 =====
NAV_URL = "https://api.bilibili.com/x/web-interface/nav"            # 拿 WBI 密钥
SPACE_ARC_URL = "https://api.bilibili.com/x/space/wbi/arc/search"   # UP主投稿列表（wbi 签名）
REPLY_URL = "https://api.bilibili.com/x/v2/reply/wbi/main"          # 评论（wbi 签名）

# ===== ② 爬取目标 =====
UP_MID = 946974            # 影视飓风的 mid
PAGE_SIZE = 25             # 每页视频数（实测服务器可能压到 25）
COMMENT_PAGES = 3          # 每个视频爬几页评论（0=不爬评论）
COMMENT_LIMIT_VIDEOS = 50  # 只对最近 N 个视频爬评论（避免量太大）

# ===== ③ 礼貌爬取 =====
RATE_LIMIT = 1.0           # 每个请求间隔秒数
MAX_RETRY = 3              # 失败重试次数
RETRY_BACKOFF = 2          # 重试等待倍数
TIMEOUT = 10

# ===== ④ 请求头 =====
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
REFERER = "https://space.bilibili.com/946974/upload/video"
ORIGIN = "https://space.bilibili.com"

# ===== ⑤ 存储 =====
DB_PATH = os.path.join(BASE_DIR, "data", "bilibili.db")
