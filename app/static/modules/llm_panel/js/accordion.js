/**
 * Accordion JavaScript
 * Handles expanding/collapsing of accordion sections
 */

export class Accordion {
    constructor() {
        this.init();
    }

    init() {
        // Add click listeners to all accordion toggles
        document.querySelectorAll('[data-accordion-toggle]').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleAccordion(toggle);
            });
        });
    }

    toggleAccordion(toggle) {
        const accordionItem = toggle.closest('.accordion-item');
        if (!accordionItem) return;

        const content = accordionItem.querySelector('.accordion-content');
        const icon = accordionItem.querySelector('.accordion-icon');
        
        if (!content || !icon) return;
        
        const isExpanded = content.classList.contains('show');
        
        // Close all other accordions
        document.querySelectorAll('.accordion-item').forEach(otherItem => {
            if (otherItem !== accordionItem) {
                const otherContent = otherItem.querySelector('.accordion-content');
                const otherIcon = otherItem.querySelector('.accordion-icon');
                if (otherContent && otherIcon) {
                    otherContent.classList.remove('show');
                    otherIcon.style.transform = 'rotate(0deg)';
                }
            }
        });
        
        // Toggle current accordion
        content.classList.toggle('show');
        icon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
    }
}

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

// Make toggleAccordion available globally
window.toggleAccordion = toggleAccordion; 