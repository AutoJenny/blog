# CLAN Blog Local Preview Implementation Plan

This plan outlines the steps to faithfully replicate the CLAN blog's front-end (listing and post detail) for local, private preview only. All preview functionality is under the `/preview/` blueprint. This is not public-facing; the public blog is on CLAN.com.

---

## 1. Preview Front-End: Faithful Blog Display & Listing (Local Only)

- [x] **Replicate Preview Listing Page**
    - [x] Route: `/preview/` (local preview only)
    - [x] Match layout: header image, blog title, post list, meta (date, author), summary, and links (all within /preview/).
    - [x] Style to match `/css/blog.css` (fonts, colors, spacing, etc.).
    - [x] Show only posts with status: published or in process.
    - [x] Add summary and meta for each post.
    - [x] Add navigation to individual post previews at `/preview/<int:post_id>/`.

- [x] **Replicate Preview Individual Blog Post Page**
    - [x] Route: `/preview/<int:post_id>/` (local preview only)
    - [x] Match layout: header, subtitle, meta, summary, header image, sections, images, captions, tags, and footer.
    - [x] Render all content sections with headings, text, and images (with captions).
    - [x] Add navigation back to `/preview/`.
    - [x] Style to match `/css/blog.css`.
    - [x] Add tags and conclusion section.
    - [x] Ensure responsive/mobile-friendly design.

- [x] **Static Assets**
    - [x] Copy or link header/footer images and post images for preview.
    - [x] Ensure all images use correct URLs (local or static CDN as appropriate).
    - [Note] All image URLs in the preview mock data have been checked and corrected to match local static files as of 2024-05-17.

---

## 2. Back-End: Data & API Integration

- [ ] **Post Data Model**
    - [ ] Design SQLAlchemy models (or adapt existing) to store post metadata, sections, images, tags, status, etc.
    - [ ] Support Markdown/HTML content and frontmatter fields.
    - [ ] Add status fields (published, in process, etc.).

- [ ] **Image Data Model**
    - [ ] Store image metadata, status, captions, and URLs (as in `image_library.json`).
    - [ ] Link images to posts/sections.

- [ ] **Workflow Status Tracking**
    - [ ] Implement workflow status tracking (as in `workflow_status.json`).
    - [ ] Track stages: conceptualisation, authoring, metadata, images, validation, publishing, syndication.
    - [ ] Expose status in the preview UI (listing, post detail, etc.).

- [ ] **Import/Sync Scripts**
    - [ ] Write scripts to import old Markdown posts, images, and status data into the new database.
    - [ ] Parse frontmatter and section structure.
    - [ ] Map image IDs and URLs.

- [ ] **API Endpoints**
    - [ ] Create REST API endpoints for posts, images, and workflow status (for future automation or admin tools).
    - [ ] Ensure endpoints can be used for preview, validation, and publishing workflows.

---

## 3. Preview & Publishing Workflow (Local Only)

- [ ] **Preview Functionality**
    - [ ] Add preview routes/pages under `/preview/` for unpublished/in-process posts in the CLAN style.
    - [ ] Allow preview of individual posts and the full blog listing.
    - [ ] Show workflow status and validation info.

- [ ] **Publishing Integration**
    - [ ] Adapt or reimplement the `post_to_clan.py` logic for publishing to CLAN.com (API calls, image upload, etc.).
    - [ ] Support manual and automated publishing from the new admin interface.
    - [ ] Log publishing attempts and errors.

---

## 4. Admin/Editor Tools (Optional, for future)

- [ ] **Admin UI for Workflow**
    - [ ] Add admin/editor tools for managing post status, editing content, and triggering preview/publish actions.
    - [ ] Expose workflow status and logs in the admin interface.

---

## 5. Testing & QA

- [ ] **Visual Regression Testing**
    - [ ] Compare new preview output to old `/blog_old/_site/` HTML for pixel/structure accuracy.
    - [ ] Test on multiple devices and browsers.

- [ ] **Functionality Testing**
    - [ ] Test preview, listing, post detail, and publishing workflows end-to-end.
    - [ ] Validate data import and API integration.

---

*Last updated: {{DATE}}* 