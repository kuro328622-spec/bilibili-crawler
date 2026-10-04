# B站爬虫（WBI 签名逆向 + UP主数据分析）

逆向 B站 的 **WBI 签名机制**写的爬虫。不需要浏览器，Python 自己就能算出签名发请求。
目前能爬指定 UP 主的全部投稿视频和热门评论，数据存 SQLite。

## 功能

- 逆向 WBI 签名（MD5 + 动态密钥 + 重排表），用 Python 复现并与浏览器抓包结果**比对验证**
- 爬取 UP 主**全部投稿视频**（按页码分页）
- 爬取视频的**热门评论**（游标翻页）
- 存 SQLite（`videos` + `comments` 两张表），按主键去重
- 限速 + 退避重试 + 风控识别（412 不重试）
- **凭证不进仓库**（cookie 放本地文件，`.gitignore` 排除）

## 目录结构

```
crypto.py                    WBI 签名（MD5 + 64位重排表）
config.py                    配置：接口地址、限速、爬取目标
config_local.example.py      凭证模板（复制成 config_local.py 填 cookie）
client.py                    请求：限速 + 重试 + 自动签名
parsers.py                   解析：视频列表 / 评论
storage.py                   存储：SQLite（videos + comments）
crawler.py                   爬取入口
```

## 运行

```bash
pip install -r requirements.txt
copy config_local.example.py config_local.py    # 填入自己的 cookie
python crawler.py
```

爬取目标在 `config.py` 里改（`UP_MID` 换成别的 UP 主 mid）。

## WBI 签名算法（逆向笔记）

B站 的 wbi 接口要求请求带 `w_rid`（签名）+ `wts`（时间戳）——实测**不带签名返回 `-403`，带错误签名返回 `HTTP 412` 风控页**。

```
① 请求 /x/web-interface/nav → 拿到 wbi_img.img_url 和 sub_url
② 从 URL 提取文件名（去掉路径和 .png）→ img_key、sub_key
③ 两者拼接，按固定"重排表"（64 个数字）打乱，取前 32 位 → mixin_key
④ 参数 + wts(时间戳) → 按参数名排序 → 删掉值里的 !'()* → 拼成 "k=v&k=v"
⑤ w_rid = MD5(拼接串 + mixin_key)
```

## 踩过的坑

- **密钥藏在图片 URL 的文件名里**（`https://i0.hdslb.com/bfs/wbi/7cd0849....png`），不仔细看根本想不到
- **nav 接口匿名会返回 `code=-101`（未登录），但 `wbi_img` 照样给** → 不能因为 code 非 0 就报错
- **视频列表接口光有签名不够，必须带 cookie**（否则 412 风控）；而**评论接口匿名就能通**
- 混淆代码里**变量名会被改**（社区说的 `img_key` 在代码里其实叫 `o`）→ **搜字符串常量（`wbi_img`、参数名）比搜变量名可靠**
- 评论是**游标翻页**（`cursor.pagination_reply.next_offset`），不是页码翻页

## 说明

仅供学习，不商用。cookie 等凭证通过 `config_local.py` 本地保存，不提交到仓库。
