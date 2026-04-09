---
name: rednote-convert
description: Convert markdown articles to Xiaohongshu (RedNote) format, including title, cover image, long-form image slides, and short-form post text with hashtags. Use this skill whenever the user wants to publish content to Xiaohongshu, convert an article for RedNote, create Xiaohongshu posts from existing markdown, or generate RedNote content (covers, slides, captions). This skill orchestrates the full pipeline from markdown to ready-to-post RedNote content.
---

# Markdown文章转小红书

# 概述

中间和结果文件都放置在 `${rednote_root} = ${源Markdown文件所在路径}/rednote` 下

小红书生成分为 4 步

1. 生成标题
    - 一般沿用Markdown文章的标题即可

2. 生成封面
    - 见 alpha_auto_research/skills/writing/cover/SKILL.md
    - 见 alpha_auto_research/skills/banana_image/SKILL.md

3. 生成长文（这个过程比较复杂，请按照以下步骤执行）
    3-1. 对文章的分区，然后对每个分区进行摘要，注意摘要还要包含对分区中所包含的图片的描述。生成 `${rednote_root}/partitions.md`
    3-2. 每个分区都转化为 4:3 的竖屏图片

4. 生成正文短文 （带关键词hashtag）



## 写作约束（严格执行）

**禁止**：
1. 绝对不使用任何形式的项目符号或编号列表（不用 *、-、1.2.3. 等列表形式）
2. 不使用破折号（——）
3. 禁用"A而且B"的对仗结构
4. 尽量避免使用冒号（：），用句号代替
5. 开头不用设问句
6. 一句话只表达一个完整意思
7. 每段不超过3句话
8. 避免嵌套从句和复合句
9. 所有内容都用自然段落呈现，用"第一"、"第二"、"第三"等词语自然串联

**改写策略**：
1. **长句拆短**：把复合句拆成多个简单句
2. **术语翻译**：把专业词汇翻译成大白话
3. **增加温度**：适当加入个人感受和真实体验
4. **逻辑清晰**：用"第一、第二、第三"标注顺序
