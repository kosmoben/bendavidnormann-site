// Starfield background: deterministic stars, gentle twinkle, slow parallax.
(() => {
  const c = document.getElementById("sky");
  if (!c) return;
  const ctx = c.getContext("2d");
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let stars = [], w = 0, h = 0, dpr = 1;
  let seed = 7;
  const rand = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
  function build() {
    dpr = Math.min(devicePixelRatio || 1, 2);
    w = c.width = innerWidth * dpr; h = c.height = innerHeight * dpr;
    c.style.width = innerWidth + "px"; c.style.height = innerHeight + "px";
    seed = 7;
    const n = Math.round((innerWidth * innerHeight) / 2600);
    stars = Array.from({ length: n }, () => {
      const band = rand() < 0.45; // cluster some stars along a diagonal "milky way"
      let x = rand(), y = rand();
      if (band) { const t = rand(); x = t; y = 0.15 + t * 0.55 + (rand() - 0.5) * 0.18; }
      const big = rand() < 0.06;
      return { x: x * w, y: y * h, r: (big ? 1.4 + rand() * 1.2 : 0.3 + rand() * 0.9) * dpr,
               a: 0.35 + rand() * 0.65, tw: rand() * Math.PI * 2, sp: 0.4 + rand() * 1.4,
               green: rand() < 0.12, depth: 0.2 + rand() * 0.8 };
    });
  }
  function draw(t) {
    ctx.clearRect(0, 0, w, h);
    const g = ctx.createLinearGradient(0, h * 0.1, w, h * 0.9);
    g.addColorStop(0, "rgba(157,255,122,0)"); g.addColorStop(0.5, "rgba(157,255,122,0.035)"); g.addColorStop(1, "rgba(120,140,255,0.03)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    const sy = scrollY * dpr;
    for (const s of stars) {
      const tw = still ? 1 : 0.65 + 0.35 * Math.sin(t / 1000 * s.sp + s.tw);
      const y = ((s.y - sy * s.depth * 0.15) % h + h) % h;
      ctx.globalAlpha = s.a * tw;
      ctx.fillStyle = s.green ? "#9dff7a" : "#f4f6ff";
      ctx.beginPath(); ctx.arc(s.x, y, s.r, 0, Math.PI * 2); ctx.fill();
      if (s.r > 1.6 * dpr) { ctx.globalAlpha *= 0.25; ctx.beginPath(); ctx.arc(s.x, y, s.r * 3, 0, Math.PI * 2); ctx.fill(); }
    }
    ctx.globalAlpha = 1;
    if (!still) requestAnimationFrame(draw);
  }
  build(); addEventListener("resize", build);
  if (still) { draw(0); addEventListener("scroll", () => draw(0), { passive: true }); } else requestAnimationFrame(draw);
})();
