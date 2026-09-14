"use client";

import {
  Bell,
  Brain,
  GripHorizontal,
  Maximize2,
  Minimize2,
  Pause,
  Play,
  RotateCcw,
  Volume2,
  VolumeX
} from "lucide-react";
import {
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";
import { readLocalStore, useLocalStore, writeLocalStore } from "@/lib/local-store";

const TECHNIQUES = [
  {
    id: "pomodoro",
    name: "Pomodoro",
    workSeconds: 25 * 60,
    breakSeconds: 5 * 60,
    accent: "bg-sky-300 text-slate-950"
  },
  {
    id: "deep",
    name: "Foco profundo",
    workSeconds: 50 * 60,
    breakSeconds: 10 * 60,
    accent: "bg-violet-300 text-slate-950"
  },
  {
    id: "flow",
    name: "Flow",
    workSeconds: 90 * 60,
    breakSeconds: 20 * 60,
    accent: "bg-cyan-300 text-slate-950"
  },
  {
    id: "sprint",
    name: "Sprint corto",
    workSeconds: 15 * 60,
    breakSeconds: 3 * 60,
    accent: "bg-emerald-300 text-slate-950"
  },
  {
    id: "micro",
    name: "Micro sesion",
    workSeconds: 5 * 60,
    breakSeconds: 1 * 60,
    accent: "bg-amber-300 text-slate-950"
  }
] as const;

type Technique = (typeof TECHNIQUES)[number];

type TimerState = {
  mode: "work" | "break";
  secondsLeft: number;
  isRunning: boolean;
};

type Point = { x: number; y: number };
type Size = { width: number; height: number | null };

const TIMER_KEY = "study-ia-pomodoro-timer";
const TECHNIQUE_KEY = "study-ia-pomodoro-technique";
const POSITION_KEY = "study-ia-pomodoro-position";
const SIZE_KEY = "study-ia-pomodoro-size";
const MINIMIZED_KEY = "study-ia-pomodoro-minimized";
const STATISTICS_KEY = "study-ia-pomodoro-seconds";

const DEFAULT_WIDTH = 290;
const MIN_WIDTH = 220;
const MAX_WIDTH = 480;
const MIN_HEIGHT = 160;
const MAX_HEIGHT = 640;
const VIEWPORT_MARGIN = 12;

const DEFAULT_TIMER: TimerState = {
  mode: "work",
  secondsLeft: TECHNIQUES[0].workSeconds,
  isRunning: false
};

function updateTimer(mutator: (current: TimerState) => TimerState) {
  const current = readLocalStore<TimerState>(TIMER_KEY, DEFAULT_TIMER);
  writeLocalStore(TIMER_KEY, mutator(current));
}

export function PomodoroTimer() {
  const [soundEnabled, setSoundEnabled] = useState(true);
  const audioContextRef = useRef<AudioContext | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  const techniqueId = useLocalStore(TECHNIQUE_KEY, TECHNIQUES[0].id);
  const technique =
    TECHNIQUES.find((item) => item.id === techniqueId) ?? TECHNIQUES[0];

  const timer = useLocalStore<TimerState>(TIMER_KEY, DEFAULT_TIMER);
  const studiedSeconds = useLocalStore(STATISTICS_KEY, 0);
  const position = useLocalStore<Point | null>(POSITION_KEY, null);
  const size = useLocalStore<Size | null>(SIZE_KEY, null);
  const minimized = useLocalStore(MINIMIZED_KEY, false);

  // Never resume a running session automatically after a reload.
  useEffect(() => {
    const current = readLocalStore<TimerState>(TIMER_KEY, DEFAULT_TIMER);
    if (current.isRunning) {
      writeLocalStore(TIMER_KEY, { ...current, isRunning: false });
    }
  }, []);

  // Countdown lives in the shared store so the UI stays in sync everywhere.
  useEffect(() => {
    if (!timer.isRunning) return;

    const intervalId = window.setInterval(() => {
      updateTimer((current) => {
        if (current.secondsLeft > 1) {
          return { ...current, secondsLeft: current.secondsLeft - 1 };
        }

        if (current.mode === "work") {
          writeLocalStore(STATISTICS_KEY, readLocalStore<number>(STATISTICS_KEY, 0) + technique.workSeconds);
        }
        if (soundEnabled) playSoftBeep(audioContextRef);

        const nextMode = current.mode === "work" ? "break" : "work";
        const nextSeconds =
          nextMode === "work" ? technique.workSeconds : technique.breakSeconds;
        return { mode: nextMode, secondsLeft: nextSeconds, isRunning: true };
      });
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [timer.isRunning, technique, soundEnabled]);

  const width = minimized ? 224 : size?.width ?? DEFAULT_WIDTH;
  const height = minimized ? undefined : (size?.height ?? undefined);

  const formattedTime = useMemo(() => formatTime(timer.secondsLeft), [timer.secondsLeft]);
  const studiedMinutes = Math.floor(studiedSeconds / 60);

  function changeTechnique(nextId: string) {
    const next = TECHNIQUES.find((item) => item.id === nextId);
    if (!next) return;
    writeLocalStore(TECHNIQUE_KEY, next.id);
    updateTimer(() => ({
      mode: "work",
      secondsLeft: next.workSeconds,
      isRunning: false
    }));
  }

  function toggleRunning() {
    updateTimer((current) => ({ ...current, isRunning: !current.isRunning }));
  }

  function resetTimer() {
    updateTimer(() => ({
      mode: "work",
      secondsLeft: technique.workSeconds,
      isRunning: false
    }));
  }

  function toggleMode(nextMode: "work" | "break") {
    const nextSeconds = nextMode === "work" ? technique.workSeconds : technique.breakSeconds;
    updateTimer(() => ({ mode: nextMode, secondsLeft: nextSeconds, isRunning: false }));
  }

  function toggleMinimized() {
    writeLocalStore(MINIMIZED_KEY, !minimized);
  }

  function onDragStart(event: ReactPointerEvent) {
    if ((event.target as HTMLElement).closest("button,select")) return;
    if (event.button !== 0) return;

    const panel = panelRef.current;
    if (!panel) return;
    const rect = panel.getBoundingClientRect();
    const startPointerX = event.clientX;
    const startPointerY = event.clientY;
    const startLeft = rect.left;
    const startTop = rect.top;

    function move(pointerEvent: globalThis.PointerEvent) {
      let nextX = startLeft + (pointerEvent.clientX - startPointerX);
      let nextY = startTop + (pointerEvent.clientY - startPointerY);
      nextX = clamp(nextX, 0, Math.max(0, window.innerWidth - rect.width - VIEWPORT_MARGIN));
      nextY = clamp(nextY, 0, Math.max(0, window.innerHeight - rect.height - VIEWPORT_MARGIN));
      writeLocalStore(POSITION_KEY, { x: Math.round(nextX), y: Math.round(nextY) });
    }

    function up() {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    }

    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  function onResizeStart(event: ReactPointerEvent) {
    if (event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();

    const panel = panelRef.current;
    if (!panel) return;
    const rect = panel.getBoundingClientRect();
    const startPointerX = event.clientX;
    const startPointerY = event.clientY;
    const startWidth = size?.width ?? rect.width;
    const startHeight = size?.height ?? rect.height;

    function move(pointerEvent: globalThis.PointerEvent) {
      const nextWidth = clamp(
        startWidth + (pointerEvent.clientX - startPointerX),
        MIN_WIDTH,
        MAX_WIDTH
      );
      const nextHeight = clamp(
        startHeight + (pointerEvent.clientY - startPointerY),
        MIN_HEIGHT,
        MAX_HEIGHT
      );
      writeLocalStore(SIZE_KEY, { width: Math.round(nextWidth), height: Math.round(nextHeight) });
    }

    function up() {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    }

    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  const panelStyle: CSSProperties = {
    width,
    height,
    position: "fixed"
  };
  if (position) {
    panelStyle.left = position.x;
    panelStyle.top = position.y;
  } else {
    panelStyle.right = VIEWPORT_MARGIN;
    panelStyle.bottom = VIEWPORT_MARGIN;
  }

  if (minimized) {
    return (
      <div
        ref={panelRef}
        onPointerDown={onDragStart}
        style={panelStyle}
        className="z-30 cursor-move touch-none select-none rounded-lg border border-slate-700/80 bg-slate-950/90 px-3 py-2 shadow-glow backdrop-blur"
      >
        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={toggleMinimized}
            className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-slate-800 text-slate-300 transition hover:border-sky-300/60 hover:text-white"
            aria-label="Expandir temporizador"
          >
            <Maximize2 size={15} />
          </button>
          <div className="flex min-w-0 flex-1 items-center justify-center gap-2">
            <Brain size={15} className="shrink-0 text-violet-300" />
            <span className="tabular-nums text-sm font-semibold text-white">
              {formattedTime}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setSoundEnabled((value) => !value)}
            className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-slate-800 text-slate-300 transition hover:border-slate-600 hover:text-white"
            aria-label={soundEnabled ? "Desactivar sonido" : "Activar sonido"}
          >
            {soundEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={panelRef}
      onPointerDown={onDragStart}
      style={panelStyle}
      className="z-30 flex touch-none select-none flex-col overflow-hidden rounded-lg border border-slate-700/80 bg-slate-950/90 p-4 shadow-glow backdrop-blur"
    >
      <div className="flex shrink-0 cursor-move items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <GripHorizontal size={16} className="shrink-0 text-slate-500" />
          <Bell size={16} className="shrink-0 text-emerald-300" />
          <span className="truncate text-sm font-semibold text-white">Temporizador</span>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={() => setSoundEnabled((value) => !value)}
            className="grid h-8 w-8 place-items-center rounded-md border border-slate-800 text-slate-300 transition hover:border-slate-600 hover:text-white"
            aria-label={soundEnabled ? "Desactivar sonido" : "Activar sonido"}
          >
            {soundEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
          </button>
          <button
            type="button"
            onClick={toggleMinimized}
            className="grid h-8 w-8 place-items-center rounded-md border border-slate-800 text-slate-300 transition hover:border-slate-600 hover:text-white"
            aria-label="Minimizar temporizador"
          >
            <Minimize2 size={15} />
          </button>
        </div>
      </div>

      <div className="thin-scrollbar min-h-0 flex-1 touch-auto overflow-y-auto pr-1">
        <label className="mt-3 block">
          <span className="text-xs uppercase tracking-[0.14em] text-slate-500">
            Tecnica
          </span>
          <select
            value={technique.id}
            onChange={(event) => changeTechnique(event.target.value)}
            className="mt-1 h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-2 text-sm text-slate-100 outline-none transition focus:border-sky-300/70"
          >
            {TECHNIQUES.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name} ({formatTime(item.workSeconds)} / {formatTime(item.breakSeconds)})
              </option>
            ))}
          </select>
        </label>

        <div className="mt-3 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => toggleMode("work")}
            className={`h-8 rounded-md text-xs font-medium transition ${
              timer.mode === "work"
                ? "bg-sky-300 text-slate-950"
                : "bg-slate-900 text-slate-300"
            }`}
          >
            Foco
          </button>
          <button
            type="button"
            onClick={() => toggleMode("break")}
            className={`h-8 rounded-md text-xs font-medium transition ${
              timer.mode === "break"
                ? "bg-emerald-300 text-slate-950"
                : "bg-slate-900 text-slate-300"
            }`}
          >
            Pausa
          </button>
        </div>

        <div className="py-5 text-center">
          <div className="text-4xl font-semibold tabular-nums text-white">{formattedTime}</div>
          <p className="mt-1 text-xs text-slate-400">
            {timer.mode === "work" ? "Foco" : "Descanso"} · {studiedMinutes} min estudiados
          </p>
        </div>

        <div className="grid grid-cols-[1fr_44px] gap-2">
          <button
            type="button"
            onClick={toggleRunning}
            className={`inline-flex h-10 items-center justify-center gap-2 rounded-md text-sm font-semibold transition ${technique.accent}`}
          >
            {timer.isRunning ? <Pause size={16} /> : <Play size={16} />}
            {timer.isRunning ? "Pausar" : "Iniciar"}
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

      <div
        onPointerDown={onResizeStart}
        className="absolute bottom-1 right-1 h-4 w-4 cursor-nwse-resize touch-none select-none rounded-sm border-b-2 border-r-2 border-slate-500 opacity-60 transition hover:opacity-100"
        role="separator"
        aria-orientation="horizontal"
        aria-label="Redimensionar temporizador"
      />
    </div>
  );
}

function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function playSoftBeep(audioContextRef: { current: AudioContext | null }) {
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