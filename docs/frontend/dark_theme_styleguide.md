# Dark Theme UI Styleguide

## Overview
This styleguide defines the visual and UX standards for the CLAN.com Blog CMS dark theme. All new and existing UI components must adhere to these guidelines to ensure a cohesive, premium, and accessible user experience.

---

## 1. Color Palette
- **Background:** `#181c2a` (main), `#23273a` (surface, header, cards)
- **Accent:** `#6366f1` (Tailwind indigo-500), `#a5b4fc` (Tailwind indigo-300)
- **Text:** `#e0e0e0` (primary), `#a5b4fc` (accent), `#fff` (on accent)
- **Borders:** `#31364a` (card, dropdown, header)
- **Card Hover:** `#23273a` with accent border
- **Icon Colors:** Use accent colors for icons (e.g., indigo, yellow, green, blue, purple, pink)

## 2. Layout & Structure
- **Header:**
  - Use a dark horizontal gradient (`linear-gradient(90deg, #181c2a 0%, #23273a 100%)`)
  - Unified with navigation, logo, and dropdowns
  - Soft shadow and subtle border
  - Navigation dropdowns use dark backgrounds and accent borders
- **Main Content:**
  - Use `bg-dark-bg` and `text-dark-text` for the main area
  - All cards and sections use `.card-dark` (see below)
- **Footer:**
  - Matches header in color and border

## 3. Cards & Sections
- **Card Base:**
  - Background: `#181c2a`
  - Border: `1px solid #31364a`
  - Text: `#e0e0e0`
  - Border-radius: `.75rem` (rounded-xl)
  - Box-shadow: `0 2px 8px 0 rgba(0,0,0,0.25)`
- **Card Hover:**
  - Background: `#23273a`
  - Border-color: accent (`#6366f1`)
- **Section Titles:**
  - Color: accent (`#a5b4fc`)
  - Font-weight: bold

## 4. Typography
- **Font:** Use system sans-serif (default Tailwind stack)
- **Text Color:**
  - Primary: `#e0e0e0`
  - Accent: `#a5b4fc` for highlights and section titles
- **Headings:**
  - Large, bold, and white in headers
  - Use accent color for section titles

## 5. Buttons & Inputs
- **Primary Button:**
  - Background: accent (`#6366f1`)
  - Text: white
  - Border-radius: `.5rem` (rounded-lg)
  - Hover: dark background, accent border
- **Secondary Button:**
  - Background: transparent or dark surface
  - Border: accent or dark
  - Text: accent or white
- **Input Fields:**
  - Background: `#23273a`
  - Text: `#e0e0e0`
  - Border: `#31364a`
  - Focus: accent border

## 6. Icons
- Use FontAwesome 6 solid icons
- Place icons in `.icon-circle` with dark background and subtle shadow
- Use accent colors for icon foregrounds

## 7. Navigation & Dropdowns
- **Dropdowns:**
  - Background: `#23273a`
  - Border: `#31364a`
  - Text: `#e0e0e0`
  - Hover: accent text, no background change
- **Active/Selected:**
  - Use accent color for text or border

## 8. Accessibility
- Ensure sufficient contrast for all text and interactive elements
- Use large clickable areas for buttons and nav links
- All icons must have accessible labels or be decorative

## 9. Responsive Design
- All layouts must be fully responsive
- Use Tailwind's grid and flex utilities for adaptive layouts
- Navigation collapses gracefully on mobile

## 10. Example Classes
```html
<!-- Card Example -->
<div class="card-dark rounded-xl p-6 transition flex flex-col items-center gap-2 group-hover:border-dark-accent">
  <span class="icon-circle"><i class="fa-solid fa-lightbulb text-yellow-400 text-xl"></i></span>
  <span class="text-lg font-semibold text-white">Planning</span>
  <p class="text-dark-accent text-sm text-center">Outline your post structure and key points</p>
</div>

<!-- Input Example -->
<input class="input-dark rounded-lg px-4 py-2 shadow" placeholder="Search..." />

<!-- Button Example -->
<button class="bg-dark-accent hover:bg-dark-bg text-white font-semibold px-6 py-2 rounded-lg shadow border border-dark-accent transition">
  <i class="fa-solid fa-plus"></i> New Post
</button>
```

---

## 11. Implementation Notes
- Always use the `.dark` class on the `<html>` root for dark mode
- Use Tailwind utility classes for spacing, layout, and responsiveness
- Custom classes (`.card-dark`, `.icon-circle`, `.input-dark`, etc.) should be defined in a global stylesheet or in the template's `<style>` block
- Avoid any light backgrounds or text colors in dark mode

---

## 12. References
- [Tailwind CSS Dark Mode](https://tailwindcss.com/docs/dark-mode)
- [Accessible Color Palette](https://www.smashingmagazine.com/2020/04/accessible-color-systems/)
- [FontAwesome Icons](https://fontawesome.com/icons)

---

## 13. Workflow Process Indicator
- **Structure:** 9 substages grouped into 3 conceptual stages, each with a subtly different dark background.
- **Appearance:** Shallow, horizontally oriented, touchscreen-friendly, and visually cohesive with the dark theme.
- **Stage Grouping:** Each stage is visually grouped with a unique but subtle background shade, separated by soft accent gradients.
- **Substages:** Each substage is a clickable step, with the current one highlighted using accent color and shadow.
- **Progress:** Subtle progress bars/arrows between substages and stages suggest direction and flow.
- **Accessibility:** Large touch targets, clear focus/active states, and high contrast.
- **Responsiveness:** Fully responsive, adapts to mobile and desktop layouts.
- **Implementation:** See `workflow_indicator.html` macro and usage in workflow templates.

---

> **All new features and UI changes must be reviewed for compliance with this styleguide.** 