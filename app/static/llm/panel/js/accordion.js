function toggleAccordion(id) {
    const content = document.getElementById(`${id}-content`);
    const icon = document.getElementById(`${id}-icon`);
    
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.classList.add('rotate-180');
    } else {
        content.classList.add('hidden');
        icon.classList.remove('rotate-180');
    }
} 