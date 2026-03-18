# MindWall Extension Icons

This folder holds the Chrome extension icons required by `manifest.json`.

## Required Files

| File | Size | Usage |
|------|------|-------|
| `icon16.png` | 16 × 16 px | Favicon, toolbar icon (small) |
| `icon48.png` | 48 × 48 px | Extensions management page |
| `icon128.png` | 128 × 128 px | Chrome Web Store, install dialog |

All icons must be **PNG** format with transparency support. The manifest references them as:

```json
"icons": {
  "16": "icons/icon16.png",
  "48": "icons/icon48.png",
  "128": "icons/icon128.png"
}
```

## Design Specifications

- **Primary colour:** `#3B82F6` (Tailwind blue-500, matches the dashboard theme)
- **Background:** Transparent
- **Symbol:** Shield with "M" lettermark, consistent with the MindWall brand
- **Format:** PNG-24 with alpha channel
- **Padding:** ~10% inset from edges for visual balance at small sizes

## Generating Placeholder Icons

If you don't have final artwork, generate simple placeholders with **ImageMagick**:

### Linux / macOS

```bash
magick -size 16x16 xc:none -fill '#3b82f6' -draw 'roundrectangle 0,0 15,15 3,3' \
  -fill white -gravity center -pointsize 12 -annotate 0 'M' icon16.png

magick -size 48x48 xc:none -fill '#3b82f6' -draw 'roundrectangle 0,0 47,47 8,8' \
  -fill white -gravity center -pointsize 28 -annotate 0 'M' icon48.png

magick -size 128x128 xc:none -fill '#3b82f6' -draw 'roundrectangle 0,0 127,127 16,16' \
  -fill white -gravity center -pointsize 72 -annotate 0 'M' icon128.png
```

### Windows (PowerShell)

```powershell
magick -size 16x16 xc:none -fill "#3b82f6" -draw "roundrectangle 0,0 15,15 3,3" `
  -fill white -gravity center -pointsize 12 -annotate 0 "M" icon16.png

magick -size 48x48 xc:none -fill "#3b82f6" -draw "roundrectangle 0,0 47,47 8,8" `
  -fill white -gravity center -pointsize 28 -annotate 0 "M" icon48.png

magick -size 128x128 xc:none -fill "#3b82f6" -draw "roundrectangle 0,0 127,127 16,16" `
  -fill white -gravity center -pointsize 72 -annotate 0 "M" icon128.png
```

> **Note:** Use `magick` (ImageMagick 7+). On older versions, replace `magick` with `convert`.

## Alternative: Python (Pillow)

```python
from PIL import Image, ImageDraw, ImageFont

for size in (16, 48, 128):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = max(size // 8, 2)
    draw.rounded_rectangle([0, 0, size-1, size-1], radius=r, fill='#3b82f6')
    font_size = int(size * 0.6)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    draw.text((size/2, size/2), 'M', fill='white', font=font, anchor='mm')
    img.save(f'icon{size}.png')
```

## After Generating

1. Place all three PNG files in this directory (`extension/icons/`)
2. Reload the extension in `chrome://extensions/`
3. Verify icons appear in the toolbar and extensions page
