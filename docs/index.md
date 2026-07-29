# Gareth Thomas

**Consultant, technologist, and founder** based in Eindhoven, Netherlands.

**Embracing Change** is my motto — I love adjusting to new technologies and leveraging the right tools for the right job. I'm a consultant, technologist, and founder based in Eindhoven, Netherlands. Over 20 years I've moved from control-theory engineering at MathWorks to co-founding and running software businesses, to consulting delivery at CGI — while chairing PyData Eindhoven's community for six years and hosting the Inspiring Computing podcast.

[Get in touch](mailto:gareth.bj.thomas@gmail.com){ .md-button .md-button--primary }
[LinkedIn profile](https://nl.linkedin.com/in/g-thomas){ .md-button }
[Download CV (short)](assets/gareth-thomas-cv-short.pdf){ .md-button }
[Download CV (long)](assets/gareth-thomas-cv-long.pdf){ .md-button }

<div markdown="0">
<style>
#cv-bg-canvas {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    width: 100vw;
    height: 100vh;
}
@media (prefers-reduced-motion: reduce) { #cv-bg-canvas { opacity: .7; } }
</style>
<script>
(function () {
    if (document.getElementById("cv-bg-canvas")) return;
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var canvas = document.createElement("canvas");
    canvas.id = "cv-bg-canvas";
    canvas.setAttribute("aria-hidden", "true");
    // Appended directly to <body> (not left inline in the article) so its
    // `position: fixed` is always relative to the real viewport, even if
    // some ancestor in the theme's layout applies a CSS transform.
    document.body.appendChild(canvas);
    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var DPR = Math.min(window.devicePixelRatio || 1, 2);
    var W, H;
    function resize() {
        W = Math.max(1, Math.round(window.innerWidth * DPR));
        H = Math.max(1, Math.round(window.innerHeight * DPR));
        canvas.width = W;
        canvas.height = H;
    }
    resize();

    // Clifford strange attractor: a chaotic system whose orbit traces an
    // ever-shifting cloud of points; parameters drift slowly (and lean
    // toward the pointer) so the pattern never quite repeats.
    var N = 3200;
    var xs = new Float32Array(N);
    var ys = new Float32Array(N);
    for (var i = 0; i < N; i++) {
        xs[i] = Math.random() * 4 - 2;
        ys[i] = Math.random() * 4 - 2;
    }

    var t = 0, mx = 0, my = 0, tmx = 0, tmy = 0;
    window.addEventListener("pointermove", function (e) {
        tmx = (e.clientX / window.innerWidth) * 2 - 1;
        tmy = (e.clientY / window.innerHeight) * 2 - 1;
    });

    function iterate(n) {
        t += 0.0025 * n;
        mx += (tmx - mx) * 0.02;
        my += (tmy - my) * 0.02;
        var a = -1.4 + Math.sin(t * 0.6) * 0.25 + mx * 0.15;
        var b = 1.6 + Math.cos(t * 0.5) * 0.2 + my * 0.15;
        var c = 1.0 + Math.sin(t * 0.37) * 0.15;
        var d = 0.7 + Math.cos(t * 0.29) * 0.15;
        for (var i = 0; i < N; i++) {
            var x = xs[i], y = ys[i];
            xs[i] = Math.sin(a * y) + c * Math.cos(a * x);
            ys[i] = Math.sin(b * x) + d * Math.cos(b * y);
        }
    }

    // Dark theme cycles green -> orange -> blue -> green. Light theme drops
    // orange and just merges green and blue (a softer teal blend), so it
    // never reads as white or washes out against a light page.
    var HUES_DARK = [140, 35, 220];
    var HUES_LIGHT = [140, 220];
    function hueAt(phase, hues) {
        var len = hues.length;
        var p = ((phase % len) + len) % len;
        var idx = Math.floor(p);
        var frac = p - idx;
        var from = hues[idx], to = hues[(idx + 1) % len];
        return from + (to - from) * frac;
    }

    function isDarkScheme() {
        return document.body.getAttribute("data-md-color-scheme") === "slate";
    }

    var scale, ox, oy;
    function computeTransform() {
        scale = Math.min(W, H) / 4.2;
        ox = W / 2;
        oy = H / 2;
    }
    computeTransform();

    function draw() {
        // Fade the previous frame toward transparent (never toward black
        // or white), so it works over both the light and dark theme.
        ctx.globalCompositeOperation = "destination-out";
        ctx.fillStyle = "rgba(0,0,0,0.06)";
        ctx.fillRect(0, 0, W, H);
        ctx.globalCompositeOperation = "source-over";

        // Read the active theme each frame so this reacts live to the
        // light/dark toggle without needing a page reload.
        var dark = isDarkScheme();
        var hues = dark ? HUES_DARK : HUES_LIGHT;
        var lightness = dark ? 46 : 38;
        var alpha = dark ? 0.16 : 0.1;
        var huePhase = t * 0.08;
        var size = Math.max(1, 1.3 * DPR);
        for (var i = 0; i < N; i++) {
            var px = ox + xs[i] * scale;
            var py = oy + ys[i] * scale;
            if (px < 0 || px > W || py < 0 || py > H) continue;
            var hue = hueAt(huePhase + (xs[i] + ys[i]) * 0.15, hues);
            // Moderate saturation, low lightness/alpha keep this subtle and
            // legible behind text, never washing out toward white.
            ctx.fillStyle = "hsla(" + hue + ", 65%, " + lightness + "%, " + alpha + ")";
            ctx.fillRect(px, py, size, size);
        }
    }

    // Warm up so the very first paint already shows a full pattern,
    // instead of particles slowly trickling in from a blank canvas.
    for (var w = 0; w < 40; w++) iterate(1);

    var raf, running = true;
    function loop() {
        iterate(1);
        draw();
        if (running) raf = requestAnimationFrame(loop);
    }

    if (reduceMotion) {
        for (var k = 0; k < 30; k++) iterate(1);
        draw();
    } else {
        for (var k2 = 0; k2 < 12; k2++) { iterate(1); draw(); }
        raf = requestAnimationFrame(loop);
    }

    document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
            running = false;
            if (raf) cancelAnimationFrame(raf);
        } else if (!reduceMotion) {
            running = true;
            raf = requestAnimationFrame(loop);
        }
    });

    var resizeTimer;
    window.addEventListener("resize", function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            resize();
            computeTransform();
        }, 150);
    });
})();
</script>
</div>

## Where I've worked

[![CGI](assets/logos/cgi.png){ width="48" }](experience.md#cgi-nederland)
[![MathWorks](assets/logos/mathworks.png){ width="48" }](experience.md#mathworks)
[![VersionBay](assets/logos/versionbay.png){ width="48" }](experience.md#entrepreneurial-ventures)
[![Open iT](assets/logos/openit.png){ width="70" }](experience.md#entrepreneurial-ventures)
[![Oceanscan](assets/logos/oceanscan.png){ width="48" }](experience.md#oceanscan)
[![Altran CIS](assets/logos/altran.svg){ width="100" }](experience.md#altran-cis)
[![PyData Eindhoven](assets/logos/pydata.png){ width="48" }](events.md)
[![Inspiring Computing](assets/logos/inspiringcomputing.jpg){ width="48" }](podcast.md)

## At a glance

| | |
|---|---|
| **Role** | Consultant, CGI Nederland |
| **Location** | Nuenen, Netherlands |
| **Focus** | Consulting • Founder • Community |
| **Languages** | English, Portuguese, Italian, Dutch |

## By the numbers

| 20+ | 1 | 6+ | 4 |
|---|---|---|---|
| Years in engineering, consulting & entrepreneurship | Company founded — VersionBay | Years chairing PyData Eindhoven | Languages spoken |

## About

I'm a consultant and founder with a control-theory engineering foundation. After nearly a decade at MathWorks — from application engineer to Business Development Manager for global Academic strategy — I co-founded VersionBay, running it alongside a stint as Country Manager Benelux at Open iT and the [MATLAB Coders](hobbies.md#matlab-coders) hobby project. Today I work as a Consultant at CGI Nederland after a year directing consulting services, having previously led delivery, sales enablement, and technical strategy across the US, Portugal, and the Netherlands. Alongside client work, I chair PyData Eindhoven's organizing committee and co-host the Inspiring Computing podcast — both going on their sixth and fourth year respectively.

Raised in an actuarial family, and now married with two kids. I try to live my motto, not just say it: I build my own apps ([Meetello](hobbies.md#built-maintain), [Brainport AI's Game Hub](hobbies.md#built-maintain)), lean on AI daily to accelerate my work, and even used it to build this very CV site.

## What people say

A few LinkedIn recommendations from colleagues and clients over the years:

> Gareth is one of those people that can motivate an entire team.
>
> — **Duarte Antunes**, Associate Professor, Eindhoven University of Technology

<!-- -->

> Working with Gareth at The MathWorks is a real pleasure. He has great enthusiasm and energy for every task and always considered ways to improve how things were done.
>
> — **Marc Wouters**, Sr Sales Account Manager Belux, MathWorks

<!-- -->

> [He] turns out to be an outstanding public speaker and to have amazing explanation skills. In short, he is an inspirational co-worker who has the perfect combination of skills that make true leaders.
>
> — **Jean-Philippe Villaréal**, Lead Developer, Consafe Logistics Group

<!-- -->

> Gareth's "Yes we can!" mentality, technical credibility and drive for results sparks to everyone he works with.
>
> — **Caspar Perik**, Director of Business Development, Grace

See [Experience](experience.md), [Education](education.md), the full [Timeline](timeline.md), [Events Organized](events.md), [Podcast Episodes](podcast.md), [Talks Given](talks.md), and [Hobbies](hobbies.md) for details.
