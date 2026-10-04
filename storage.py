# storage.py —— 存储模块（SQLite：videos 视频表 + comments 评论表）
import os
import sqlite3

import config


class Storage:
    def __init__(self, db_path=config.DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        # 视频表：字段按实际抓包看到的返回结构设计
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                bvid        TEXT PRIMARY KEY,
                aid         INTEGER,
                title       TEXT,
                mid         INTEGER,
                author      TEXT,
                play        INTEGER,
                comment_cnt INTEGER,
                danmaku_cnt INTEGER,
                created     INTEGER,
                length      TEXT,
                typeid      INTEGER,
                description TEXT
            )
        """)
        # 评论表：通过 bvid 关联到视频
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                rpid      INTEGER PRIMARY KEY,
                bvid      TEXT,
                user_mid  INTEGER,
                user_name TEXT,
                content   TEXT,
                like_cnt  INTEGER,
                ctime     INTEGER
            )
        """)
        self.conn.commit()

    def save_videos(self, videos):
        """存视频（按 bvid 去重）"""
        rows = [
            (v.get("bvid"), v.get("aid"), v.get("title"), v.get("mid"), v.get("author"),
             v.get("play"), v.get("comment_cnt"), v.get("danmaku_cnt"),
             v.get("created"), v.get("length"), v.get("typeid"), v.get("description", ""))
            for v in videos
        ]
        self.conn.executemany("""
            INSERT OR IGNORE INTO videos
            (bvid, aid, title, mid, author, play, comment_cnt, danmaku_cnt,
             created, length, typeid, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        self.conn.commit()

    def save_comments(self, comments):
        """存评论（按 rpid 去重）"""
        rows = [
            (c.get("rpid"), c.get("bvid"), c.get("user_mid"), c.get("user_name"),
             c.get("content"), c.get("like_cnt"), c.get("ctime"))
            for c in comments
        ]
        self.conn.executemany("""
            INSERT OR IGNORE INTO comments
            (rpid, bvid, user_mid, user_name, content, like_cnt, ctime)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rows)
        self.conn.commit()

    def count_videos(self):
        return self.conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

    def count_comments(self):
        return self.conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]

    def close(self):
        self.conn.close()
