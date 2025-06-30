function toggleAccordion(sectionId) {
    const content = document.getElementById(`${sectionId}-content`);
    const icon = document.getElementById(`${sectionId}-icon`);
    
    if (!content || !icon) return;

    // Toggle visibility
    content.classList.toggle('hidden');
    
    // Rotate icon
    if (content.classList.contains('hidden')) {
        icon.style.transform = 'rotate(0deg)';
    } else {
        icon.style.transform = 'rotate(180deg)';
    }
} 