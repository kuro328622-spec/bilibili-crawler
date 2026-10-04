# parsers.py —— 解析模块：把接口返回的 JSON 变成干净记录


def parse_videos(video_list):
    """解析投稿列表（data.list.vlist）→ 视频记录列表

    字段名来自实际抓包观察到的返回结构，不是猜的。
    """
    result = []
    for v in video_list:
        result.append({
            "bvid": v["bvid"],                    # 视频 BV 号（唯一标识）
            "aid": v["aid"],                      # 数字 ID
            "title": v["title"],                  # 标题
            "mid": v["mid"],                      # UP主 ID
            "author": v["author"],                # UP主名
            "play": v["play"],                    # 播放量
            "comment_cnt": v["comment"],          # 评论数
            "danmaku_cnt": v["video_review"],     # 弹幕数（B站字段名叫 review）
            "created": v["created"],              # 发布时间（Unix 时间戳）
            "length": v["length"],                # 时长字符串 "09:43"
            "typeid": v["typeid"],                # 分区 ID
            "description": v.get("description", ""),
        })
    return result


def parse_replies(replies, bvid):
    """解析评论（data.replies）→ 评论记录列表

    只取顶层评论；楼中楼（每条评论里的 replies）暂不处理。
    """
    result = []
    for r in replies or []:
        result.append({
            "rpid": r["rpid"],                          # 评论 ID
            "bvid": bvid,                               # 关联到哪个视频
            "user_mid": r["member"]["mid"],             # 用户 ID
            "user_name": r["member"]["uname"],          # 用户名
            "content": r["content"]["message"],         # 评论内容
            "like_cnt": r["like"],                      # 点赞数
            "ctime": r["ctime"],                        # 评论时间戳
        })
    return result
