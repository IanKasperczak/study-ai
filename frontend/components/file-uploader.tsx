"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { FileUp, FolderOpen, Loader2 } from "lucide-react";
import { uploadStudyFiles } from "@/lib/api";
import type { ProjectResponse } from "@/lib/types";

// Mirrors the backend's MAX_UPLOAD_MB default (see backend/.env.example) so
// oversized selections get rejected instantly instead of after a slow
// upload. The backend re-checks regardless -- this is just a fast, friendly
// client-side guard, not the source of truth.
const MAX_UPLOAD_MB = Number(process.env.NEXT_PUBLIC_MAX_UPLOAD_MB ?? "20");

type FileUploaderProps = {
  onProjectReady: (project: ProjectResponse) => void;
  currentProjectId?: string | null;
};

export function FileUploader({ onProjectReady, currentProjectId }: FileUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const folderInput = folderInputRef.current;
    if (!folderInput) return;

    // Browser-only attributes allow local folder selection without desktop APIs.
    folderInput.setAttribute("webkitdirectory", "");
    folderInput.setAttribute("directory", "");
  }, []);

  async function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(event.target.files ?? []);
    event.target.value = "";

    if (!selectedFiles.length) return;

    const totalMb = selectedFiles.reduce((sum, file) => sum + file.size, 0) / (1024 * 1024);
    if (totalMb > MAX_UPLOAD_MB) {
      setError(
        `Los archivos pesan ${totalMb.toFixed(1)} MB en total, el limite es ${MAX_UPLOAD_MB} MB ` +
          "(un archivo mas chico o varios que sumados no lo superen)."
      );
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // Adds to the currently loaded project when there is one, instead of
      // silently abandoning it in a new, unreferenced project every time.
      const project = await uploadStudyFiles(selectedFiles, currentProjectId ?? undefined);
      onProjectReady(project);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron procesar los archivos.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="border-t border-slate-800/80 p-3">
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-2 text-sm font-medium text-slate-100 transition hover:border-sky-300/50 hover:text-sky-100 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isUploading ? <Loader2 size={16} className="animate-spin" /> : <FileUp size={16} />}
          Archivos
        </button>
        <button
          type="button"
          onClick={() => folderInputRef.current?.click()}
          disabled={isUploading}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-sky-300 px-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-200 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isUploading ? <Loader2 size={16} className="animate-spin" /> : <FolderOpen size={16} />}
          Carpeta
        </button>
      </div>

      {error ? (
        <div className="mt-2 rounded-md border border-red-400/30 bg-red-950/35 px-3 py-2 text-xs text-red-100">
          {error}
        </div>
      ) : null}

      <input
        ref={fileInputRef}
        className="hidden"
        type="file"
        multiple
        accept=".pdf,.docx,.txt,.md"
        onChange={handleFiles}
      />
      <input
        ref={folderInputRef}
        className="hidden"
        type="file"
        multiple
        accept=".pdf,.docx,.txt,.md"
        onChange={handleFiles}
      />
    </div>
  );
}

