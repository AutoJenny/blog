/**
 * Content Roles Reference Page
 * 
 * Shows full details of all content roles.
 */

class ContentRolesReference {
    constructor() {
        this.init();
    }
    
    init() {
        this.renderRoles();
        
        // Handle anchor links (e.g., #depth_long)
        const hash = window.location.hash.substring(1);
        if (hash) {
            setTimeout(() => {
                const element = document.getElementById(hash);
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    element.style.outline = '2px solid var(--color-primary, #2563eb)';
                    element.style.outlineOffset = '4px';
                }
            }, 100);
        }
    }
    
    renderRoles() {
        const container = document.getElementById('roles-reference');
        if (!container) return;
        
        const roles = [
            {
                code: 'REASSURANCE',
                displayName: 'Human Service',
                purpose: 'Reduce anxiety and friction. Give people permission to engage comfortably.',
                characteristics: 'Human, patient, calm. Mentions availability, time, flexibility. Often references phone or conversation.',
                constraints: [
                    'Must not promote products',
                    'Must not contain sales language',
                    'Must not provide technical depth'
                ],
                typicalLength: 'Short (1–3 short paragraphs, 50-300 words)',
                typicalSources: 'Service principles, customer interaction philosophy, reassurance pool',
                requiresTopic: false,
                requiresSourcePage: false,
                usage: 'Saturday 14:30 (Facebook)'
            },
            {
                code: 'AUTHORITY_SHORT',
                displayName: 'Quiet Authority',
                purpose: 'Establish quiet credibility through factual context or reframing.',
                characteristics: 'Declarative, calm and factual. Usually avoids first-person ("we"). Often myth-correcting or context-setting.',
                constraints: [
                    'No reassurance language',
                    'No service mentions',
                    'No calls to action',
                    'One idea only'
                ],
                typicalLength: 'Very short (1–3 lines, 20-150 words)',
                typicalSources: 'Clan Info Centre (single article/page), historical or practical assertions',
                requiresTopic: false,
                requiresSourcePage: true,
                usage: 'Future implementation (X/Twitter planned)'
            },
            {
                code: 'DEPTH_LONG',
                displayName: 'Deep Dive',
                purpose: 'Demonstrate embedded knowledge and judgement.',
                characteristics: 'Narrow scope, explanatory (not summarising), structured with white space, reflective close (not a conclusion).',
                constraints: [
                    'No selling',
                    'No service mentions',
                    'No product mentions',
                    'Must be grounded in Clan Info Centre source material',
                    'Must not introduce facts beyond the source'
                ],
                typicalLength: '120–220 words',
                typicalSources: 'Clan Info Centre (single page or section), weekly topic from KB Topic Rota',
                requiresTopic: true,
                requiresSourcePage: true,
                usage: 'Sunday 15:00 (Facebook)'
            },
            {
                code: 'CULTURE',
                displayName: 'Cultural Detail',
                purpose: 'Provide personality, rhythm, and familiarity.',
                characteristics: 'Light, repeatable formats, familiar cadence.',
                constraints: [
                    'No selling',
                    'No authority claims',
                    'No deep explanation'
                ],
                typicalLength: 'Very short (10-100 words)',
                typicalSources: 'Word / Phrase / Insult formats, fixed pools',
                requiresTopic: false,
                requiresSourcePage: false,
                usage: 'Monday 09:00, Wednesday 09:00, Friday 11:07 (Facebook)'
            },
            {
                code: 'COMMERCE',
                displayName: 'Product Spotlight',
                purpose: 'Make products visible and concrete.',
                characteristics: 'Visual or descriptive, straightforward, non-educational.',
                constraints: [
                    'No deep heritage explanation',
                    'No reassurance language',
                    'No long-form content'
                ],
                typicalLength: 'Short to medium (50-200 words)',
                typicalSources: 'Product catalogue',
                requiresTopic: false,
                requiresSourcePage: false,
                usage: 'Tuesday 17:00, Thursday 17:00 (Facebook)'
            }
        ];
        
        container.innerHTML = roles.map(role => {
            const roleClass = role.code.toLowerCase().replace('_', '-');
            return `
                <div class="role-reference-card" id="${role.code.toLowerCase()}">
                    <div class="role-card-header">
                        <div class="role-card-badge">
                            <span class="role-badge ${roleClass}">${role.displayName}</span>
                            <span class="role-code">${role.code}</span>
                        </div>
                    </div>
                    <div class="role-card-body">
                        <div class="role-card-section">
                            <h3>Purpose</h3>
                            <p>${role.purpose}</p>
                        </div>
                        <div class="role-card-section">
                            <h3>Characteristics</h3>
                            <p>${role.characteristics}</p>
                        </div>
                        <div class="role-card-section">
                            <h3>Constraints</h3>
                            <ul>
                                ${role.constraints.map(c => `<li>${c}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="role-card-section">
                            <h3>Typical Length</h3>
                            <p>${role.typicalLength}</p>
                        </div>
                        <div class="role-card-section">
                            <h3>Typical Sources</h3>
                            <p>${role.typicalSources}</p>
                        </div>
                        <div class="role-card-section">
                            <h3>Requirements</h3>
                            <ul>
                                <li>Topic required: ${role.requiresTopic ? 'Yes' : 'No'}</li>
                                <li>Source page required: ${role.requiresSourcePage ? 'Yes' : 'No'}</li>
                            </ul>
                        </div>
                        <div class="role-card-section">
                            <h3>Usage</h3>
                            <p>${role.usage}</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ContentRolesReference();
    });
} else {
    new ContentRolesReference();
}
