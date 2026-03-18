# Newsletter Preview Styling

## Overview

The newsletter preview (`/newsletter/issue/<id>/preview`) is styled to match how the newsletter will appear when sent via email. It uses email-safe HTML with inline styles, table-based layouts, and embedded images for reliable display across different email clients.

## Structure

### Email-Safe HTML Layout

The newsletter uses a nested table structure optimized for email clients:

```
Outer Table (background pattern + centering)
  └─ Main Container Table (600px max, white background)
       ├─ Header Row (optional - subject/preheader)
       ├─ Block Panel Rows (off-white panels with rounded corners)
       └─ Footer Row
```

### Key Design Elements

1. **Background Pattern**
   - Repeating tile image on outer container
   - Location: `static/images/newsletter/tile.jpg` (optimized from original)
   - Base64 encoded for embedding: `static/images/newsletter/tile_base64.txt`
   - Fallback: Solid color `#0b1020` (dark blue-black)

2. **Main Container**
   - Max width: 600px (email-safe standard)
   - Background: `transparent` (panels show individually against dark background)
   - Centered with padding

3. **Block Panels**
   - Background: `#fef9e7` (very light cream)
   - Border: `1px solid #e8dcc0` (light brown)
   - Border radius: 8px (rounded corners)
   - Padding: 20px inside, 24px spacing between panels
   - Each block wrapped in its own panel with rounded corners

4. **Typography**
   - Headings: Georgia, 'Times New Roman', serif (heritage feel)
   - Body: Arial, Helvetica, sans-serif (readability)
   - Headings: `#3d2817` (very dark brown), 18-24px
   - Body text: `#3d2817` (very dark brown), 16px, line-height 1.6
   - Secondary text: `#5c3e2a` / `#6b4e3d` (medium brown)

5. **Links**
   - Color: `#6b4e3d` (brown)
   - Underlined for accessibility

## Files

### Main Template
- `templates/newsletter/render.html` - Main email structure with background pattern

### Block Partials (All Updated)
- `templates/newsletter/partials/intro.html` - Intro block panel
- `templates/newsletter/partials/snapshot.html` - Snapshot block panel
- `templates/newsletter/partials/feature.html` - Feature block panel
- `templates/newsletter/partials/new_products.html` - Products block panel
- `templates/newsletter/partials/spotlight.html` - Spotlight block panel
- `templates/newsletter/partials/category.html` - Category block panel
- `templates/newsletter/partials/evergreen.html` - Evergreen block panel
- `templates/newsletter/partials/closing.html` - Closing block panel

### Assets
- `static/images/newsletter/tile.jpg` - Optimized tile image (2.8KB, 99.9% reduction from original)
- `static/images/newsletter/tile_base64.txt` - Base64 encoded tile for embedding

## Implementation Details

### Background Pattern Loading

The preview route (`blueprints/newsletter.py::preview_issue`) loads the base64 tile data:

```python
tile_path = os.path.join(..., 'static', 'images', 'newsletter', 'tile_base64.txt')
with open(tile_path, 'r') as f:
    tile_base64_data = f.read().strip()
```

The template uses it as:
```html
background-image:url('data:image/jpeg;base64,{{ tile_base64_data }}');
```

### Block Panel Structure

Each block follows this pattern:

```html
<tr>
  <td style="padding:0 24px 24px 24px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" 
           style="background-color:#fafaf5; border-radius:8px; border:1px solid #e5e5e0;">
      <tr>
        <td style="padding:20px;">
          <!-- Block content -->
        </td>
      </tr>
    </table>
  </td>
</tr>
```

### Email Client Compatibility

- **Gmail**: Full support for all features
- **Apple Mail**: Full support for all features
- **Outlook.com**: Full support (border-radius works)
- **Outlook Desktop**: May need VML for background images (can add later if needed)
- **Mobile clients**: Responsive with max-width constraints

## Color Palette

- **Outer background**: `#0b1020` (dark blue-black) with repeating tile pattern
- **Main container**: `transparent` (panels show individually)
- **Panel background**: `#fef9e7` (very light cream)
- **Borders**: `#e8dcc0` (light brown)
- **Text (headings)**: `#3d2817` (very dark brown)
- **Text (body)**: `#3d2817` (very dark brown)
- **Text (secondary)**: `#5c3e2a` / `#6b4e3d` (medium brown)
- **Links**: `#6b4e3d` (brown)

## Image Optimization

The tile image was optimized:
- **Original**: `docs/temp/tile.png` (1.9MB, 1024x1536px)
- **Optimized**: `static/images/newsletter/tile.jpg` (2.8KB, ~200px)
- **Reduction**: 99.9% size reduction
- **Format**: JPEG (RGB, quality 85)
- **Base64**: Encoded for embedding in email HTML

## Export Considerations

When exporting the newsletter for sending:
1. All images should be converted to base64 data URIs
2. All CSS must be inline (already done)
3. Generate standalone HTML with no external dependencies
4. Test in multiple email clients before sending

## Future Enhancements

- Add VML support for Outlook desktop background images
- Add media queries for mobile optimization
- Create export function that base64 encodes all images
- Add preview in actual email clients (Litmus/Email on Acid integration)

