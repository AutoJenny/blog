# Header Image Upload Diagnosis

## Systematic Comparison: Header vs Section Images

### 1. PATH EXTRACTION
**Header:**
- Line 443: `header_path = post.get('header_image', {}).get('path')`
- Path format: `/static/content/posts/90/header/optimized/header.jpg`

**Section:**
- Line 499: `section_path = section['image']['path']`
- Path format: `/static/content/posts/90/sections/845/optimized/845.jpg`

**DIFFERENCE:** None - both extract web paths correctly

### 2. PATH CONVERSION
**Header:**
- Line 455: `fs_path = path_resolver.convert_web_path_to_filesystem(header_path)`
- Inside try block

**Section:**
- Line 510: `fs_path = path_resolver.convert_web_path_to_filesystem(section_path)`
- Outside try block
- Line 524: Converts AGAIN (redundant) inside try block

**DIFFERENCE:** Section converts twice (redundant but harmless)

### 3. FILE EXISTENCE CHECK
**Header:**
- Line 459: Checks `os.path.exists(fs_path)` - logs error if not found
- Line 466: Checks AGAIN `os.path.exists(fs_path)` - only uploads if True

**Section:**
- Line 511: Checks `os.path.exists(fs_path)` - logs error if not found
- Does NOT check again before upload attempt

**DIFFERENCE:** Header has double-check, section doesn't (but both should work)

### 4. UPLOAD ATTEMPT
**Header:**
- Line 470: `uploaded_url = self.upload_image(fs_path, filename)`
- Inside nested if blocks: `if header_path:` → `try:` → `if os.path.exists(fs_path):`

**Section:**
- Line 527: `uploaded_url = self.upload_image(fs_path, filename)`
- Inside nested blocks: `if section.get('image')...` → `try:`

**DIFFERENCE:** Both call `upload_image` with filesystem path

### 5. STORING RESULT
**Header:**
- Line 474: `uploaded_images[header_path] = uploaded_url`
- Only if `uploaded_url` is truthy
- Uses WEB path as key: `/static/content/posts/90/header/optimized/header.jpg`

**Section:**
- Line 529: `uploaded_images[section_path] = uploaded_url`
- Only if `uploaded_url` is truthy
- Uses WEB path as key: `/static/content/posts/90/sections/845/optimized/845.jpg`

**DIFFERENCE:** None - both use web paths as keys

### 6. ERROR HANDLING
**Header:**
- Line 485-488: Catches ALL exceptions in try block
- Logs error and continues

**Section:**
- Line 533-534: Catches exceptions in try block
- Logs error and continues

**DIFFERENCE:** Both catch exceptions similarly

## CRITICAL FINDING

The code structure is nearly identical. The most likely issues are:

1. **Header image upload is failing silently** - `upload_image()` returns `None` but error is caught
2. **Path mismatch** - The key stored doesn't match the key looked up
3. **Exception in upload_image** - An exception is being caught and not re-raised

## RECOMMENDED FIX

Make header image processing EXACTLY match section image processing:

1. Move file existence check outside try block (like sections)
2. Remove redundant file existence check
3. Ensure upload attempt happens regardless of file check (let upload_image handle errors)
4. Add explicit logging before and after upload_image call

