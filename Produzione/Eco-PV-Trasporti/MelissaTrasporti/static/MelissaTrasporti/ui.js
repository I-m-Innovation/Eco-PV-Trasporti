(function () {
    function onReady(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            window.setTimeout(callback, 0);
        }
    }

    function prefersReducedMotion() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    onReady(function () {
        if (!window.gsap || prefersReducedMotion()) {
            document.documentElement.classList.add('ui-motion-static');
            return;
        }

        var gsap = window.gsap;

        gsap.from('.navbar-brand img, .brand-title', {
            autoAlpha: 0,
            y: 4,
            duration: 0.25,
            stagger: 0.04,
            ease: 'power1.out',
            clearProps: 'transform,opacity,visibility'
        });

        gsap.from('[data-ui-panel]', {
            autoAlpha: 0,
            y: 8,
            duration: 0.32,
            stagger: 0.05,
            ease: 'power1.out',
            clearProps: 'transform,opacity,visibility'
        });

        gsap.from('.legend-item, .action-link', {
            autoAlpha: 0,
            duration: 0.24,
            stagger: 0.025,
            delay: 0.08,
            ease: 'power1.out',
            clearProps: 'opacity,visibility'
        });

        if (window.jQuery && document.getElementById('table-commesse')) {
            window.jQuery('#table-commesse').on('draw.dt', function () {
                gsap.fromTo(
                    '#table-commesse tbody tr',
                    {autoAlpha: 0.82},
                    {autoAlpha: 1, duration: 0.16, stagger: 0.008, ease: 'power1.out'}
                );
            });
        }
    });
}());
