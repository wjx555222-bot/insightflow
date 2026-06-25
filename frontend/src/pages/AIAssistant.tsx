import { useState, useRef, useEffect } from "react";
import { Send, Loader2, FileText, TrendingUp, Package, Bot, User } from "lucide-react";
import { aiApi } from "@/api/endpoints";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import type { AIResponse } from "@/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  aiResponse?: AIResponse;
  timestamp: Date;
}

const confidenceColor = (c: string) =>
  c === "high" ? "default" : c === "medium" ? "secondary" : "destructive";

export default function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const addMessage = (role: "user" | "assistant", content: string, aiResponse?: AIResponse) => {
    setMessages((prev) => [...prev, { role, content, aiResponse, timestamp: new Date() }]);
  };

  const sendQuestion = async (question: string) => {
    if (!question.trim() || loading) return;
    addMessage("user", question);
    setInput("");
    setLoading(true);
    try {
      const res = await aiApi.ask(question);
      addMessage("assistant", res.data.short_answer, res.data);
    } catch {
      addMessage("assistant", "Sorry, I encountered an error processing your request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = async (type: string) => {
    if (loading) return;
    setLoading(true);
    try {
      let res: AIResponse;
      if (type === "report") {
        addMessage("user", "Generate a weekly business report");
        const r = await aiApi.generateReport("weekly");
        res = r.data;
      } else if (type === "trend") {
        addMessage("user", "Explain the current revenue trend");
        const r = await aiApi.explainTrend("revenue", "last_month");
        res = r.data;
      } else {
        addMessage("user", "What inventory actions do you suggest?");
        const r = await aiApi.inventorySuggestion();
        res = r.data;
      }
      addMessage("assistant", res.short_answer, res);
    } catch {
      addMessage("assistant", "Sorry, I encountered an error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuestion(input);
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">AI Business Analyst</h2>
        <p className="text-sm text-muted-foreground">Ask questions about your business data and get intelligent insights</p>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={() => handleQuickAction("report")} disabled={loading}>
          <FileText className="mr-1 h-4 w-4" />Weekly Report
        </Button>
        <Button variant="outline" size="sm" onClick={() => handleQuickAction("trend")} disabled={loading}>
          <TrendingUp className="mr-1 h-4 w-4" />Revenue Trend
        </Button>
        <Button variant="outline" size="sm" onClick={() => handleQuickAction("inventory")} disabled={loading}>
          <Package className="mr-1 h-4 w-4" />Inventory Tips
        </Button>
      </div>

      {/* Chat Area */}
      <Card className="flex-1 overflow-hidden">
        <CardContent className="flex h-full flex-col p-0">
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center text-muted-foreground">
                <Bot className="mb-3 h-12 w-12 opacity-30" />
                <p className="text-lg font-medium">How can I help you today?</p>
                <p className="mt-1 max-w-md text-sm">
                  Ask me about revenue trends, customer behavior, product performance, or generate a business report.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "assistant" && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div className={`max-w-[70%] rounded-lg p-3 ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      {msg.aiResponse && (
                        <div className="mt-3 space-y-2 border-t border-border/30 pt-3">
                          {msg.aiResponse.data_evidence.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold opacity-70">Data Evidence</p>
                              <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs">
                                {msg.aiResponse.data_evidence.map((e, j) => <li key={j}>{e}</li>)}
                              </ul>
                            </div>
                          )}
                          {msg.aiResponse.reasoning && (
                            <div>
                              <p className="text-xs font-semibold opacity-70">Reasoning</p>
                              <p className="mt-0.5 text-xs">{msg.aiResponse.reasoning}</p>
                            </div>
                          )}
                          {msg.aiResponse.suggested_actions.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold opacity-70">Suggested Actions</p>
                              <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs">
                                {msg.aiResponse.suggested_actions.map((a, j) => <li key={j}>{a}</li>)}
                              </ul>
                            </div>
                          )}
                          <div className="flex items-center gap-2 pt-1">
                            <span className="text-xs opacity-60">Confidence:</span>
                            <Badge variant={confidenceColor(msg.aiResponse.confidence) as "default" | "secondary" | "destructive"} className="text-[10px]">
                              {msg.aiResponse.confidence}
                            </Badge>
                          </div>
                        </div>
                      )}
                    </div>
                    {msg.role === "user" && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                        <User className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                    <div className="rounded-lg bg-muted p-3">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex gap-2 border-t p-3">
            <Input
              placeholder="Ask a question about your business data..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              className="flex-1"
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
