"use client";

import { useEffect, useRef } from "react";

type Star = {
  x: number;
  y: number;
  radius: number;
  baseAlpha: number;
  twinkleSpeed: number;
  twinklePhase: number;
  hue: "white" | "sky";
  offsetX: number;
  offsetY: number;
};

const INFLUENCE_RADIUS = 150;
const MAX_PUSH = 16;

function createStars(width: number, height: number): Star[] {
  const count = Math.min(260, Math.max(90, Math.floor((width * height) / 8500)));
  return Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    radius: Math.random() * 1.1 + 0.4,
    baseAlpha: Math.random() * 0.5 + 0.35,
    twinkleSpeed: Math.random() * 0.9 + 0.3,
    twinklePhase: Math.random() * Math.PI * 2,
    hue: Math.random() < 0.75 ? "white" : "sky",
    offsetX: 0,
    offsetY: 0
  }));
}

export function StarfieldBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let width = window.innerWidth;
    let height = window.innerHeight;
    let stars = createStars(width, height);
    let mouse: { x: number; y: number } | null = null;
    let rafId = 0;

    function resize() {
      width = window.innerWidth;
      height = window.innerHeight;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas!.width = width * dpr;
      canvas!.height = height * dpr;
      canvas!.style.width = `${width}px`;
      canvas!.style.height = `${height}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      stars = createStars(width, height);
    }

    function onPointerMove(event: PointerEvent) {
      mouse = { x: event.clientX, y: event.clientY };
    }

    function onPointerLeave() {
      mouse = null;
    }

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerleave", onPointerLeave);
    window.addEventListener("blur", onPointerLeave);

    function draw(time: number) {
      ctx!.clearRect(0, 0, width, height);

      for (const star of stars) {
        let targetOffsetX = 0;
        let targetOffsetY = 0;
        let boost = 0;

        if (mouse) {
          const dx = star.x - mouse.x;
          const dy = star.y - mouse.y;
          const distance = Math.hypot(dx, dy);
          if (distance < INFLUENCE_RADIUS && distance > 0.01) {
            const factor = 1 - distance / INFLUENCE_RADIUS;
            targetOffsetX = (dx / distance) * MAX_PUSH * factor;
            targetOffsetY = (dy / distance) * MAX_PUSH * factor;
            boost = factor;
          }
        }

        star.offsetX += (targetOffsetX - star.offsetX) * 0.12;
        star.offsetY += (targetOffsetY - star.offsetY) * 0.12;

        const twinkle = reduceMotion
          ? 0.8
          : 0.55 + 0.45 * Math.sin(time * 0.001 * star.twinkleSpeed + star.twinklePhase);
        const alpha = Math.min(1, star.baseAlpha * twinkle + boost * 0.55);
        const radius = star.radius * (1 + boost * 1.4);
        const color = star.hue === "white" ? "255, 255, 255" : "125, 211, 252";

        if (boost > 0.05) {
          ctx!.shadowBlur = 8 * boost;
          ctx!.shadowColor = `rgba(${color}, ${Math.min(1, alpha)})`;
        } else {
          ctx!.shadowBlur = 0;
        }

        ctx!.beginPath();
        ctx!.arc(star.x + star.offsetX, star.y + star.offsetY, radius, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(${color}, ${alpha})`;
        ctx!.fill();
      }

      rafId = window.requestAnimationFrame(draw);
    }

    rafId = window.requestAnimationFrame(draw);

    return () => {
      window.cancelAnimationFrame(rafId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerleave", onPointerLeave);
      window.removeEventListener("blur", onPointerLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0"
      aria-hidden="true"
    />
  );
}
