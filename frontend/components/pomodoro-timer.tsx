"use client";

import { type MutableRefObject, useEffect, useMemo, useRef, useState } from "react";
import { Bell, Pause, Play, RotateCcw, Volume2, VolumeX } from "lucide-react";

const WORK_SECONDS = 25 * 60;
const BREAK_SECONDS = 5 * 60;

export function PomodoroTimer() {
  const [mode, setMode] = useState<"work" | "break">("work");
  const [secondsLeft, setSecondsLeft] = useState(WORK_SECONDS);
  const [isRunning, setIsRunning] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [studiedSeconds, setStudiedSeconds] = useState(0);
  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    const saved = Number(localStorage.getItem("study-ia-pomodoro-seconds") ?? "0");
    setStudiedSeconds(Number.isFinite(saved) ? saved : 0);
  }, []);

  useEffect(() => {
    if (!isRunning) return;

    const intervalId = window.setInterval(() => {
      setSecondsLeft((current) => {
        if (current <= 1) {
          const nextMode = mode === "work" ? "break" : "work";
          if (mode === "work") {
            setStudiedSeconds((value) => {
              const next = value + WORK_SECONDS;
              localStorage.setItem("study-ia-pomodoro-seconds", String(next));
              return next;
            });
          }
          if (soundEnabled) playSoftBeep(audioContextRef);
          setMode(nextMode);
          return nextMode === "work" ? WORK_SECONDS : BREAK_SECONDS;
        }
        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [isRunning, mode, soundEnabled]);

  const formattedTime = useMemo(() => formatTime(secondsLeft), [secondsLeft]);
  const studiedMinutes = Math.floor(studiedSeconds / 60);

  function resetTimer() {
    setIsRunning(false);
    setSecondsLeft(mode === "work" ? WORK_SECONDS : BREAK_SECONDS);
  }

  function toggleMode(nextMode: "work" | "break") {
    setMode(nextMode);
    setIsRunning(false);
    setSecondsLeft(nextMode === "work" ? WORK_SECONDS : BREAK_SECONDS);
  }

  return (
    <div className="fixed bottom-5 right-5 z-30 w-[280px] rounded-lg border border-slate-700/80 bg-slate-950/90 p-4 shadow-glow backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Bell size={17} className="text-emerald-300" />
          <span className="text-sm font-semibold text-white">Pomodoro</span>
        </div>
        <button
          type="button"
          onClick={() => setSoundEnabled((value) => !value)}
          className="grid h-8 w-8 place-items-center rounded-md border border-slate-800 text-slate-300 transition hover:border-slate-600 hover:text-white"
          aria-label={soundEnabled ? "Desactivar sonido" : "Activar sonido"}
        >
          {soundEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
        </button>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => toggleMode("work")}
          className={`h-8 rounded-md text-xs font-medium transition ${
            mode === "work" ? "bg-sky-300 text-slate-950" : "bg-slate-900 text-slate-300"
          }`}
        >
          Foco
        </button>
        <button
          type="button"
          onClick={() => toggleMode("break")}
          className={`h-8 rounded-md text-xs font-medium transition ${
            mode === "break" ? "bg-emerald-300 text-slate-950" : "bg-slate-900 text-slate-300"
          }`}
        >
          Pausa
        </button>
      </div>

      <div className="py-5 text-center">
        <div className="text-4xl font-semibold tabular-nums text-white">{formattedTime}</div>
        <p className="mt-1 text-xs text-slate-400">{studiedMinutes} min estudiados</p>
      </div>

      <div className="grid grid-cols-[1fr_44px] gap-2">
        <button
          type="button"
          onClick={() => setIsRunning((value) => !value)}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-violet-300 text-sm font-semibold text-slate-950 transition hover:bg-violet-200"
        >
          {isRunning ? <Pause size={16} /> : <Play size={16} />}
          {isRunning ? "Pausar" : "Iniciar"}
        </button>
        <button
          type="button"
          onClick={resetTimer}
          className="grid h-10 place-items-center rounded-md border border-slate-700 text-slate-200 transition hover:border-slate-500"
          aria-label="Reiniciar temporizador"
        >
          <RotateCcw size={16} />
        </button>
      </div>
    </div>
  );
}

function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function playSoftBeep(audioContextRef: MutableRefObject<AudioContext | null>) {
  const AudioContextConstructor =
    window.AudioContext ||
    (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextConstructor) return;

  const context = audioContextRef.current ?? new AudioContextConstructor();
  audioContextRef.current = context;

  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = "sine";
  oscillator.frequency.value = 740;
  gain.gain.value = 0.05;
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + 0.16);
}
