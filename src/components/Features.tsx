import { 
  PhoneCall, 
  Database, 
  BrainCircuit, 
  Zap, 
  Users, 
  CreditCard, 
  ShieldCheck, 
  Headphones,
  Bot,
  FileCode2,
  Workflow,
  Sparkles
} from "lucide-react";

const Features = () => {
  const features = [
    {
      icon: PhoneCall,
      title: "Autonomous Voice Agents",
      badge: "Real-time Voice",
      description: "Human-grade conversational phone agents that answer inquiries, resolve tickets, and take appointments with sub-300ms latency."
    },
    {
      icon: Database,
      title: "Direct PostgreSQL Connector",
      badge: "Zero OpenAPI Needed",
      description: "Connect your PostgreSQL, Supabase, or MySQL database securely. Agents execute safe read-only SQL queries to fetch real-time customer data."
    },
    {
      icon: BrainCircuit,
      title: "Hybrid Vector RAG",
      badge: "ChromaDB + BM25",
      description: "Ingest product catalogs, PDFs, policy docs, and URLs. The agent grounds every answer in your verified company knowledge."
    },
    {
      icon: Zap,
      title: "Zero-Cost Neural Voice Engine",
      badge: "Edge-TTS + Web Speech",
      description: "Free, high-fidelity neural voices out of the box with zero third-party per-character fees, plus optional ElevenLabs voice cloning."
    },
    {
      icon: Bot,
      title: "Multi-Agent Studio",
      badge: "Multi-Role",
      description: "Create distinct agents for different departments: Inbound Sales, Technical Support, Appointment Scheduling, and Billing."
    },
    {
      icon: CreditCard,
      title: "Instant Razorpay Billing",
      badge: "Self-Service",
      description: "Seamless subscription checkout supporting Indian Rupee (₹) and Global (USD) pricing with automated tenant activation."
    },
    {
      icon: Headphones,
      title: "Smart Human Warm-Handoff",
      badge: "SIP Transfer",
      description: "Automatically detects customer frustration and seamlessly escalates calls to your human support team with complete transcript context."
    },
    {
      icon: ShieldCheck,
      title: "Enterprise Tenant Isolation",
      badge: "SOC-2 Ready",
      description: "Strict multi-tenant security with isolated vector namespaces and read-only database transaction limits."
    }
  ];

  return (
    <section className="py-24 bg-muted/20 border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold mb-3">
            <Sparkles className="h-3.5 w-3.5 mr-1.5" />
            Next-Generation Architecture
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
            Everything You Need for <span className="gradient-text">AI-Powered Support</span>
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Replace clunky IVRs and scripted chatbots with autonomous voice agents built for real business operations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div 
                key={index} 
                className="bg-card rounded-2xl p-6 shadow-soft border border-border hover:shadow-medium hover:border-primary/40 transition-all duration-300 flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary group-hover:scale-110 group-hover:bg-primary group-hover:text-white transition-all duration-300">
                      <Icon className="h-6 w-6" />
                    </div>
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">
                      {feature.badge}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold mb-2 text-foreground">{feature.title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;
