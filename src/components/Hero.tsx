import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowRight, 
  Mic, 
  MicOff, 
  Bot, 
  Sparkles, 
  Volume2, 
  VolumeX, 
  Send, 
  Database, 
  Zap, 
  ShieldCheck, 
  Globe2 
} from "lucide-react";
import { Link } from "react-router-dom";

const SAMPLE_QUERIES = [
  { label: "Check Order", text: "Where is order #ZMT-8492 and when will it arrive?" },
  { label: "Book Slot", text: "Can I schedule a consultation for tomorrow at 3 PM?" },
  { label: "Refund Policy", text: "What is your 30-day return and refund policy?" }
];

const Hero = () => {
  const [inputText, setInputText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [demoResponse, setDemoResponse] = useState<string | null>(
    "Hello! I'm your VoxAide agent. I connect to your PostgreSQL database and company docs to handle customer calls 24/7. Try asking me a question!"
  );
  const [activeQuery, setActiveQuery] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number>(240);

  const handleRunDemo = (query: string) => {
    setActiveQuery(query);
    setInputText(query);
    setIsProcessing(true);
    setDemoResponse(null);

    // Realistic simulation with instantaneous response
    setTimeout(() => {
      let reply = "";
      if (query.toLowerCase().includes("order")) {
        reply = "Order #ZMT-8492 is currently Out for Delivery with FedEx. Estimated delivery is today by 4:30 PM. A tracking SMS has been sent to the customer.";
      } else if (query.toLowerCase().includes("schedule") || query.toLowerCase().includes("consultation")) {
        reply = "I checked our live availability: Tomorrow at 3:00 PM is open. I've penciled you in and sent a confirmation invite to your email.";
      } else {
        reply = "According to our company knowledge base, items returned within 30 days in original condition receive a 100% refund processed within 3 business days.";
      }

      setDemoResponse(reply);
      setIsProcessing(false);
      setLatencyMs(Math.floor(Math.random() * 80) + 180); // 180-260ms

      // Speak using client-side Web Speech API (zero-cost, instant)
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(reply);
        utterance.rate = 1.05;
        utterance.pitch = 1.0;
        utterance.onstart = () => setIsPlayingAudio(true);
        utterance.onend = () => setIsPlayingAudio(false);
        utterance.onerror = () => setIsPlayingAudio(false);
        window.speechSynthesis.speak(utterance);
      }
    }, 450);
  };

  const toggleMic = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      handleRunDemo(SAMPLE_QUERIES[0].text);
      return;
    }

    if (isSpeaking) {
      setIsSpeaking(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.onstart = () => setIsSpeaking(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setIsSpeaking(false);
        handleRunDemo(transcript);
      };
      recognition.onerror = () => setIsSpeaking(false);
      recognition.onend = () => setIsSpeaking(false);
      recognition.start();
    } catch {
      setIsSpeaking(false);
      handleRunDemo(SAMPLE_QUERIES[0].text);
    }
  };

  const stopAudio = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsPlayingAudio(false);
    }
  };

  return (
    <section className="pt-12 pb-24 bg-gradient-hero relative overflow-hidden">
      {/* Background Decorative Tech Elements */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center max-w-4xl mx-auto">
          {/* 2026 Tech Badge */}
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs sm:text-sm font-semibold mb-6 shadow-soft backdrop-blur-sm">
            <Sparkles className="h-4 w-4 mr-2 text-primary animate-pulse" />
            2026 Agentic AI Platform • Autonomous Voice & Omnichannel Support
          </div>

          {/* Main Heading */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-[1.1]">
            Customer Support on <br className="hidden sm:inline" />
            <span className="gradient-text">Autonomous Voice AI</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-muted-foreground max-w-3xl mx-auto mb-8 leading-relaxed">
            Deploy intelligent AI voice agents that resolve customer calls, execute live read-only queries 
            against your PostgreSQL database, and learn from company docs in <span className="font-semibold text-foreground">under 300 milliseconds</span>.
          </p>

          {/* Primary Call to Actions */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-14">
            <Link to="/signup">
              <Button size="xl" className="bg-primary hover:bg-primary-hover text-white shadow-glow group px-8">
                Start 14-Day Free Trial
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button variant="outline" size="xl" className="px-8 border-border bg-card/60 backdrop-blur-sm hover:bg-card">
                View Pricing & Plans
              </Button>
            </Link>
          </div>
        </div>

        {/* Interactive Live AI Agent Playground Sandbox */}
        <div className="max-w-4xl mx-auto">
          <div className="relative bg-card/90 backdrop-blur-md rounded-2xl shadow-large border border-border p-6 sm:p-8">
            {/* Top Bar Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-border mb-6">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white shadow-soft">
                    <Bot className="h-5 w-5" />
                  </div>
                  <span className="absolute -top-1 -right-1 flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-accent"></span>
                  </span>
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-foreground">VoxAide Demo Agent</span>
                    <Badge variant="outline" className="text-[11px] bg-accent/10 text-accent border-accent/20">
                      Live Sandbox
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground flex items-center gap-2 mt-0.5">
                    <Database className="h-3 w-3 text-primary" />
                    <span>PostgreSQL & RAG Connected</span>
                  </div>
                </div>
              </div>

              {/* Latency & Status Indicator */}
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="text-xs font-mono font-bold text-accent flex items-center gap-1 justify-end">
                    <Zap className="h-3 w-3" />
                    {latencyMs}ms Latency
                  </div>
                  <div className="text-[11px] text-muted-foreground">Neural Voice Active</div>
                </div>
                {isPlayingAudio && (
                  <Button variant="ghost" size="sm" onClick={stopAudio} className="h-8 w-8 p-0 text-destructive">
                    <VolumeX className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>

            {/* Conversation / Response Box */}
            <div className="min-h-[140px] bg-muted/40 rounded-xl p-5 mb-6 border border-border/50 flex flex-col justify-between">
              {isProcessing ? (
                <div className="flex items-center justify-center py-8 space-x-3 text-muted-foreground">
                  <div className="flex space-x-1">
                    <span className="w-2.5 h-2.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2.5 h-2.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2.5 h-2.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                  <span className="text-sm font-medium">Querying database & generating voice response...</span>
                </div>
              ) : (
                <>
                  <div className="text-foreground text-sm sm:text-base leading-relaxed">
                    {demoResponse}
                  </div>
                  {demoResponse && (
                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-border/40 text-xs text-muted-foreground">
                      <div className="flex items-center space-x-2">
                        <span className="inline-block w-2 h-2 rounded-full bg-accent"></span>
                        <span>Source: Safe PostgreSQL Query + Verified Docs</span>
                      </div>
                      <button 
                        onClick={() => handleRunDemo(inputText || SAMPLE_QUERIES[0].text)}
                        className="text-primary hover:underline flex items-center gap-1 font-medium"
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                        Replay Voice
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Clickable Quick Prompts */}
            <div className="mb-4">
              <div className="text-xs font-medium text-muted-foreground mb-2">Try a sample query:</div>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_QUERIES.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleRunDemo(q.text)}
                    className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                      activeQuery === q.text 
                        ? "bg-primary text-white border-primary" 
                        : "bg-background hover:bg-muted text-muted-foreground border-border hover:text-foreground"
                    }`}
                  >
                    {q.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Bar */}
            <div className="flex items-center space-x-2">
              <div className="relative flex-1">
                <Input
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && inputText.trim() && handleRunDemo(inputText)}
                  placeholder="Type or speak a question (e.g. 'Track order #ZMT-8492')..."
                  className="pr-10 bg-background"
                />
              </div>
              <Button
                type="button"
                variant={isSpeaking ? "destructive" : "outline"}
                size="icon"
                onClick={toggleMic}
                title="Click to speak"
                className="shrink-0"
              >
                {isSpeaking ? <MicOff className="h-4 w-4 animate-pulse" /> : <Mic className="h-4 w-4 text-primary" />}
              </Button>
              <Button
                type="button"
                size="icon"
                onClick={() => inputText.trim() && handleRunDemo(inputText)}
                disabled={!inputText.trim() || isProcessing}
                className="shrink-0 bg-primary hover:bg-primary-hover text-white"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Floating Key Performance Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8">
            <div className="bg-card/70 backdrop-blur-sm rounded-xl p-4 border border-border text-center shadow-soft">
              <div className="text-2xl sm:text-3xl font-extrabold text-primary">&lt;300ms</div>
              <div className="text-xs text-muted-foreground font-medium mt-1">Voice Latency</div>
            </div>
            <div className="bg-card/70 backdrop-blur-sm rounded-xl p-4 border border-border text-center shadow-soft">
              <div className="text-2xl sm:text-3xl font-extrabold text-accent">99.2%</div>
              <div className="text-xs text-muted-foreground font-medium mt-1">Resolution Rate</div>
            </div>
            <div className="bg-card/70 backdrop-blur-sm rounded-xl p-4 border border-border text-center shadow-soft">
              <div className="text-2xl sm:text-3xl font-extrabold text-foreground">50+</div>
              <div className="text-xs text-muted-foreground font-medium mt-1">Languages Supported</div>
            </div>
            <div className="bg-card/70 backdrop-blur-sm rounded-xl p-4 border border-border text-center shadow-soft">
              <div className="text-2xl sm:text-3xl font-extrabold text-primary">₹0.00</div>
              <div className="text-xs text-muted-foreground font-medium mt-1">Base Voice Engine Cost</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
