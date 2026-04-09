# Banana Image Generation Skill

## 密钥

从 `research_config.jsonc` 的 `banana_image` 字段读取所有 `${...}` 变量。


---

## 生成图像

### API 概览

- **格式**：OpenAI DALL-E 兼容
- **模型**：Nano-banana-3.1-Flash（Generations，推荐）
- **请求方式**：`POST ${image_gen_url}/v1/images/generations`

### 请求参数

#### Header

| 参数 | 类型 | 必需 | 说明 |
|:-----|:-----|:----:|:-----|
| `Authorization` | string | 否 | 默认值：`Bearer ${image_generation_api_key}` |

#### Body（application/json）

| 参数 | 类型 | 必需 | 说明 |
|:-----|:-----|:----:|:-----|
| `model` | string | **是** | 模型名称，如 `gemini-3.1-flash-image-preview` |
| `prompt` | string | **是** | 图像描述提示词 |
| `aspect_ratio` | enum | 否 | 可选值：`4:3` `3:4` `16:9` `9:16` `2:3` `3:2` `1:1` `4:5` `5:4` `21:9` `1:4` `4:1` `8:1` `1:8` |
| `response_format` | string | 否 | `url` 或 `b64_json` |
| `image` | array[string] | 否 | 参考图数组（url 或 b64_json） |
| `image_size` | enum | 否 | 仅 nano-banana-2 支持，可选值：`512` `1K` `2K` `4K` |

### 请求示例

```python
import http.client
import json

conn = http.client.HTTPSConnection("${image_gen_url}'s host")  # read from research_config.jsonc -> banana_image.image_gen_url
payload = json.dumps({
   "prompt": "cat",  # include image url here if you want to edit one image
   "model": "gemini-3.1-flash-image-preview"
})
headers = {
   'Authorization': 'Bearer ${image_generation_api_key}',  # read from research_config.jsonc -> banana_image.image_generation_api_key
   'Content-Type': 'application/json'
}
conn.request("POST", "/v1/images/generations", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
```

### 返回响应

- **200**：成功，返回 `application/json` 对象


---

## Prompting 指南

Interactive prompt crafting for Nano Banana Pro image generation. This skill guides users through a structured process to create effective prompts by clarifying intent and applying proven techniques.

### Step 1: Gather Reference Materials

Before asking questions, check if the user has provided:

- **Reference images** - Photos to use for character consistency, style, or composition
- **Existing prompts** - Previous attempts to improve upon
- **Visual references** - Screenshots or examples of desired output

If reference materials are available, this affects which techniques apply (e.g., Reference Role Assignment, Character Consistency).

### Step 2: Clarify Intent with Questions

Use the `AskUserQuestion` tool to understand the user's goal. Ask questions in batches of 2-4, focusing on the most important aspects first.

#### Core Questions (always ask)

1. **Output Type** - What kind of image?
   - Photo/realistic
   - Illustration/artistic
   - Infographic/educational
   - Product shot/commercial
   - UI mockup/design

2. **Subject** - Who or what is the main focus?
   - Person (with or without reference)
   - Object/product
   - Scene/environment
   - Concept/abstract

#### Technique-Specific Questions (based on answers)

**If Photo/Realistic:**
- What era or camera style? (modern DSLR, 1990s film, 2000s digital)
- Specific lighting? (golden hour, studio, flash)
- Aspect ratio needed? (16:9, 9:16, 1:1)

**If Reference Images Provided:**
- What role for each image? (pose, style, color palette, background)
- Should character identity be preserved?
- Combine images or use as style reference?

**If Text Needed:**
- What text should appear?
- What font style? (serif, sans-serif, handwritten)
- Where should text be placed?

**If Educational/Infographic:**
- What concept to explain?
- Target audience level?
- Should it include labels, arrows, flow?

### Step 3: Determine Prompt Style

Based on user responses, select the appropriate prompt format:

| User Need | Recommended Technique |
|:----------|:----------------------|
| Simple, quick generation | Technique 1: Narrative Prompt |
| Precise control over details | Technique 2: Structured Prompt |
| Era-specific aesthetic | Techniques 3-4: Vibe Library + Photography Terms |
| Magazine/poster with text | Technique 5: Physical Object Framing |
| Conceptual/interpretive | Technique 6: Perspective Framing |
| Diagram/infographic | Technique 7: Educational Imagery |
| Editing existing image | Technique 8: Image Transformation |
| Multiple views/panels | Technique 9: Multi-Panel Output |
| Multiple reference images | Technique 12: Reference Role Assignment |

### Step 4: Generate the Prompt

Construct the prompt by:

1. **Loading `references/guide.md`** to access technique details
2. **Applying relevant techniques** based on Step 3 selection
3. **Cross-checking** against guide examples for proper formatting
4. **Including negative prompts** if needed (Technique 10)
5. **Specifying aspect ratio/resolution** if required (Technique 11)

#### Prompt Construction Checklist

- [ ] Subject clearly defined
- [ ] Action/pose specified (if applicable)
- [ ] Location/background described
- [ ] Style/aesthetic anchored
- [ ] Technical specs included (aspect ratio, lighting, camera)
- [ ] Text integration specified (if needed)
- [ ] Negative prompts added (if needed)
- [ ] Reference image roles assigned (if using references)


---

## Technique Reference

### Technique 1: Narrative Prompts

Start with a simpler narrative approach if no need to provide detailed specifications.

**Scene Narrative** — Describe a moment or action happening in the scene:

> "A young woman stands almost sideways, slightly bent forward, during the final preparation for the show. Makeup artists apply lipstick to her."

End with a style summary to anchor the aesthetic:

> "Victoria's Secret style: sensuality, luxury, glamour."

Direct attention to specific elements:

> "The main emphasis is on the girl's face and the details of her costume. Emphasize the expressiveness of the gaze."

### Technique 2: Structured Prompts

Use structured formats (YAML/JSON) when you need to provide more detailed specifications.

**Reference Preservation** (when reference image available):

```yaml
face:
  preserve_original: true
  reference_match: true
  description: "The girl's facial features, expression, and identity must remain exactly the same as the reference image."
```

**Multi-Subject Handling** — Define each element as a separate object:

```yaml
subject:
  girl:
    age: "young"
    hair: "long, wavy brown hair"
    expression: "puckering her lips toward the camera"
    clothing: "black hooded sweatshirt"
  puppy:
    type: "small white puppy"
    eyes: "light blue"
    expression: "calm, looking forward"
```

**Example — 2000s Mirror Selfie:**

```yaml
subject:
  description: "A young woman taking a mirror selfie with very long voluminous dark waves and soft wispy bangs"
  age: "young adult"
  expression: "confident and slightly playful"
  hair:
    color: "dark"
    style: "very long, voluminous waves with soft wispy bangs"
  clothing:
    top:
      type: "fitted cropped t-shirt"
      color: "cream white"
      details: "features a large cute anime-style cat face graphic with big blue eyes, whiskers, and a small pink mouth"
  face:
    preserve_original: true
    makeup: "natural glam makeup with soft pink dewy blush and glossy red pouty lips"

accessories:
  earrings:
    type: "gold geometric hoop earrings"
  jewelry:
    waistchain: "silver waistchain"
  device:
    type: "smartphone"
    details: "patterned case"

photography:
  camera_style: "early-2000s digital camera aesthetic"
  lighting: "harsh super-flash with bright blown-out highlights but subject still visible"
  angle: "mirror selfie"
  shot_type: "tight selfie composition"
  texture: "subtle grain, retro highlights, V6 realism, crisp details, soft shadows"

background:
  setting: "nostalgic early-2000s bedroom"
  wall_color: "pastel tones"
  elements:
    - "chunky wooden dresser"
    - "CD player"
    - "posters of 2000s pop icons"
    - "hanging beaded door curtain"
    - "cluttered vanity with lip glosses"
  atmosphere: "authentic 2000s nostalgic vibe"
  lighting: "retro"
```

### Technique 3: Vibe Library

The vibe is determined by **signature details** — specific elements that define an era or style.

| Era/Style | Signature Details |
|:----------|:------------------|
| 2000s bedroom | CD player, beaded curtain, lip glosses, pop icon posters |
| 1990s film photography | direct flash, messy hair, dim lighting, magazine posters |
| Film noir | venetian blind shadows, cigarette smoke, fedora, rain on window |
| Wes Anderson | symmetry, pastels, vintage props, centered framing |
| Blade Runner | neon rain, holographic ads, steam, cramped urban spaces |

**Mood/Atmosphere Words:**

> "dreamy, storytelling vibe", "warm, nostalgic", "cinematic, emotional"

**Candid Actions** — Natural poses add authenticity:

> "The subject is looking slightly away from the camera, holding a coffee cup, with a relaxed, candid expression."

### Technique 4: Photography Terminology

Technical camera/lighting terms add realism and control.

| Category | Example |
|:---------|:--------|
| **Camera/Lens** | "Shot on a Sony A7III with an 85mm f/1.4 lens, creating a flattering portrait compression." |
| **Lighting** | "Classic three-point lighting setup. Soft key light, subtle rim light separating subject from dark background." |
| **Texture** | "Render natural skin texture with visible pores. The fabric should show subtle wool texture." |
| **Time of Day** | "Golden Hour sunset. Warm, nostalgic lighting hitting the side of the face." |
| **Framing** | "Framed from chest up, ample headroom, shot from high angle, looking directly at camera." |
| **Focus** | "Exquisite focus on the eyes." |
| **Color Grading** | "Clean and bright cinematic grading with subtle warmth and balanced tones." |
| **Era Camera** | `camera_style: "early-2000s digital camera aesthetic"` with `lighting: "harsh super-flash"` |

### Technique 5: Physical Object Framing

Generate an image OF a physical object (magazine, poster, photo on desk) rather than just the content itself.

> "A photo of a glossy magazine cover... The magazine is on a white shelf against a wall."

- **Typography**: "The text is in a serif font, black on white, and fills the view."
- **Realistic Details**: "Put the issue number and today's date in the corner along with a barcode and a price."

### Technique 6: Perspective Framing

Ask for an interpretation from a specific viewpoint rather than a literal image.

> "How engineers see the San Francisco Bridge"

Other examples: "How a child sees a hospital", "How a chef sees a kitchen", "How an architect sees a city"

### Technique 7: Educational/Instructional Imagery

Create infographics, diagrams, and educational visuals.

- **Educational Framing**: "Create an educational infographic explaining [Photosynthesis]."
- **Visual Elements**: "Illustrate: The Sun, a green Plant, Water (H2O) entering roots, CO2 entering leaves, O2 being released."
- **Audience**: "Suitable for a high school science textbook."
- **Flow & Labeling**: "Use arrows to show the flow of energy and matter. Label each element clearly."

### Technique 8: Image Transformation

Transform a reference image by specifying operations.

- **Task-Based Verbs**: "Identify the main product... Cleanly extract... Recreate as a premium e-commerce product shot... Place on pure white studio background."
- **Removal**: "Automatically removing any hands holding it or messy background details."

### Technique 9: Multi-Panel/Collage Output

Generate multiple views or panels in a single image.

- **Layout**: "A collage with one large main image at the top, and several smaller images below it."
- **Numbered Panels**: "1. Main: wide-angle living area. 2. Bottom Left: Master Bedroom. 3. Bottom Right: 3D top-down floor plan."
- **Consistent Style**: "Apply Modern Minimalist style with warm oak wood flooring and off-white walls across ALL images."

### Technique 10: Negative Prompts

Tell the model what NOT to include:

> "no date stamp", "no text", "not rustic", "No monkeys"

### Technique 11: Aspect Ratio & Resolution

- **Aspect Ratio**: `9:16` (vertical poster), `21:9` (cinematic wide), `4:5` (Instagram)
- **Resolution**: `1K`, `2K`, `4K`

### Technique 12: Reference Role Assignment

When using multiple reference images, assign specific roles:

> "Use Image A for the character's pose, Image B for the art style, and Image C for the background environment."

Common roles: character/subject, style/aesthetic, color palette, background/environment, branding/logo.

### Technique 13: Character Consistency

Maintain the same character across multiple outputs.

- **Single Reference**: Generate a 360 turnaround view first, then use as reference library.
- **Multiple References** (up to 5): Use diverse angles — close-ups, full body, different clothes/poses/expressions.

### Technique 14: Image Blending

Combine multiple input images into one:

> "Combine these images into one appropriately arranged cinematic image in 16:9 format."

### Technique 15: Upscaling & Restoration

- **Upscaling**: "Upscale to 4K" (works with images as small as 150x150)
- **Restoration**: "Faithfully restore this old photo"

### Technique 16: Translation & Localization

> "Translate all the English text on the cans into Korean, while keeping everything else the same."


---

## 生成图像之后

当你把生成的图像下载到本地后，需要进一步上传到云端图床，方便分享和浏览：

```bash
curl -X POST ${image_bed_upload_url} \
  -H "Authorization: Bearer ${image_bed_api_key}" \
  -F "folder=testfolder" \
  -F "file_name=test_file.log" \
  -F "file=@/path/to/local/image.png" \
  --no-buffer
```

运行完毕后，如果一切无误，服务器会返回云端图像 URL，然后你把 markdown 中的本地图像路径替换为云端 URL 即可。

> 注意：以上所有 `${...}` 变量均从 `research_config.jsonc` 的 `banana_image` 字段读取。
