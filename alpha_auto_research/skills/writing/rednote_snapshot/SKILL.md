---
name: rednote-snapshot
description: Take high-resolution website snapshots in mobile 4:3 format (768x1024 viewport, 3x retina) for Xiaohongshu/RedNote content. Use this skill when the user wants to capture a webpage screenshot for social media, create a mobile-optimized page snapshot, or needs a high-DPI website capture in portrait orientation.
---

# 小红书网页快照技能

将网页截取为高清移动端 4:3 比例图片，适用于小红书等社交平台内容制作。

## 截图规格

| 参数 | 值 |
|------|-----|
| 视口尺寸 | 768 x 1024 (4:3) |
| 设备像素比 | 3x (Retina) |
| 输出分辨率 | 2304 x 3072 |
| 输出格式 | JPEG (quality 95%) |

## 前置要求

- tmux（所有 playwright-cli 命令必须在 tmux 中执行）
- playwright-cli（全局或通过 npx）
- ImageMagick `convert`（用于 PNG → JPEG 转换）

## 操作步骤

### 1. 创建 tmux 会话并打开浏览器

```bash
tmux new-session -d -s pw 2>/dev/null || true
tmux send-keys -t pw "playwright-cli open <URL>" Enter
```

等待 3 秒后检查输出：

```bash
sleep 3 && tmux capture-pane -t pw -p | tail -15
```

### 2. 调整视口为移动端 4:3

```bash
tmux send-keys -t pw "playwright-cli resize 768 1024" Enter
```

### 3. 使用 3x 设备像素比截图

通过 `run-code` 创建新的高 DPI 上下文并截图：

```bash
tmux send-keys -t pw "playwright-cli run-code \"async page => { \
  await page.close(); \
  const context = await page.context().browser().newContext({ \
    viewport: { width: 768, height: 1024 }, \
    deviceScaleFactor: 3 \
  }); \
  const p = await context.newPage(); \
  await p.goto('<URL>'); \
  await p.screenshot({ path: 'snapshot-hires.png', type: 'png' }); \
}\"" Enter
```

### 4. 转换为高质量 JPEG

```bash
convert snapshot-hires.png -quality 95 snapshot.jpg
rm snapshot-hires.png
```

### 5. 关闭浏览器

```bash
tmux send-keys -t pw "playwright-cli close" Enter
```

## 完整单命令参考

```bash
# 一键流程（替换 <URL> 和 <OUTPUT>）
tmux new-session -d -s pw 2>/dev/null || true \
  && tmux send-keys -t pw "playwright-cli open <URL>" Enter \
  && sleep 3 \
  && tmux send-keys -t pw "playwright-cli resize 768 1024" Enter \
  && sleep 2 \
  && tmux send-keys -t pw "playwright-cli run-code \"async page => { \
       await page.close(); \
       const ctx = await page.context().browser().newContext({ \
         viewport:{width:768,height:1024}, deviceScaleFactor:3 \
       }); \
       const p = await ctx.newPage(); \
       await p.goto('<URL>'); \
       await p.screenshot({path:'hires.png',type:'png'}); \
     }\"" Enter \
  && sleep 5 \
  && convert hires.png -quality 95 <OUTPUT>.jpg \
  && rm hires.png \
  && tmux send-keys -t pw "playwright-cli close" Enter
```

## 注意事项

- playwright-cli 的 `screenshot` 命令默认输出 PNG（即使文件名为 .jpg），因此需要用 ImageMagick 转换
- `deviceScaleFactor: 3` 产生 3 倍分辨率，确保在高清屏上清晰显示
- 如需全页截图（含滚动区域），在 screenshot 参数中添加 `fullPage: true`
- 截图前可等待页面加载完成：`await p.waitForLoadState('networkidle')`
