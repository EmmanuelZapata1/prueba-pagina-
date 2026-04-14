let themeTransitionTimer;

function applyThemeState(isDark) {
    const root = document.documentElement;
    const backgroundColor = isDark ? '#030610' : '#ffffff';
    const textColor = isDark ? '#daeeff' : '#212529';

    root.classList.toggle('dark-mode', isDark);
    root.style.colorScheme = isDark ? 'dark' : 'light';
    root.style.backgroundColor = backgroundColor;

    if (document.body) {
        document.body.style.backgroundColor = backgroundColor;
        document.body.style.color = textColor;
    }
}

function syncThemeToggleUI(isDark) {
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');

    if (themeToggle) {
        themeToggle.setAttribute('aria-pressed', String(isDark));
        themeToggle.setAttribute('aria-label', isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
        themeToggle.dataset.theme = isDark ? 'dark' : 'light';
    }

    if (sunIcon) sunIcon.classList.toggle('active', !isDark);
    if (moonIcon) moonIcon.classList.toggle('active', isDark);
}

function saveThemeToCookie(theme) {
    localStorage.setItem('theme', theme);
    document.cookie = 'theme=' + theme + '; path=/; max-age=' + (365*24*60*60) + '; samesite=Lax';
    fetch('/api/theme', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({theme: theme})
    }).catch(() => {});
}

function toggleTheme() {
    const root = document.documentElement;
    root.classList.add('theme-animating');
    window.clearTimeout(themeTransitionTimer);
    void root.offsetWidth;

    const isDark = !root.classList.contains('dark-mode');
    applyThemeState(isDark);
    saveThemeToCookie(isDark ? 'dark' : 'light');
    syncThemeToggleUI(isDark);

    themeTransitionTimer = window.setTimeout(() => {
        root.classList.remove('theme-animating');
    }, 250);
    
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { isDark } }));
}

function getTheme() {
    return localStorage.getItem('theme') === 'dark' ? 'dark' : 'light';
}

(function applyThemeEarly() {
    try {
        const savedTheme = localStorage.getItem('theme');
        const finalIsDark = savedTheme === 'dark';
        applyThemeState(finalIsDark);

        const color = localStorage.getItem('accent');
        if (color) document.documentElement.style.setProperty('--accent', color);
    } catch (e) {}
})();

if (!document.readyState || document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
        syncThemeToggleUI(getTheme() === 'dark');
        document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
    });
} else {
    syncThemeToggleUI(getTheme() === 'dark');
    document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
}

window.addEventListener('storage', function (e) {
    if (e.key === 'theme') {
        const isDark = e.newValue === 'dark';
        applyThemeState(isDark);
        syncThemeToggleUI(isDark);
    }
});
