/**
 * LLM Panel JavaScript
 * Handles field mapping and value persistence
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize field selector
    const fieldSelector = new FieldSelector();

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

            try {
                const response = await fetch('/workflow/api/update_field_mapping/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        target_id: targetId,
                        field_name: fieldName,
                        section: section
                    })
                });

                if (response.ok) {
                    // Update the field value display
                    const fieldValue = await window.fieldSelector.getFieldValue(fieldName);
                    const displayElement = document.querySelector(`[data-field-display="${targetId}"]`);
                    if (displayElement) {
                        displayElement.textContent = fieldValue || '';
                    }
                    
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