// Workflow Navigation JavaScript

// Handle post selector changes
document.getElementById('post-selector')?.addEventListener('change', function () {
    const newPostId = this.value;
    // Build the new URL, preserving stage/substage/step
    let path = window.location.pathname.split('/').filter(Boolean);
    // path: ["workflow", post_id, stage, substage, step]
    if (path.length >= 2) {
        path[1] = newPostId;
        window.location.pathname = '/' + path.join('/') + '/';
    }
}); 