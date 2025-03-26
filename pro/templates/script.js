// Update glow effect based on cursor position
document.addEventListener('mousemove', (event) => {
    const glow = document.getElementById('glow');
    glow.style.top = `${event.clientY}px`;
    glow.style.left = `${event.clientX}px`;
});

// Enhance glow when hovering over specific elements
const elements = document.querySelectorAll('.btn, input, img, form');
elements.forEach((element) => {
    element.addEventListener('mouseenter', () => {
        const glow = document.getElementById('glow');
        glow.style.background = 'radial-gradient(circle, rgba(255, 255, 200, 0.9) 0%, rgba(255, 255, 255, 0) 70%)';
    });
    element.addEventListener('mouseleave', () => {
        const glow = document.getElementById('glow');
        glow.style.background = 'radial-gradient(circle, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0) 70%)';
    });
});
