"use client";

import { FormEvent, useState } from "react";
import { Loader2, SendHorizontal } from "lucide-react";
import { askContextualChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

type ChatPanelProps = {
  projectId: string | null;
  selectedTopicIds: string[];
};

export function ChatPanel({ projectId, selectedTopicIds }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = input.trim();
    if (!message || !projectId) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const response = await askContextualChat(projectId, message, selectedTopicIds);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          sources: response.sources
        }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo enviar la pregunta.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="panel flex min-h-[360px] flex-1 flex-col rounded-lg">
      <div className="border-b border-slate-800/80 p-4">
        <h2 className="text-base font-semibold text-white">Chat contextual</h2>
        <p className="mt-1 text-sm text-slate-400">Respuestas limitadas al material cargado.</p>
      </div>

      <div className="thin-scrollbar min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length ? (
          messages.map((message) => (
            <div
              key={message.id}
              className={`max-w-[86%] rounded-lg border px-4 py-3 text-sm leading-6 ${
                message.role === "user"
                  ? "ml-auto border-sky-300/40 bg-sky-300/10 text-sky-50"
                  : "border-slate-800 bg-slate-950/55 text-slate-200"
              }`}
            >
              <p className="whitespace-pre-line">{message.content}</p>
              {message.sources?.length ? (
                <div className="mt-3 space-y-2 border-t border-slate-800 pt-3 text-xs text-slate-400">
                  {message.sources.map((source) => (
                    <p key={source.id}>
                      <span className="text-slate-300">{source.source}</span>: {source.preview}
                    </p>
                  ))}
                </div>
              ) : null}
            </div>
          ))
        ) : (
          <div className="grid h-full place-items-center text-center text-sm text-slate-500">
            Carga documentos para iniciar una conversacion.
          </div>
        )}
      </div>

      {error ? (
        <div className="mx-4 mb-3 rounded-md border border-red-400/30 bg-red-950/35 px-3 py-2 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="border-t border-slate-800/80 p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={!projectId || isSending}
            placeholder="Pregunta sobre tus documentos"
            className="h-11 min-w-0 flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-sky-300/70 disabled:cursor-not-allowed disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={!projectId || !input.trim() || isSending}
            className="grid h-11 w-11 shrink-0 place-items-center rounded-md bg-emerald-300 text-slate-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Enviar pregunta"
          >
            {isSending ? <Loader2 size={18} className="animate-spin" /> : <SendHorizontal size={18} />}
          </button>
        </div>
      </form>
    </section>
  );
}

