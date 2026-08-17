/* =========================================================
   Afaq Real Estate Platform - Video & Booking Module (js/video.js)
   ========================================================= */

function getYouTubeEmbedUrl(url) {
    if (!url) return '';
    if (url.includes('embed/')) return url;
    var regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    var match = url.match(regExp);
    if (match && match[2].length === 11) {
        return 'https://www.youtube.com/embed/' + match[2] + '?autoplay=1';
    }
    return url;
}
window.getYouTubeEmbedUrl = getYouTubeEmbedUrl;

function openVideoModal(videoUrl) {
    var modal = document.getElementById('video-modal');
    var iframe = document.getElementById('video-iframe');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'video-modal';
        modal.className = 'afaq-modal-overlay';
        modal.innerHTML = '' +
        '<div class="afaq-modal-content video-modal-content">' +
            '<button class="modal-close-btn" onclick="closeVideoModal()"><i class="fas fa-times"></i></button>' +
            '<div class="video-container">' +
                '<iframe id="video-iframe" src="" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>' +
            '</div>' +
        '</div>';
        document.body.appendChild(modal);
        iframe = document.getElementById('video-iframe');
    }
    if (iframe) {
        iframe.src = getYouTubeEmbedUrl(videoUrl);
    }
    modal.classList.add('active');
}
window.openVideoModal = openVideoModal;

function closeVideoModal() {
    var modal = document.getElementById('video-modal');
    var iframe = document.getElementById('video-iframe');
    if (iframe) iframe.src = '';
    if (modal) modal.classList.remove('active');
}
window.closeVideoModal = closeVideoModal;

// Booking Modal
function openBookingModal(offerId) {
    var modal = document.getElementById('booking-modal');
    if (modal) modal.classList.add('active');
}
window.openBookingModal = openBookingModal;

function closeBookingModal() {
    var modal = document.getElementById('booking-modal');
    if (modal) modal.classList.remove('active');
}
window.closeBookingModal = closeBookingModal;

function handleBookingSubmit(e) {
    if (e) e.preventDefault();
    var payload = {
        kind: 'booking',
        timestamp: new Date().toISOString()
    };
    if (window.postToIngest) window.postToIngest(payload);
    window.showToast('تم حجز موعد المعاينة بنجاح!', 'success');
    closeBookingModal();
}
window.handleBookingSubmit = handleBookingSubmit;
