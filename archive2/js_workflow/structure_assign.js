// Get post ID from URL
function getPostId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('post_id');
}

// Initialize accordion functionality
function initAccordion() {
    const accordionButtons = document.querySelectorAll('#sections-accordion button');
    accordionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const content = button.nextElementSibling;
            const isExpanded = button.getAttribute('aria-expanded') === 'true';
            
            button.setAttribute('aria-expanded', !isExpanded);
            content.style.display = isExpanded ? 'none' : 'block';
            
            // Rotate arrow
            const arrow = button.querySelector('svg');
            arrow.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
        });
    });
}

// Parse multiline input into array
function parseMultilineInput(text) {
    return text.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
}

// Allocate content using LLM
async function allocateContent() {
    const postId = getPostId();
    if (!postId) {
        throw new Error('No post ID found');
    }

    // Get all sections
    const sections = Array.from(document.querySelectorAll('#sections-accordion > div')).map(section => ({
        id: section.querySelector('ul').id.split('-')[1],
        heading: section.querySelector('span').textContent,
        description: section.querySelector('p').textContent
    }));

    // Get all facts
    const facts = Array.from(document.querySelectorAll('#facts-list > div')).map(fact => 
        fact.querySelector('p').textContent
    );

    const resp = await fetch(`/api/v1/structure/allocate/${postId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sections,
            facts
        })
    });

    if (!resp.ok) {
        const error = await resp.json();
        throw new Error(error.error || 'Failed to allocate content');
    }

    const result = await resp.json();
    return result;
}

// Render allocated facts in sections
function renderAllocatedFacts(allocations) {
    // Clear existing allocations
    document.querySelectorAll('[id^="section-"][id$="-facts"]').forEach(list => {
        list.innerHTML = '';
    });

    // Create Additional Information section if needed
    let additionalSection = document.querySelector('#section-additional');
    if (!additionalSection) {
        const accordion = document.getElementById('sections-accordion');
        additionalSection = document.createElement('div');
        additionalSection.className = 'border border-gray-700 rounded-lg';
        additionalSection.innerHTML = `
            <button class="w-full px-4 py-3 text-left bg-gray-700 hover:bg-gray-600 rounded-t-lg flex justify-between items-center">
                <span class="font-medium text-gray-200">Additional Information</span>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </button>
            <div class="px-4 py-3 bg-gray-800 rounded-b-lg">
                <p class="text-gray-300">Facts that don't clearly fit into other sections.</p>
                <div class="mt-3">
                    <h5 class="text-sm font-medium text-gray-400 mb-2">Assigned Facts:</h5>
                    <ul id="section-additional-facts" class="space-y-2"></ul>
                </div>
            </div>
        `;
        accordion.appendChild(additionalSection);
    }

    // Add new allocations
    allocations.allocations.forEach(allocation => {
        const list = document.getElementById(`section-${allocation.section_id}-facts`);
        if (list) {
            const li = document.createElement('li');
            li.className = 'text-gray-300';
            li.textContent = allocation.fact;
            list.appendChild(li);
        }
    });

    // Initialize accordion for new section
    initAccordion();
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    // Initialize accordion
    initAccordion();

    // Add click handler for allocate button
    const allocateButton = document.getElementById('allocate-content');
    if (allocateButton) {
        allocateButton.addEventListener('click', async () => {
            try {
                const result = await allocateContent();
                renderAllocatedFacts(result);
                alert('Content allocated successfully!');
            } catch (error) {
                console.error('Error allocating content:', error);
                alert('Failed to allocate content: ' + error.message);
            }
        });
    }
}); 