import { Database, Bot, CreditCard, PhoneCall, Sparkles } from "lucide-react";

const HowItWorks = () => {
  const steps = [
    {
      icon: Database,
      title: "1. Connect Knowledge & Database",
      description: "Upload PDFs, policies, and FAQs, or connect your PostgreSQL/Supabase database with safe, read-only permissions in one click.",
      color: "text-blue-500",
      bg: "bg-blue-500/10"
    },
    {
      icon: Bot,
      title: "2. Configure Voice & Persona",
      description: "Customize your agent's tone, instructions, and choose natural neural voices (Edge-TTS, gTTS, or custom ElevenLabs voice cloning).",
      color: "text-purple-500",
      bg: "bg-purple-500/10"
    },
    {
      icon: CreditCard,
      title: "3. Subscribe with Razorpay",
      description: "Choose a plan that fits your call volume. Activate your workspace instantly with self-service checkout in INR (₹) or USD ($).",
      color: "text-emerald-500",
      bg: "bg-emerald-500/10"
    },
    {
      icon: PhoneCall,
      title: "4. Go Live on Phone & Web",
      description: "Assign an inbound Twilio phone number or embed our one-line voice/chat widget on your website to automate 80%+ of calls.",
      color: "text-amber-500",
      bg: "bg-amber-500/10"
    }
  ];

  return (
    <section className="py-24 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold mb-3">
            <Sparkles className="h-3.5 w-3.5 mr-1.5" />
            Simple 4-Step Onboarding
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
            How <span className="gradient-text">VoxAide</span> Powers Your Support
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            From zero to an active, voice-enabled customer service agent in under 5 minutes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="relative">
                {/* Step Card */}
                <div className="relative bg-card rounded-2xl p-6 shadow-soft border border-border hover:shadow-medium hover:border-primary/40 transition-all duration-300 h-full flex flex-col justify-between">
                  <div>
                    {/* Icon */}
                    <div className="mb-5">
                      <div className={`w-14 h-14 ${step.bg} rounded-xl flex items-center justify-center shadow-soft`}>
                        <Icon className={`h-7 w-7 ${step.color}`} />
                      </div>
                    </div>

                    {/* Content */}
                    <h3 className="text-lg font-bold mb-2.5 text-foreground">{step.title}</h3>
                    <p className="text-muted-foreground text-sm leading-relaxed">{step.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* 2026 Core Tech Stack Architecture Banner */}
        <div className="mt-16 bg-gradient-card rounded-2xl p-8 border border-border shadow-soft">
          <div className="text-center mb-8">
            <h3 className="text-xl sm:text-2xl font-bold mb-2 text-foreground">Next-Gen Agentic Architecture</h3>
            <p className="text-muted-foreground text-sm">State-of-the-art AI infrastructure designed for sub-300ms real-time audio interaction</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div className="p-4 rounded-xl bg-background/60 border border-border/60">
              <div className="text-xl font-bold text-primary mb-1">ChromaDB RAG</div>
              <div className="text-xs text-muted-foreground">Multi-Tenant Vector Store</div>
            </div>
            <div className="p-4 rounded-xl bg-background/60 border border-border/60">
              <div className="text-xl font-bold text-accent mb-1">PostgreSQL Pool</div>
              <div className="text-xs text-muted-foreground">Safe Read-Only Connectors</div>
            </div>
            <div className="p-4 rounded-xl bg-background/60 border border-border/60">
              <div className="text-xl font-bold text-foreground mb-1">Edge-TTS & Neural</div>
              <div className="text-xs text-muted-foreground">Zero-Cost Voice Synthesis</div>
            </div>
            <div className="p-4 rounded-xl bg-background/60 border border-border/60">
              <div className="text-xl font-bold text-primary mb-1">Twilio Streams</div>
              <div className="text-xs text-muted-foreground">WebSocket Phone Telephony</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
