// js/skeleton-loader.js (جديد)

function showSkeletons(containerId, count = 6) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = Array(count).fill(0).map(() => `
        <div class="offer-card skeleton-card">
            <div class="skeleton skeleton-image"></div>
            <div class="skeleton skeleton-text medium"></div>
            <div class="skeleton skeleton-text short"></div>
            <div class="skeleton skeleton-text long"></div>
        </div>
    `).join('');
}

function hideSkeletons(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
}
