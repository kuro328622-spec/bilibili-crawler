# client.py —— 请求模块：限速 + 重试 + 自动 WBI 签名
import time

import requests

import config
from crypto import get_mixin_key, sign_params

# 本地凭证（cookie）。没有 config_local.py 也能跑（匿名），只是数据可能受限
try:
    import config_local
    COOKIE = getattr(config_local, "COOKIE", "")
except ImportError:
    COOKIE = ""


class BiliClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Referer": config.REFERER,
            "Origin": config.ORIGIN,
        })
        if COOKIE:
            self.session.headers["Cookie"] = COOKIE
        self.last_request_time = 0     # 上次请求时刻（限速用）
        self._mixin_key = None         # WBI 混合密钥缓存

    # ---------- 限速：两个请求之间至少隔 RATE_LIMIT 秒 ----------
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < config.RATE_LIMIT:
            time.sleep(config.RATE_LIMIT - elapsed)

    # ---------- 拿 WBI 混合密钥（从 nav 接口，缓存起来避免重复请求）----------
    def get_mixin_key(self):
        if self._mixin_key is None:
            # 注意：匿名请求 nav 会返回 code=-101（未登录），但 wbi_img 照样给
            # 所以这里不检查 code
            resp = self._get(config.NAV_URL, check_code=False)
            wbi_img = resp["data"]["wbi_img"]
            # 密钥藏在图片 URL 的文件名里
            img_key = wbi_img["img_url"].rsplit("/", 1)[-1].split(".")[0]
            sub_key = wbi_img["sub_url"].rsplit("/", 1)[-1].split(".")[0]
            self._mixin_key = get_mixin_key(img_key, sub_key)
        return self._mixin_key

    # ---------- 底层 GET：限速 + 重试 + 风控处理 ----------
    def _get(self, url, params=None, check_code=True):
        for attempt in range(1, config.MAX_RETRY + 1):
            self._rate_limit()
            try:
                resp = self.session.get(url, params=params, timeout=config.TIMEOUT)
                self.last_request_time = time.time()

                # 412 = 被风控拦截：重试只会更糟，直接报错
                if resp.status_code == 412:
                    raise RuntimeError("被风控拦截（HTTP 412）——降低频率或检查签名/凭证")

                resp.raise_for_status()
                data = resp.json()

                # B站约定：code != 0 表示业务失败（部分接口允许忽略）
                if check_code and data.get("code") != 0:
                    raise RuntimeError(f"接口报错 code={data.get('code')} message={data.get('message')}")
                return data

            except Exception:
                if attempt == config.MAX_RETRY:
                    raise
                time.sleep(config.RATE_LIMIT * config.RETRY_BACKOFF ** attempt)

    # ---------- 对外主方法：wbi 接口自动签名 ----------
    def get(self, url, params=None):
        params = dict(params or {})
        if "/wbi/" in url:                       # 是 wbi 接口 → 自动签名
            params = sign_params(params, self.get_mixin_key())
        return self._get(url, params)

    def close(self):
        self.session.close()


# ===== 自测：拿影视飓风的第一页投稿视频 =====
if __name__ == "__main__":
    c = BiliClient()
    data = c.get(config.SPACE_ARC_URL, {
        "mid": config.UP_MID,
        "pn": 1,
        "ps": config.PAGE_SIZE,
        "order": "pubdate",
        "platform": "web",
        "web_location": "333.1387",
    })
    page = data["data"]["page"]
    vlist = data["data"]["list"]["vlist"]
    print(f"共 {page['count']} 个视频，本页 {len(vlist)} 个")
    for v in vlist[:5]:
        print(f"  {v['bvid']}  {v['title']}  播放 {v['play']}  时长 {v['length']}")
    c.close()
