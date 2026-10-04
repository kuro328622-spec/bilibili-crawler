# crawler.py —— 爬取流程：UP主全部视频 + 部分视频的评论
import json

import config
from client import BiliClient
from parsers import parse_replies, parse_videos
from storage import Storage


def crawl_videos(client, storage):
    """爬取 UP主 的全部投稿视频（按页码分页）"""
    pn = 1
    total = None
    while True:
        data = client.get(config.SPACE_ARC_URL, {
            "mid": config.UP_MID,
            "pn": pn,
            "ps": config.PAGE_SIZE,
            "order": "pubdate",
            "platform": "web",
            "web_location": "333.1387",
        })
        page = data["data"]["page"]
        vlist = data["data"]["list"]["vlist"]

        if total is None:
            total = page["count"]
            print(f"共 {total} 个视频，预计 {(total + config.PAGE_SIZE - 1) // config.PAGE_SIZE} 页")

        if not vlist:
            break
        storage.save_videos(parse_videos(vlist))
        print(f"  第 {pn} 页：+{len(vlist)} 条（库中 {storage.count_videos()}）")

        if pn * config.PAGE_SIZE >= total:
            break
        pn += 1
    return storage.count_videos()


def crawl_comments(client, storage, limit_videos, max_pages):
    """对最近 N 个视频爬评论（用 cursor.pagination_reply.next_offset 翻页）"""
    rows = storage.conn.execute(
        "SELECT bvid, aid FROM videos ORDER BY created DESC LIMIT ?", (limit_videos,)
    ).fetchall()

    for i, (bvid, aid) in enumerate(rows, 1):
        offset = ""
        for _ in range(max_pages):
            data = client.get(config.REPLY_URL, {
                "oid": str(aid),
                "type": "1",
                "mode": "3",                                   # 3 = 热门评论
                "pagination_str": json.dumps({"offset": offset}),
                "plat": "1",
                "web_location": "1315875",
            })
            d = data["data"]
            storage.save_comments(parse_replies(d.get("replies"), bvid))

            cursor = d.get("cursor") or {}
            if cursor.get("is_end"):
                break
            offset = (cursor.get("pagination_reply") or {}).get("next_offset", "")
            if not offset:
                break

        print(f"  [{i}/{len(rows)}] {bvid} 完成（评论累计 {storage.count_comments()}）")
    return storage.count_comments()


if __name__ == "__main__":
    client = BiliClient()
    storage = Storage()

    print("=== ① 爬取投稿视频列表 ===")
    crawl_videos(client, storage)

    if config.COMMENT_PAGES > 0:
        print(f"\n=== ② 爬取最近 {config.COMMENT_LIMIT_VIDEOS} 个视频的评论"
              f"（每个最多 {config.COMMENT_PAGES} 页）===")
        crawl_comments(client, storage, config.COMMENT_LIMIT_VIDEOS, config.COMMENT_PAGES)

    print(f"\n完成：视频 {storage.count_videos()} 个，评论 {storage.count_comments()} 条")
    storage.close()
    client.close()
