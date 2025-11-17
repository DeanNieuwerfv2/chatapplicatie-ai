import { useState } from "react";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
        const res = await fetch("https://8faiqqacrm.eu-west-1.awsapprunner.com/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        console.error("Backend error status:", res.status, "body:", text);
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const data = await res.json();

      // conversation_id van backend opslaan (eerste keer dat je 'm krijgt)
      if (data.conversation_id && conversationId !== data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      const aiMessage = { role: "assistant", content: data.reply };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error("Frontend caught error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: "Er ging iets mis bij het verbinden met de server.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="w-full max-w-3xl h-[80vh] bg-slate-950/80 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-slate-950 font-bold">
              AI
            </div>
            <div>
              <h1 className="text-sm font-semibold text-slate-50">
                Chat met jouw AI
              </h1>
              <p className="text-xs text-slate-400">
                Stuur een bericht om te beginnen
              </p>
            </div>
          </div>
          {loading && (
            <div className="text-xs text-emerald-400 animate-pulse">
              AI is aan het typen...
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-gradient-to-b from-slate-950 to-slate-900">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center">
              <p className="text-slate-500 text-sm text-center max-w-sm">
                👋 Hoi! Ik ben je AI-assistent. Stel een vraag of typ iets in
                het veld hieronder om een gesprek te starten.
              </p>
            </div>
          )}

          {messages.map((m, i) => {
            const isUser = m.role === "user";
            const isSystem = m.role === "system";

            return (
              <div
                key={i}
                className={`flex ${isUser ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`
                    max-w-[80%] px-3 py-2 rounded-2xl text-sm
                    ${
                      isSystem
                        ? "bg-amber-500/10 text-amber-200 border border-amber-500/40"
                        : isUser
                        ? "bg-emerald-500 text-slate-950 rounded-br-sm"
                        : "bg-slate-800 text-slate-50 rounded-bl-sm border border-slate-700/60"
                    }
                  `}
                >
                  {!isUser && !isSystem && (
                    <div className="text-[10px] uppercase tracking-wide text-emerald-400 mb-1">
                      AI
                    </div>
                  )}
                  {isUser && (
                    <div className="text-[10px] uppercase tracking-wide text-emerald-950/80 mb-1">
                      Jij
                    </div>
                  )}
                  {isSystem && (
                    <div className="text-[10px] uppercase tracking-wide text-amber-400 mb-1">
                      Systeem
                    </div>
                  )}
                  <div className="whitespace-pre-wrap">{m.content}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Input */}
        <div className="border-t border-slate-800 bg-slate-950/90 px-4 py-3">
          <div className="flex items-end gap-2">
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Stel een vraag aan de AI..."
              className="flex-1 resize-none rounded-xl bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/70 focus:border-transparent"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium bg-emerald-500 text-slate-950 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-emerald-400 transition-colors"
            >
              {loading ? "..." : "Verstuur"}
            </button>
          </div>
          <p className="mt-1 text-[10px] text-slate-500">
            Druk op <span className="font-semibold">Enter</span> om te
            versturen, <span className="font-semibold">Shift+Enter</span> voor
            een nieuwe regel.
          </p>
          {conversationId && (
            <p className="mt-1 text-[10px] text-slate-600">
              Conversatie ID:{" "}
              <span className="font-mono text-[9px]">
                {conversationId}
              </span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
