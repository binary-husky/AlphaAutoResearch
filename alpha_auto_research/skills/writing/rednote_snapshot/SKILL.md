---
name: rednote-snapshot
description: Take high-resolution website snapshots for Xiaohongshu/RedNote content. Use this skill when the user wants to capture a webpage screenshot for social media.
---

# Mkdocs 转 小红书图片


## 首先后台运行 mkdocs serve

```

root@dsw-386706-7c4c8cfc94-5f6nl:/mnt/data_cpfs/qingxu.fu/rl_auto_research_v2# mkdocs serve

 │  ⚠  Warning from the Material for MkDocs team
 │
 │  MkDocs 2.0, the underlying framework of Material for MkDocs,
 │  will introduce backward-incompatible changes, including:
 │
 │  × All plugins will stop working – the plugin system has been removed
 │  × All theme overrides will break – the theming system has been rewritten
 │  × No migration path exists – existing projects cannot be upgraded
 │  × Closed contribution model – community members can't report bugs
 │  × Currently unlicensed – unsuitable for production use
 │
 │  Our full analysis:
 │
 │  https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/

INFO    -  Building documentation...
INFO    -  Cleaning site directory
Building prefix dict from the default dictionary ...
Loading model from cache /tmp/jieba.cache
Loading model cost 0.626 seconds.
Prefix dict has been built successfully.
INFO    -  Documentation built in 0.97 seconds
INFO    -  [03:16:23] Watching paths for changes: 'docs', 'mkdocs.yml'
INFO    -  [03:16:23] Serving on http://127.0.0.1:8000/mysite/

```



## 然后运行 snapshot_pages.sh

注意，你处在特殊的网络环境中，访问网络必须使用tmux。这个步骤必须在 tmux 中操作

tmux new-session ....
tmux send-keys ....

cd alpha_auto_research/skills/writing/rednote_snapshot
rm -rf mysite-snapshot_pages mysite-snapshot_pages_offset
bash snapshot_pages.sh "http://127.0.0.1:8000/mysite/" mysite-snapshot
