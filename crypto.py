# crypto.py —— B站 WBI 签名
#
# 算法来源：从混淆 JS 里逆向出来，并用 Python 复现验证过（签名与浏览器完全一致）
#   ① nav 接口给两个 key（img_key、sub_key）
#   ② 两者拼接 → 按"重排表"打乱 → 取前 32 位 = mixin_key
#   ③ 参数 + wts(时间戳) → 按参数名排序 → 删掉值里的 !'()* → 拼成 k=v&k=v
#   ④ w_rid = MD5(拼接串 + mixin_key)
import hashlib
import re
import time
from urllib.parse import quote

# WBI 重排表（64 个数字，从混淆 JS 里抄出来的）
MIXIN_KEY_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


def get_mixin_key(img_key, sub_key):
    """两个密钥拼接 → 按重排表打乱 → 取前 32 位（= 混合密钥）"""
    raw = img_key + sub_key
    return "".join(raw[i] for i in MIXIN_KEY_TAB if i < len(raw))[:32]


def sign_params(params, mixin_key, wts=None):
    """给请求参数签名

    params    : 请求参数字典（不含 w_rid / wts）
    mixin_key : 混合密钥
    wts       : 时间戳，不传则用当前时间
    返回      : 带 wts 和 w_rid 的完整参数字典（可直接发给服务器）
    """
    wts = wts or str(int(time.time()))
    merged = {**params, "wts": wts}

    pairs = []
    for k in sorted(merged.keys()):           # ① 参数名按字典序排序
        v = merged[k]
        if isinstance(v, str):
            v = re.sub(r"[!'()*]", "", v)     # ② 值里删掉 !'()*
        if v is not None:
            pairs.append(f"{quote(k, safe='')}={quote(str(v), safe='')}")
    query = "&".join(pairs)                    # ③ 拼成 k=v&k=v

    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()   # ④ MD5
    return {**merged, "w_rid": w_rid}


# ===== 自测：复现抓包时的 w_rid =====
if __name__ == "__main__":
    img_key = "7cd084941338484aae1ad9425b84077c"
    sub_key = "4932caff0ff746eab6f01bf08b70ac45"
    mixin = get_mixin_key(img_key, sub_key)

    # 抓包时那个评论请求的参数（w_rid 除外）
    params = {
        "oid": "117337885774958",
        "type": "1",
        "mode": "3",
        "pagination_str": '{"offset":"CAESEDE4MzM0OTA5NzkwMzczODgiAggB"}',
        "plat": "1",
        "web_location": "1315875",
        "x-bili-locale-json": '{"c_locale":{"language":"zh","script":"Hans"},"always_translate":false}',
    }
    signed = sign_params(params, mixin, wts="1790518604")

    print("mixin_key   :", mixin)
    print("算出的 w_rid:", signed["w_rid"])
    print("抓包的 w_rid:", "1bb727404e1977b41211037ee2fbb6ca")
    print("一致        :", "✅" if signed["w_rid"] == "1bb727404e1977b41211037ee2fbb6ca" else "❌")
