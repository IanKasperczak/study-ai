"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
  content: string;
  className?: string;
};

// Renders AI-generated text as actual formatted markdown (headings, bold,
// lists, etc.) instead of showing the raw "#"/"**" characters -- the app's
// dark theme has no typography plugin, so every element is styled by hand
// to match the existing panels instead of relying on prose defaults.
export function MarkdownContent({ content, className }: MarkdownContentProps) {
  return (
    <div className={`markdown-content ${className ?? ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ ...props }) => (
            <h1 className="mb-2 mt-4 text-base font-semibold text-white first:mt-0" {...props} />
          ),
          h2: ({ ...props }) => (
            <h2 className="mb-2 mt-4 text-sm font-semibold text-white first:mt-0" {...props} />
          ),
          h3: ({ ...props }) => (
            <h3
              className="mb-1.5 mt-3 text-xs font-semibold uppercase tracking-wide text-sky-200 first:mt-0"
              {...props}
            />
          ),
          p: ({ ...props }) => <p className="mb-2.5 leading-[inherit] last:mb-0" {...props} />,
          strong: ({ ...props }) => <strong className="font-semibold text-white" {...props} />,
          em: ({ ...props }) => <em className="italic" {...props} />,
          ul: ({ ...props }) => <ul className="mb-2.5 ml-5 list-disc space-y-1 last:mb-0" {...props} />,
          ol: ({ ...props }) => (
            <ol className="mb-2.5 ml-5 list-decimal space-y-1 last:mb-0" {...props} />
          ),
          li: ({ ...props }) => <li className="leading-[inherit]" {...props} />,
          a: ({ ...props }) => (
            <a
              className="text-sky-300 underline underline-offset-2 hover:text-sky-200"
              target="_blank"
              rel="noreferrer"
              {...props}
            />
          ),
          blockquote: ({ ...props }) => (
            <blockquote
              className="mb-2.5 border-l-2 border-sky-300/40 pl-3 italic text-slate-300 last:mb-0"
              {...props}
            />
          ),
          pre: ({ ...props }) => (
            <pre
              className="mb-2.5 overflow-x-auto rounded-md bg-slate-950/70 p-3 text-xs text-slate-200 last:mb-0"
              {...props}
            />
          ),
          code: ({ ...props }) => (
            <code className="rounded bg-slate-800 px-1.5 py-0.5 text-[0.85em] text-sky-200" {...props} />
          ),
          hr: ({ ...props }) => <hr className="my-3 border-slate-800" {...props} />
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
