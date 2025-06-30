/**
 * LLM Panel JavaScript
 * Handles field mapping and value persistence
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordions
    document.querySelectorAll('[data-accordion]').forEach(accordion => {
        const button = accordion.querySelector('button');
        const content = accordion.querySelector('.accordion-content');
        const icon = accordion.querySelector('.accordion-icon');

        button.addEventListener('click', () => {
            const isExpanded = content.classList.contains('show');
            content.classList.toggle('show');
            icon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
        });
    });

    // Initialize field mapping persistence
    document.querySelectorAll('.field-mapping-select').forEach(select => {
        select.addEventListener('change', async (e) => {
            const targetId = e.target.dataset.targetId;
            const section = e.target.dataset.section;
            const fieldName = e.target.value;
            
            // Determine accordion type based on section
            const accordion_type = section === 'inputs' ? 'inputs' : 'outputs';

            try {
                const response = await fetch('/api/workflow/fields/mappings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        target_id: targetId,
                        field_name: fieldName,
                        section: section,
                        accordion_type: accordion_type
                    })
                });

                if (response.ok) {
                    // Show success indicator
                    select.classList.add('success');
                    setTimeout(() => select.classList.remove('success'), 2000);
                } else {
                    // Show error indicator
                    select.classList.add('error');
                    setTimeout(() => select.classList.remove('error'), 2000);
                }
            } catch (error) {
                console.error('Error updating field mapping:', error);
                // Show error indicator
                select.classList.add('error');
                setTimeout(() => select.classList.remove('error'), 2000);
            }
        });
    });
}); 