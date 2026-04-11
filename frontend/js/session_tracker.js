function autoTrackLinks() {
    document.querySelectorAll('a[data-track]')
        .forEach(function(link) {
            link.addEventListener('click', function() {
                if (typeof logEvent === 'function') {
                    logEvent('button_click', 
                        link.getAttribute('data-track'));
                }
            });
        });
}

function autoTrackButtons() {
    document.querySelectorAll('button[data-track]')
        .forEach(function(btn) {
            btn.addEventListener('click', function() {
                if (typeof logEvent === 'function') {
                    logEvent('button_click', 
                        btn.getAttribute('data-track'));
                }
            });
        });
}

// Log page view after 1 second delay
// so auth_token is definitely in sessionStorage
setTimeout(function() {
    if (typeof logEvent === 'function') {
        logEvent('page_view', window.location.pathname);
    }
}, 1000);

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        autoTrackLinks();
        autoTrackButtons();
    });
} else {
    autoTrackLinks();
    autoTrackButtons();
}
