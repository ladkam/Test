// Dark mode toggle functionality
(function() {
    // Check for saved theme preference or default to light mode
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        const themeToggle = document.getElementById('theme-toggle');

        if (themeToggle) {
            themeToggle.addEventListener('click', function() {
                let theme = document.documentElement.getAttribute('data-theme');
                let newTheme = theme === 'dark' ? 'light' : 'dark';

                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);

                // Add a subtle animation class
                document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
            });
        }
    });
})();
