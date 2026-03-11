/**
 * Bubble canvas animation – cyan floating bubbles
 */
(function () {
    const canvas = document.getElementById('bubbleCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let W = window.innerWidth;
    let H = window.innerHeight;
    canvas.width = W;
    canvas.height = H;

    window.addEventListener('resize', () => {
        W = window.innerWidth;
        H = window.innerHeight;
        canvas.width = W;
        canvas.height = H;
    });

    const COLORS = [
        'rgba(6,182,212,',
        'rgba(34,211,238,',
        'rgba(103,232,249,',
        'rgba(14,116,144,',
        'rgba(8,145,178,',
    ];

    function randomBetween(a, b) {
        return a + Math.random() * (b - a);
    }

    function createBubble() {
        const r = randomBetween(8, 42);
        return {
            x: randomBetween(0, W),
            y: H + r + randomBetween(0, H * 0.3),
            r,
            speed: randomBetween(0.3, 1.4),
            drift: randomBetween(-0.3, 0.3),
            alpha: randomBetween(0.06, 0.22),
            color: COLORS[Math.floor(Math.random() * COLORS.length)],
            wobble: randomBetween(0, Math.PI * 2),
            wobbleSpeed: randomBetween(0.008, 0.025),
        };
    }

    // One bubble per ~20 000px² of viewport area, capped at 55 for performance
    const COUNT = Math.min(55, Math.floor((W * H) / 20000));
    const bubbles = Array.from({ length: COUNT }, createBubble);

    // Stagger initial positions
    bubbles.forEach(b => {
        b.y = randomBetween(-b.r * 2, H + b.r);
    });

    function drawBubble(b) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.strokeStyle = b.color + (b.alpha * 1.4) + ')';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Inner sheen
        const grad = ctx.createRadialGradient(
            b.x - b.r * 0.3, b.y - b.r * 0.3, b.r * 0.08,
            b.x, b.y, b.r
        );
        grad.addColorStop(0, b.color + (b.alpha * 0.6) + ')');
        grad.addColorStop(1, b.color + '0)');
        ctx.fillStyle = grad;
        ctx.fill();
        ctx.restore();
    }

    let raf;
    function animate() {
        ctx.clearRect(0, 0, W, H);
        bubbles.forEach(b => {
            b.wobble += b.wobbleSpeed;
            b.x += b.drift + Math.sin(b.wobble) * 0.4;
            b.y -= b.speed;
            if (b.y < -b.r * 2) {
                Object.assign(b, createBubble());
                b.y = H + b.r;
            }
            drawBubble(b);
        });
        raf = requestAnimationFrame(animate);
    }

    animate();
})();
