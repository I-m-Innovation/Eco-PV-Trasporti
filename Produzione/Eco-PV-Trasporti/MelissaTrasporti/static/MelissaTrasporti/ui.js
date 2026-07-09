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

    function fileListLabel(files) {
        if (!files || !files.length) {
            return 'Nessun file selezionato';
        }
        if (files.length === 1) {
            return files[0].name;
        }
        return files.length + ' file selezionati';
    }

    function setupFileDropzones() {
        document.querySelectorAll('[data-upload-dropzone]').forEach(function (zone) {
            var input = zone.querySelector('input[type="file"]');
            var label = zone.querySelector('[data-upload-file-name]');

            if (!input || !label) {
                return;
            }

            function updateLabel() {
                label.textContent = fileListLabel(input.files);
            }

            input.addEventListener('change', updateLabel);

            ['dragenter', 'dragover'].forEach(function (eventName) {
                zone.addEventListener(eventName, function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    zone.classList.add('is-dragover');
                });
            });

            ['dragleave', 'dragend', 'drop'].forEach(function (eventName) {
                zone.addEventListener(eventName, function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    zone.classList.remove('is-dragover');
                });
            });

            zone.addEventListener('drop', function (event) {
                if (!event.dataTransfer || !event.dataTransfer.files.length) {
                    return;
                }
                input.files = event.dataTransfer.files;
                input.dispatchEvent(new Event('change', {bubbles: true}));
            });
        });
    }

    onReady(function () {
        setupFileDropzones();

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
