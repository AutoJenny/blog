// DOM Ready Event
document.addEventListener('DOMContentLoaded', () => {
    initMobileNav();
    initSmoothScroll();
    setupFormValidation();
});

// Mobile Navigation Toggle
function initMobileNav() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('nav ul');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            const spans = navToggle.querySelectorAll('span');
            spans.forEach(span => span.classList.toggle('active'));
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
                const spans = navToggle.querySelectorAll('span');
                spans.forEach(span => span.classList.remove('active'));
            }
        });
    }
}

// Smooth Scrolling
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Date Formatting
function formatDate(date, format = 'YYYY-MM-DD') {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');

    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes);
}

// Form Validation
function setupFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (validateForm(this)) {
                // If validation passes, you can submit the form
                console.log('Form is valid, submitting...');
                this.submit();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    // Reset previous validation states
    form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    
    // Required fields
    form.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        }
    });
    
    // Email validation
    form.querySelectorAll('[type="email"]').forEach(field => {
        if (field.value && !emailRegex.test(field.value)) {
            field.classList.add('error');
            isValid = false;
        }
    });
    
    return isValid;
}

// Debounce Utility
function debounce(func, wait = 250) {
    let timeout;
    
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Example usage of debounce for window resize
const handleResize = debounce(() => {
    // Add your resize handling code here
    console.log('Window resized');
}, 250);

window.addEventListener('resize', handleResize);

// Update copyright year in footer
function updateCopyright() {
    const copyrightYear = document.querySelector('.copyright-year');
    if (copyrightYear) {
        copyrightYear.textContent = new Date().getFullYear();
    }
}

// Initialize copyright year
updateCopyright(); 