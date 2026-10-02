import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';

interface MessageProps {
  content: string;
  role: 'user' | 'assistant' | 'system' | 'tool'; // ← Adicionado 'tool' aqui
}

export function ChatMessage({ content, role }: MessageProps) {
  if (!content || content.trim() === ''){
    return null;
  }

  const getRoleStyles = () => {
    switch (role) {
      case 'user':
        return 'bg-blue-600 text-white self-end ml-auto';
      case 'system':
        return 'bg-red-950/40 border border-red-900/50 text-red-300 self-center mx-auto text-sm text-center';
      case 'tool': 
        return 'bg-zinc-800/50 text-zinc-400 self-start mr-auto text-xs font-mono'; 
      case 'assistant':
      default:
        return 'bg-zinc-800 text-zinc-100 self-start mr-auto';
    }
  };

  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : role === 'system' ? 'justify-center' : 'justify-start'}`}>
      <div className={`p-4 text-left rounded-lg my-2 max-w-[85%] ${getRoleStyles()}`}>
        <div className="prose dark:prose-invert max-w-none">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeSanitize]}
            components={{
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto my-3">
                  <table className="min-w-full border-collapse border border-zinc-700 text-sm" {...props} />
                </div>
              ),
              th: ({ node, ...props }) => (
                <th className="border border-zinc-700 bg-zinc-900 px-3 py-2 text-left font-bold" {...props} />
              ),
              td: ({ node, ...props }) => (
                <td className="border border-zinc-700 px-3 py-2" {...props} />
              ),
              ul: ({ node, ...props }) => (
                <ul className="list-disc list-inside my-2 space-y-1" {...props} />
              ),
              p: ({ node, ...props }) => (
                <p className="mb-2 last:mb-0 leading-relaxed" {...props} />
              )
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}