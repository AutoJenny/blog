# Blog Styling Guide

## CSS Structure
The blog's styling is organized in `app/static/css/blog.css` with the following key sections:

### Base Styles
```css
:root {
    --primary-color: #1a365d;
    --secondary-color: #2b4c7e;
    --accent-color: #3182ce;
    --background-color: #f7fafc;
    --text-color: #2d3748;
    --border-color: #e2e8f0;
    --success-color: #48bb78;
    --warning-color: #ecc94b;
    --placeholder-color: #e2e8f0;
}
```

## Image Styling

### Header Images
```css
.blog-post__image {
    margin: 2rem 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.blog-post__image img {
    width: 100%;
    height: auto;
    display: block;
}

.blog-post__image figcaption {
    padding: 1rem;
    background: rgba(0, 0, 0, 0.05);
    font-size: 0.9rem;
    color: #666;
    text-align: center;
}
```

### Section Images
```css
.blog-section__image {
    margin: 2rem 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.blog-section__image img {
    width: 100%;
    height: auto;
    display: block;
    object-fit: cover;
}

.blog-section__image figcaption {
    padding: 1rem;
    background-color: #f8f9fa;
    color: #666;
    font-size: 0.9rem;
    text-align: center;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
}
```

## Layout Components

### Blog Post Structure
- `.blog-post`: Main container for blog posts
- `.blog-post__header`: Post header with title and meta
- `.blog-post__content`: Main content area
- `.blog-post__footer`: Tags and actions
- `.blog-section`: Individual post sections

### Navigation
- `.blog-nav`: Main navigation
- `.post-tabs`: Post view tabs (Preview/Edit/Code)
- `.blog-post__toc`: Table of contents

### Cards and Grids
- `.blog-grid`: Grid layout for post listings
- `.blog-card`: Individual post preview cards
- `.posts-grid`: Alternative grid layout

## Responsive Design
The blog uses responsive breakpoints:

```css
@media (max-width: 768px) {
    .blog-container {
        padding: 1rem;
    }
    .blog-grid {
        grid-template-columns: 1fr;
    }
    .blog-post__title {
        font-size: 2rem;
    }
}
```

## Customization
To customize the blog's appearance:

1. Modify CSS variables in `:root`
2. Override specific component styles
3. Add new styles at the end of `blog.css`
4. Use responsive breakpoints as needed

## Best Practices
1. Use semantic class names
2. Follow BEM naming convention
3. Keep responsive design in mind
4. Test across different devices
5. Maintain consistent spacing 