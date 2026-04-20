// main.js - Core UI Interactivity for IT Management Platform

document.addEventListener('DOMContentLoaded', () => {

    // =====================================================
    // SIDEBAR & NAVIGATION
    // =====================================================
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const mainContent = document.querySelector('.main-content');
    const sidebarToggleIcon = document.getElementById('sidebar-toggle-icon');
    let sidebarTimeout = null;
    let isSidebarExpanded = false;
    let isManualToggle = localStorage.getItem('sidebarCollapsed') === 'true';

    // Mobile toggles
    const mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
    const sidebarCloseToggle = document.getElementById('sidebar-toggle');
    
    if (mobileSidebarToggle) {
        mobileSidebarToggle.addEventListener('click', () => {
            sidebar?.classList.remove('lg:translate-x-0', '-translate-x-full');
            sidebar?.classList.add('translate-x-0');
            sidebarOverlay?.classList.remove('hidden');
        });
    }

    if (sidebarCloseToggle) {
        sidebarCloseToggle.addEventListener('click', () => {
            sidebar?.classList.remove('translate-x-0');
            sidebar?.classList.add('-translate-x-full');
            sidebarOverlay?.classList.add('hidden');
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar?.classList.remove('translate-x-0');
            sidebar?.classList.add('-translate-x-full');
            this.classList.add('hidden');
        });
    }

    // Desktop hover expansion
    if (isManualToggle) collapseSidebar(true);

    function expandSidebar() {
        if (isManualToggle || !sidebar) return;
        clearTimeout(sidebarTimeout);
        if (!isSidebarExpanded) {
            sidebar.classList.remove('sidebar-icon-only');
            sidebar.classList.add('sidebar-full');
            document.querySelectorAll('.sidebar-text').forEach(el => el.classList.remove('hidden-text'));
            
            if (mainContent) {
                mainContent.classList.remove('lg:ml-16');
                mainContent.classList.add('lg:ml-64');
            }
            if (sidebarToggleIcon) sidebarToggleIcon.classList.remove('rotate-180');
            isSidebarExpanded = true;
        }
    }

    function collapseSidebar(immediate = false) {
        if (isManualToggle && !immediate || !sidebar) return;
        
        const action = () => {
            sidebar.classList.remove('sidebar-full');
            sidebar.classList.add('sidebar-icon-only');
            document.querySelectorAll('.sidebar-text').forEach(el => el.classList.add('hidden-text'));
            
            if (mainContent) {
                mainContent.classList.remove('lg:ml-64');
                mainContent.classList.add('lg:ml-16');
            }
            if (sidebarToggleIcon) sidebarToggleIcon.classList.add('rotate-180');
            isSidebarExpanded = false;
        };

        if (immediate) action();
        else sidebarTimeout = setTimeout(action, 100);
    }

    const sidebarHoverToggle = document.getElementById('sidebar-hover-toggle');
    if (sidebarHoverToggle) {
        sidebarHoverToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            isManualToggle = !isManualToggle;
            
            if (isManualToggle) {
                collapseSidebar(true);
                localStorage.setItem('sidebarCollapsed', 'true');
            } else {
                expandSidebar();
                localStorage.setItem('sidebarCollapsed', 'false');
            }
        });
    }

    if (sidebar) {
        sidebar.addEventListener('mouseenter', () => clearTimeout(sidebarTimeout));
        sidebar.addEventListener('mouseleave', () => { if (!isManualToggle) collapseSidebar(); });
    }

    // =====================================================
    // SEARCH MODAL
    // =====================================================
    const searchInput = document.getElementById('search-modal-input');
    const searchModalResults = document.getElementById('search-modal-results');

    if (searchInput && searchModalResults) {
        searchInput.addEventListener('input', function() {
            const query = this.value;
            if (query.length > 2) {
                fetch(`/api/search/?q=${encodeURIComponent(query)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.count > 0) {
                            let html = '<div class="p-2">';
                            ['users', 'tickets', 'assets', 'projects'].forEach(type => {
                                if (data.results[type] && data.results[type].length > 0) {
                                    html += `<div class="text-xs font-semibold text-gray-400 uppercase tracking-wide px-2 mt-3 mb-1">${type}</div>`;
                                    data.results[type].forEach(item => {
                                        let link = '#';
                                        const display = item.name || item.title || item.username;
                                        if (type === 'users') link = `/edit-user/${item.id}/`;
                                        if (type === 'tickets') link = `/tickets/${item.id}/`;
                                        if (type === 'assets') link = `/assets/${item.id}/`;
                                        if (type === 'projects') link = `/project/${item.id}/`;
                                        html += `<a href="${link}" onclick="closeSearchModal()" class="flex items-center p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white text-sm transition-colors">${display}</a>`;
                                    });
                                }
                            });
                            html += '</div>';
                            searchModalResults.innerHTML = html;
                        } else {
                            searchModalResults.innerHTML = '<p class="p-4 text-center text-sm text-gray-400">No results found</p>';
                        }
                    }).catch(() => {
                        searchModalResults.innerHTML = '<p class="p-4 text-center text-sm text-red-500">Search failed.</p>';
                    });
            } else {
                searchModalResults.innerHTML = '<p class="p-4 text-center text-sm text-gray-400">Type at least 3 characters to search...</p>';
            }
        });
    }

    // =====================================================
    // NOTIFICATIONS & KEYBOARD
    // =====================================================
    document.getElementById('notifications-toggle')?.addEventListener('click', (e) => {
        e.stopPropagation();
        document.getElementById('notifications-dropdown')?.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('#notifications-toggle') && !e.target.closest('#notifications-dropdown')) {
            document.getElementById('notifications-dropdown')?.classList.add('hidden');
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.getElementById('notifications-dropdown')?.classList.add('hidden');
            window.closeSearchModal?.();
        }
    });

    // =====================================================
    // DARK MODE SYSTEM
    // =====================================================
    function updateDarkModeIcon(isDark) {
        const icon = document.getElementById('dark-mode-icon');
        if (icon) {
            icon.classList.remove(isDark ? 'fa-moon' : 'fa-sun');
            icon.classList.add(isDark ? 'fa-sun' : 'fa-moon');
        }
    }

    window.toggleDarkMode = function() {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateDarkModeIcon(isDark);
        showToast(isDark ? 'Dark mode enabled' : 'Light mode enabled', 'info', 2000);
    };

    updateDarkModeIcon(document.documentElement.classList.contains('dark'));
});

// Toast Notifications System exposed globally
window.showToast = function(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    
    const bgClasses = {
        success: 'bg-green-50 dark:bg-green-900 border-green-200 text-green-800 dark:text-green-100',
        error: 'bg-red-50 dark:bg-red-900 border-red-200 text-red-800 dark:text-red-100',
        warning: 'bg-yellow-50 dark:bg-yellow-900 border-yellow-200 text-yellow-800 dark:text-yellow-100',
        info: 'bg-blue-50 dark:bg-blue-900 border-blue-200 text-blue-800 dark:text-blue-100'
    };
    
    const icons = {
        success: '<i class="fas fa-check-circle text-green-500 dark:text-green-300"></i>',
        error: '<i class="fas fa-exclamation-circle text-red-500 dark:text-red-300"></i>',
        warning: '<i class="fas fa-exclamation-triangle text-yellow-500 dark:text-yellow-300"></i>',
        info: '<i class="fas fa-info-circle text-blue-500 dark:text-blue-300"></i>'
    };
    
    toast.className = `toast p-4 rounded-lg shadow-lg max-w-sm w-full flex items-center border ${bgClasses[type] || bgClasses.info}`;
    toast.innerHTML = `
        <div class="flex-shrink-0">${icons[type] || icons.info}</div>
        <div class="ml-3 flex-1"><p class="text-sm font-medium">${message}</p></div>
        <button class="ml-auto hover:opacity-75" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
    `;
    
    container.appendChild(toast);
    if (duration > 0) setTimeout(() => { toast.style.animation = "fadeOut 0.3s forwards"; setTimeout(() => toast.remove(), 300); }, duration);
};

// Confirm Modal
let _confirmCallback = null;

window.showConfirmation = function(title, message, onConfirm) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalMessage').textContent = message;
    _confirmCallback = onConfirm;
    document.getElementById('confirmModal').classList.remove('hidden');
};

window.closeConfirmModal = function() {
    document.getElementById('confirmModal').classList.add('hidden');
    _confirmCallback = null;
};

window.executeConfirm = function() {
    document.getElementById('confirmModal').classList.add('hidden');
    if (_confirmCallback) _confirmCallback();
    _confirmCallback = null;
};

// Search Modal
window.openSearchModal = function() {
    document.getElementById('search-modal')?.classList.remove('hidden');
    setTimeout(() => document.getElementById('search-modal-input')?.focus(), 50);
};

window.closeSearchModal = function() {
    document.getElementById('search-modal')?.classList.add('hidden');
    const input = document.getElementById('search-modal-input');
    const results = document.getElementById('search-modal-results');
    if (input) input.value = '';
    if (results) results.innerHTML = '<p class="p-4 text-center text-sm text-gray-400">Type at least 3 characters to search...</p>';
};

// Generic Modal Handling
window.showModal = function(modalId) {
    document.getElementById('modal-overlay')?.classList.remove('hidden');
    document.getElementById(modalId)?.classList.remove('hidden');
};

window.hideModal = function(modalId) {
    document.getElementById('modal-overlay')?.classList.add('hidden');
    document.getElementById(modalId)?.classList.add('hidden');
};
