#!/bin/bash
# Scroll through a webpage and take page-by-page snapshots (mobile 4:3, 3x retina)
# Usage: bash snapshot_pages.sh <URL> [output_prefix]
#
# Requires: tmux, playwright-cli, ImageMagick (convert)
# All playwright-cli commands run inside a tmux session named "pw".

# rm -rf mysite-snapshot_pages; bash snapshot_pages.sh "http://127.0.0.1:8000/mysite/" mysite-snapshot

set -e

URL="${1:?Usage: bash snapshot_pages.sh <URL> [output_prefix]}"
PREFIX="${2:-snapshot}"
VIEWPORT_W=768
VIEWPORT_H=1280
SCALE=3
QUALITY=95
SESSION="pw"

# Create output directory
OUTDIR="${PREFIX}_pages"
mkdir -p "$OUTDIR"

SCRIPTDIR="$(cd "$(dirname "$0")" && pwd)"
JS_FILE="$SCRIPTDIR/.snapshot_scroll.js"

# Ensure tmux session exists
tmux new-session -d -s "$SESSION" 2>/dev/null || true

# Helper: send command to tmux and wait for prompt
pw_run() {
    local cmd="$1"
    local wait="${2:-5}"
    tmux send-keys -t "$SESSION" "$cmd" Enter
    sleep "$wait"
}

# Helper: capture tmux output
pw_output() {
    tmux capture-pane -t "$SESSION" -p
}

# Helper: wait for shell prompt (command finished)
pw_wait() {
    local max="${1:-60}"
    for i in $(seq 1 "$max"); do
        last_line=$(pw_output | grep -v '^$' | tail -1)
        if echo "$last_line" | grep -qE '(^root@|\$\s*$|#\s*$)'; then
            if [ "$i" -gt 1 ]; then
                return 0
            fi
        fi
        sleep 2
    done
}

echo "=== Opening browser ==="
pw_run "playwright-cli open '$URL'" 3
pw_wait 15

echo "=== Setting up high-DPI context and scrolling ==="
# Write a JS file with values inlined (playwright run-code has no access to process.env)
cat > "$JS_FILE" << JSEOF
async (page) => {
    const url = '${URL}';
    const outdir = '${OUTDIR}';
    const scale = ${SCALE};
    const vw = ${VIEWPORT_W};
    const vh = ${VIEWPORT_H};

    const ctx = await page.context().browser().newContext({
        viewport: { width: vw, height: vh },
        deviceScaleFactor: scale,
    });
    const p = await ctx.newPage();
    await p.goto(url, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(2000);

    // Apply 150% zoom, hide sticky header, style titles and content background
    await p.evaluate(() => {
        document.body.style.zoom = '1.5';
        const header = document.querySelector('header.md-header');
        if (header) header.style.display = 'none';

        const style = document.createElement('style');
        style.textContent = \`
            /* Light background for main content area */
            .md-content {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 16px 20px;
            }

            /* H1: bold accent bar */
            article h1 {
                background: linear-gradient(135deg, #1a237e, #283593);
                color: #fff !important;
                padding: 14px 20px;
                border-radius: 6px;
                margin: 12px -20px 16px -20px;
            }

            /* H2: left accent border + subtle background */
            article h2 {
                background: #e8eaf6;
                border-left: 5px solid #3949ab;
                padding: 10px 16px;
                border-radius: 0 6px 6px 0;
                margin: 20px -20px 12px -20px;
            }

            /* H3: lighter accent */
            article h3 {
                background: #f0f1fa;
                border-left: 4px solid #7986cb;
                padding: 8px 14px;
                border-radius: 0 4px 4px 0;
                margin: 16px -20px 10px -20px;
            }

            /* H4+: minimal underline */
            article h4, article h5, article h6 {
                border-bottom: 2px solid #c5cae9;
                padding-bottom: 4px;
            }
        \`;
        document.head.appendChild(style);
    });
    await p.waitForTimeout(500);

    const totalHeight = await p.evaluate(() => document.documentElement.scrollHeight);
    const viewportHeight = await p.evaluate(() => window.innerHeight);

    // Find clean break points by snapping to block element boundaries.
    // For each candidate scroll position, find the nearest block element top
    // that is just above the bottom edge, and use that as the cut point.
    const breakPoints = await p.evaluate((vh) => {
        // Collect top positions of all visible block-level elements
        const selectors = 'p, h1, h2, h3, h4, h5, h6, li, tr, pre, blockquote, div.highlight, figure, img, table, hr, details, .admonition';
        const elements = document.querySelectorAll(selectors);
        const tops = new Set();
        tops.add(0);
        for (const el of elements) {
            const rect = el.getBoundingClientRect();
            const absTop = rect.top + window.scrollY;
            tops.add(Math.round(absTop));
        }
        const totalH = document.documentElement.scrollHeight;
        tops.add(totalH);
        const sorted = [...tops].sort((a, b) => a - b);

        // Walk through and pick break points ~1 viewport apart
        const breaks = [0];
        let cursor = 0;
        while (cursor + vh < totalH) {
            const target = cursor + vh;
            // Find the largest element top that is <= target (snap back)
            let best = cursor + vh;
            for (let j = 0; j < sorted.length; j++) {
                if (sorted[j] > target) {
                    // Use the previous element top, but ensure we make progress
                    best = (j > 0 && sorted[j - 1] > cursor + vh * 0.5)
                        ? sorted[j - 1]
                        : sorted[j];
                    break;
                }
            }
            if (best <= cursor) best = cursor + vh; // safety: always advance
            breaks.push(best);
            cursor = best;
        }
        if (breaks[breaks.length - 1] < totalH) breaks.push(totalH);
        return breaks;
    }, viewportHeight);

    // Take screenshots: scroll to each break, capture viewport, record crop height
    // For the last page, we need special handling: the browser won't scroll past
    // (totalHeight - viewportHeight), so we scroll to the max and crop from the top
    // to capture only the non-overlapping portion.
    const results = [];
    const cropHeights = [];
    const maxScroll = totalHeight - viewportHeight;

    for (let i = 0; i < breakPoints.length - 1; i++) {
        const clipTop = breakPoints[i];
        const clipBottom = breakPoints[i + 1];
        const clipHeight = clipBottom - clipTop;
        const isLast = (i === breakPoints.length - 2);

        if (!isLast || clipTop <= maxScroll) {
            // Normal page: scroll to clipTop, crop from top of viewport
            await p.evaluate((y) => window.scrollTo(0, y), clipTop);
            await p.waitForTimeout(500);

            const cropH = Math.round(clipHeight * scale);
            const filename = outdir + '/page_' + String(i + 1).padStart(2, '0') + '_h' + cropH + '.png';
            await p.screenshot({ path: filename, type: 'png' });
            results.push(filename);
            cropHeights.push(cropH);
        } else {
            // Last page: clipTop > maxScroll, browser can't scroll that far.
            // Scroll to maxScroll, then crop from the offset within the viewport.
            await p.evaluate((y) => window.scrollTo(0, y), maxScroll);
            await p.waitForTimeout(500);

            // The visible region starts at maxScroll, but we want clipTop..clipBottom
            // Offset from top of viewport = clipTop - maxScroll (in CSS px)
            const offsetY = Math.round((clipTop - maxScroll) * scale);
            const cropH = Math.round(clipHeight * scale);
            // Encode both offset and height: _o{offset}_h{height}
            const filename = outdir + '/page_' + String(i + 1).padStart(2, '0') + '_o' + offsetY + '_h' + cropH + '.png';
            await p.screenshot({ path: filename, type: 'png' });
            results.push(filename);
            cropHeights.push(cropH);
        }
    }

    await ctx.close();
    return JSON.stringify({ pageCount: results.length, totalHeight, viewportHeight, breakPoints, cropHeights, files: results });
}
JSEOF

pw_run "playwright-cli run-code --filename=$JS_FILE" 3

echo "=== Waiting for screenshots to complete ==="
pw_wait 60

# Check for errors
if pw_output | tail -20 | grep -q "### Error"; then
    echo "=== Error detected ==="
    pw_output | tail -20
    rm -f "$JS_FILE"
    exit 1
fi

rm -f "$JS_FILE"

echo "=== Converting PNGs to high-quality JPEGs (with smart crop) ==="
count=0
for png in "$OUTDIR"/page_*.png; do
    [ -f "$png" ] || continue
    basename_noext=$(basename "$png" .png)
    page_num=$(echo "$basename_noext" | grep -oP 'page_\K\d+')
    # Extract optional offset (_o1234) and height (_h5678)
    offset_y=$(echo "$basename_noext" | grep -oP '_o\K\d+' || echo "0")
    crop_h=$(echo "$basename_noext" | grep -oP '_h\K\d+')
    jpg="$OUTDIR/page_${page_num}.jpg"

    img_w=$(identify -format "%w" "$png")
    img_h=$(identify -format "%h" "$png")

    # Padding in device pixels: left/right 10*scale, top/bottom 20*scale
    PAD_X=$((10 * SCALE))
    PAD_Y=$((20 * SCALE))

    if [ -n "$crop_h" ] && [ "$crop_h" -gt 0 ] 2>/dev/null; then
        convert "$png" -crop "${img_w}x${crop_h}+0+${offset_y}" +repage \
            -bordercolor white -border "${PAD_X}x${PAD_Y}" \
            -quality "$QUALITY" "$jpg"
    else
        convert "$png" \
            -bordercolor white -border "${PAD_X}x${PAD_Y}" \
            -quality "$QUALITY" "$jpg"
    fi
    rm "$png"
    count=$((count + 1))
    echo "  Converted: $jpg (offset: ${offset_y}, crop: ${crop_h}/${img_h}px)"
done

echo "=== Closing browser ==="
pw_run "playwright-cli close" 2

echo "=== Done: $count pages saved to $OUTDIR/ ==="
ls -lh "$OUTDIR"/*.jpg 2>/dev/null
