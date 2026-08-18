"use client";

import { useSyncExternalStore } from "react";

// Local first, hydration-safe store backed by localStorage. Both this tab and
// other tabs can trigger updates; React re-renders through useSyncExternalStore.

type StoreEntry = {
  raw: string | null;
  value: unknown;
};

const entries = new Map<string, StoreEntry>();
const listeners = new Set<() => void>();

function readRaw(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function getEntry(key: string, fallback: unknown): StoreEntry {
  let entry = entries.get(key);
  if (!entry) {
    const raw = readRaw(key);
    entry = { raw, value: parseEntry(raw, fallback) };
    entries.set(key, entry);
  }
  return entry;
}

function parseEntry(raw: string | null, fallback: unknown): unknown {
  if (raw === null) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function refreshEntry(key: string, fallback: unknown) {
  const entry = entries.get(key);
  if (!entry) return;
  const raw = readRaw(key);
  entry.raw = raw;
  entry.value = parseEntry(raw, fallback);
}

function subscribe(callback: () => void): () => void {
  listeners.add(callback);
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(callback);
    window.removeEventListener("storage", onStorage);
  };
}

function onStorage(event: StorageEvent) {
  const key = event.key;
  if (!key) {
    refreshAll();
  } else if (entries.has(key)) {
    const fallback = entries.get(key)!.value;
    refreshEntry(key, fallback);
  }
  notify();
}

function refreshAll() {
  for (const key of entries.keys()) {
    const fallback = entries.get(key)!.value;
    refreshEntry(key, fallback);
  }
}

function notify() {
  for (const listener of listeners) listener();
}

export function readLocalStore<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  return getEntry(key, fallback).value as T;
}

export function writeLocalStore(key: string, value: unknown) {
  let raw: string;
  try {
    raw = JSON.stringify(value);
    window.localStorage.setItem(key, raw);
  } catch {
    return;
  }
  const entry = entries.get(key) ?? (entries.set(key, { raw, value }), entries.get(key)!);
  entry.raw = raw;
  entry.value = value;
  notify();
}

export function removeLocalStore(key: string) {
  try {
    window.localStorage.removeItem(key);
  } catch {
    return;
  }
  const entry = entries.get(key);
  if (entry) {
    entry.raw = null;
    entry.value = undefined;
  }
  notify();
}

export function useLocalStore<T>(key: string, fallback: T): T {
  return useSyncExternalStore(
    subscribe,
    () => readLocalStore<T>(key, fallback),
    () => fallback
  );
}