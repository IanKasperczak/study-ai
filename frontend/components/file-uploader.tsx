"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { FileUp, FolderOpen, Loader2 } from "lucide-react";
import { uploadStudyFiles } from "@/lib/api";
import type { ProjectResponse } from "@/lib/types";

type FileUploaderProps = {
  onProjectReady: (project: ProjectResponse) => void;
};

export function FileUploader({ onProjectReady }: FileUploaderProps) {
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

    setIsUploading(true);
    setError(null);

    try {
      const project = await uploadStudyFiles(selectedFiles);
      onProjectReady(project);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron procesar los archivos.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <section className="panel rounded-lg p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-white">Project Study IA</h1>
          <p className="mt-1 text-sm text-slate-400">Carga materiales y estudia con contexto.</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm font-medium text-slate-100 transition hover:border-sky-300/50 hover:text-sky-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isUploading ? <Loader2 size={16} className="animate-spin" /> : <FileUp size={16} />}
            Archivos
          </button>
          <button
            type="button"
            onClick={() => folderInputRef.current?.click()}
            disabled={isUploading}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-sky-300 px-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-200 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isUploading ? <Loader2 size={16} className="animate-spin" /> : <FolderOpen size={16} />}
            Carpeta
          </button>
        </div>
      </div>

      {error ? (
        <div className="mt-3 rounded-md border border-red-400/30 bg-red-950/35 px-3 py-2 text-sm text-red-100">
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
    </section>
  );
}

