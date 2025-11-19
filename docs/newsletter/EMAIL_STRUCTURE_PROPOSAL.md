# Newsletter Email HTML Structure Proposal

## Overview
This document outlines the optimal structure for newsletter email HTML that will work reliably across different email clients and can be exported as a complete HTML block with embedded images.

## Email HTML Best Practices

### 1. Table-Based Layout
- **Use tables, not divs** - Email clients have poor support for modern CSS layouts
- Nested tables for complex layouts
- `role="presentation"` on layout tables
- `width` attributes on tables (not just CSS)

### 2. Inline Styles Only
- All styles must be inline (no `<style>` blocks except for media queries)
- Avoid CSS properties that email clients don't support:
  - ❌ Flexbox, Grid
  - ❌ Position: absolute/fixed
  - ❌ Transform, animations
  - ✅ Margin, padding, border, background-color
  - ✅ Font properties
  - ✅ Width, height (with fallbacks)

### 3. Background Images
- **Repeating tile background**: Use `background-image` with `background-repeat: repeat`
- **Fallback**: Always provide `background-color` as fallback
- **Outlook compatibility**: May need VML for Outlook (can add later if needed)
- **Embedded images**: Use base64 encoding or absolute URLs (for export, base64 is better)

### 4. Rounded Corners
- `border-radius` works in most modern clients (Gmail, Apple Mail, Outlook.com)
- **Fallback**: Provide square corners as default, rounded as enhancement
- Use `border-radius` inline style

### 5. Color Scheme
- **Background**: Dark (#0b1020 or similar) for outer container
- **Content panels**: Off-white (#f5f5f0, #fafaf5, or #fefefe) for readability
- **Text**: Dark text (#1a1a1a, #2d2d2d) on light backgrounds
- **Accents**: Use brand colors for links and highlights

## Proposed Structure

```
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Newsletter</title>
  <!-- Outlook-specific conditional comments can go here if needed -->
</head>
<body>
  <!-- Outer wrapper table for background pattern -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #0b1020; background-image: url('data:image/png;base64,...'); background-repeat: repeat; padding: 20px 0;">
    <tr>
      <td align="center">
        <!-- Main content container -->
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 8px; overflow: hidden;">
          <!-- Header (optional) -->
          <tr>
            <td style="padding: 24px; background-color: #f5f5f0; border-bottom: 1px solid #e5e5e0;">
              <!-- Header content -->
            </td>
          </tr>
          
          <!-- Intro Block Panel -->
          <tr>
            <td style="padding: 24px; background-color: #fafaf5; border-radius: 8px; margin: 16px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding: 20px; background-color: #fefefe; border-radius: 6px; border: 1px solid #e5e5e0;">
                    <!-- Intro content -->
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Feature Block Panel -->
          <tr>
            <td style="padding: 0 24px 24px 24px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fafaf5; border-radius: 8px; border: 1px solid #e5e5e0;">
                <tr>
                  <td style="padding: 20px;">
                    <!-- Feature content -->
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Additional blocks follow same pattern -->
          
          <!-- Footer -->
          <tr>
            <td style="padding: 24px; background-color: #f5f5f0; border-top: 1px solid #e5e5e0; text-align: center; font-size: 12px; color: #666;">
              <!-- Footer content -->
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

## Key Design Decisions

### 1. Nested Table Structure
- **Outer table**: Handles background pattern and centering
- **Main container table**: 600px max width, white/off-white background
- **Block panels**: Each block in its own table row with off-white background panel
- **Inner content tables**: For complex block layouts

### 2. Panel Styling
- **Background**: `#fafaf5` or `#fefefe` (off-white)
- **Border**: `1px solid #e5e5e0` (subtle border)
- **Border-radius**: `8px` (rounded corners)
- **Padding**: `20px` or `24px` for spacing
- **Margin**: Use padding on parent `<td>` to create spacing between panels

### 3. Background Pattern
- Use a subtle repeating pattern (tartan, plaid, or simple geometric)
- Base64 encode the image for embedding
- Provide solid color fallback
- Pattern should be subtle enough not to interfere with readability

### 4. Typography
- **Font stack**: `font-family: Georgia, 'Times New Roman', serif;` (for heritage feel) or `Arial, Helvetica, sans-serif;` (for modern feel)
- **Headings**: `font-size: 24px; font-weight: 700; color: #1a1a1a;`
- **Body text**: `font-size: 16px; line-height: 1.6; color: #2d2d2d;`
- **Links**: `color: #4e6bff; text-decoration: underline;`

### 5. Images
- **Embedded images**: Use base64 encoding for export
- **Alt text**: Always provide descriptive alt text
- **Width**: Set explicit width (e.g., `width="600"` attribute + `style="width: 100%; max-width: 600px;"`)
- **Responsive**: Use `max-width: 100%` and `height: auto`

## Implementation Steps

1. **Create base template** with table structure
2. **Add background pattern** (create/select tile image, base64 encode)
3. **Update block partials** to use panel structure
4. **Test in email clients** (Gmail, Outlook, Apple Mail)
5. **Add image embedding** functionality for export
6. **Create export function** that base64 encodes images and generates standalone HTML

## Block Panel Structure

Each block should follow this pattern:

```html
<tr>
  <td style="padding: 0 24px 24px 24px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fafaf5; border-radius: 8px; border: 1px solid #e5e5e0;">
      <tr>
        <td style="padding: 20px;">
          <!-- Block content here -->
          <h2 style="margin: 0 0 12px 0; font-size: 20px; font-weight: 700; color: #1a1a1a;">Block Title</h2>
          <p style="margin: 0; font-size: 16px; line-height: 1.6; color: #2d2d2d;">Block content...</p>
        </td>
      </tr>
    </table>
  </td>
</tr>
```

## Color Palette

- **Background (outer)**: `#0b1020` (dark blue-black)
- **Background (main container)**: `#ffffff` (white)
- **Panel background**: `#fafaf5` or `#fefefe` (off-white)
- **Text (headings)**: `#1a1a1a` (near black)
- **Text (body)**: `#2d2d2d` (dark gray)
- **Borders**: `#e5e5e0` (light gray)
- **Links**: `#4e6bff` (blue)
- **Accents**: Brand colors as needed

## Responsive Considerations

- **Max width**: 600px for main container
- **Mobile**: Use `width="100%"` with `max-width: 600px` for responsive behavior
- **Padding**: Adjust padding on mobile (can use media queries in `<style>` block)
- **Font sizes**: May need to adjust for mobile readability

## Export Requirements

When exporting:
1. Convert all image URLs to base64 data URIs
2. Include all CSS inline (already done)
3. Generate standalone HTML file
4. Ensure all assets are embedded (no external dependencies)
5. Test exported HTML in email clients

