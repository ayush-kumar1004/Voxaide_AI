import { useState } from "react";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, Star, Zap, Shield, HelpCircle, ArrowRight, Database, PhoneCall, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { initiateRazorpayCheckout } from "@/services/razorpay";
import { useToast } from "@/hooks/use-toast";

const Pricing = () => {
  const [currency, setCurrency] = useState<"INR" | "USD">("INR");
  const [isProcessing, setIsProcessing] = useState<string | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();

  const plans = [
    {
      id: "starter",
      name: "Starter",
      inrPrice: 2499,
      usdPrice: 29,
      description: "Best for startups automating their primary customer FAQ & web chat.",
      features: [
        "1 Autonomous AI Voice Agent",
        "500 Included Voice & Chat Minutes/mo",
        "Free Neural Voice Engine (Edge-TTS)",
        "10 Knowledge Base Documents (PDF/Docs)",
        "Embeddable Web Chat & Voice Widget",
        "Community & Email Support"
      ],
      popular: false,
      cta: "Subscribe Starter"
    },
    {
      id: "growth",
      name: "Growth",
      inrPrice: 7999,
      usdPrice: 99,
      description: "Ideal for growing businesses needing real-time database queries & telephony.",
      features: [
        "5 Multi-Department AI Agents",
        "2,500 Included Voice Minutes/mo",
        "Direct PostgreSQL & Supabase Connector",
        "Twilio Inbound/Outbound Phone Number",
        "Full Hybrid Vector RAG with Unlimited Docs",
        "Smart Human Warm-Transfer",
        "Live Call Transcripts & Analytics",
        "Priority Support & 99.9% SLA"
      ],
      popular: true,
      cta: "Subscribe Growth"
    },
    {
      id: "enterprise",
      name: "Enterprise",
      inrPrice: 24999,
      usdPrice: 299,
      description: "For high-volume operations requiring custom voice cloning & dedicated pools.",
      features: [
        "Unlimited Autonomous AI Agents",
        "10,000 Included Voice Minutes/mo",
        "Custom Voice Cloning (ElevenLabs / PlayHT)",
        "Multiple PostgreSQL Database Connectors",
        "Custom CRM & Webhook Automation",
        "Dedicated Account Manager",
        "Custom SLA & HIPAA/SOC-2 Compliance",
        "On-Premise / Private Cloud Deployment"
      ],
      popular: false,
      cta: "Subscribe Enterprise"
    }
  ];

  const handleSubscribe = async (plan: typeof plans[0]) => {
    setIsProcessing(plan.id);

    // Retrieve user if logged in
    let userEmail = "client@company.com";
    let userName = "Enterprise Client";
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const u = JSON.parse(userStr);
        if (u.email) userEmail = u.email;
        if (u.firstName) userName = `${u.firstName} ${u.lastName || ""}`.trim();
      } catch (e) {}
    }

    const price = currency === "INR" ? plan.inrPrice : plan.usdPrice;

    toast({
      title: "Opening Razorpay Checkout",
      description: `Initiating payment for ${plan.name} Plan (${currency === "INR" ? "₹" : "$"}${price.toLocaleString()})...`
    });

    await initiateRazorpayCheckout({
      planId: plan.id,
      planName: plan.name,
      amount: price,
      currency: currency,
      customerEmail: userEmail,
      customerName: userName,
      onSuccess: (result) => {
        setIsProcessing(null);
        toast({
          title: "Payment Successful!",
          description: `Welcome to the ${plan.name} plan! Payment ID: ${result.paymentId}. Redirecting to your Dashboard...`
        });
        setTimeout(() => {
          navigate("/dashboard");
        }, 1200);
      },
      onFailure: (err) => {
        setIsProcessing(null);
        toast({
          title: "Payment Cancelled",
          description: "Payment was not completed. You can try again anytime.",
          variant: "destructive"
        });
      }
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="pt-16 pb-24">
        {/* Header Section */}
        <section className="py-20 bg-gradient-hero">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold mb-4">
              <Sparkles className="h-3.5 w-3.5 mr-1.5" />
              Transparent, Value-Based Pricing
            </div>
            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-6">
              Predictable Plans for <span className="gradient-text">Autonomous Voice Support</span>
            </h1>
            <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
              No hidden telephony markups. High-fidelity neural voice included for zero extra cost.
            </p>

            {/* Currency Selector Switch */}
            <div className="inline-flex items-center p-1.5 bg-card rounded-full border border-border shadow-soft">
              <button
                onClick={() => setCurrency("INR")}
                className={`px-5 py-2 rounded-full text-sm font-semibold transition-all ${
                  currency === "INR"
                    ? "bg-primary text-white shadow-soft"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                INR (₹ India)
              </button>
              <button
                onClick={() => setCurrency("USD")}
                className={`px-5 py-2 rounded-full text-sm font-semibold transition-all ${
                  currency === "USD"
                    ? "bg-primary text-white shadow-soft"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                USD ($ Global)
              </button>
            </div>
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-10">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan) => {
              const price = currency === "INR" ? plan.inrPrice : plan.usdPrice;
              const symbol = currency === "INR" ? "₹" : "$";

              return (
                <Card 
                  key={plan.id} 
                  className={`relative p-8 rounded-2xl flex flex-col justify-between ${
                    plan.popular 
                      ? "ring-2 ring-primary shadow-glow bg-card" 
                      : "shadow-soft bg-card/90 border-border"
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <div className="bg-primary text-white px-4 py-1 rounded-full text-xs font-bold flex items-center shadow-soft">
                        <Star className="h-3.5 w-3.5 mr-1 fill-white" />
                        Most Popular
                      </div>
                    </div>
                  )}

                  <div>
                    <div className="mb-6">
                      <h3 className="text-2xl font-bold mb-2 text-foreground">{plan.name}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">{plan.description}</p>
                    </div>

                    {/* Price Tag */}
                    <div className="mb-6 pb-6 border-b border-border">
                      <div className="flex items-baseline">
                        <span className="text-4xl sm:text-5xl font-extrabold text-foreground font-mono">
                          {symbol}{price.toLocaleString()}
                        </span>
                        <span className="text-muted-foreground ml-2 text-sm">/ month</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Billed monthly via Razorpay • Cancel anytime
                      </div>
                    </div>

                    {/* Features List */}
                    <ul className="space-y-3.5 mb-8">
                      {plan.features.map((feature, fIndex) => (
                        <li key={fIndex} className="flex items-start text-sm text-foreground">
                          <Check className="h-4 w-4 text-accent mr-3 mt-0.5 shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <Button 
                      onClick={() => handleSubscribe(plan)}
                      disabled={isProcessing === plan.id}
                      className={`w-full py-6 font-bold text-sm rounded-xl shadow-soft ${
                        plan.popular
                          ? "bg-primary hover:bg-primary-hover text-white shadow-glow"
                          : "bg-foreground text-background hover:bg-foreground/90"
                      }`}
                    >
                      {isProcessing === plan.id ? "Opening Razorpay..." : plan.cta}
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        </section>

        {/* FAQ Section */}
        <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mt-24">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3 text-foreground">Frequently Asked Questions</h2>
            <p className="text-muted-foreground">Everything you need to know about billing, voice engines, and database safety.</p>
          </div>

          <div className="space-y-6">
            <div className="bg-card rounded-xl p-6 border border-border shadow-soft">
              <h3 className="font-bold text-foreground mb-2 flex items-center">
                <HelpCircle className="h-4 w-4 text-primary mr-2" />
                How does the minimal-cost voice engine work?
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                We utilize Microsoft Edge-TTS neural voices and browser Web Speech APIs as our core default. These deliver realistic, human-quality pronunciation and tone with zero third-party per-character charges. If you require custom brand voice cloning, you can connect your ElevenLabs account anytime.
              </p>
            </div>

            <div className="bg-card rounded-xl p-6 border border-border shadow-soft">
              <h3 className="font-bold text-foreground mb-2 flex items-center">
                <Database className="h-4 w-4 text-accent mr-2" />
                Is my PostgreSQL database safe with VoxAide?
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Yes. All database connections are strictly restricted to read-only transactions (<code className="text-xs bg-muted px-1.5 py-0.5 rounded">SET TRANSACTION READ ONLY</code>) with a 3-second query timeout and row limits. The AI can only look up relevant records (e.g. order tracking, availability) and can never modify, insert, or delete your data.
              </p>
            </div>

            <div className="bg-card rounded-xl p-6 border border-border shadow-soft">
              <h3 className="font-bold text-foreground mb-2 flex items-center">
                <PhoneCall className="h-4 w-4 text-blue-500 mr-2" />
                Can I connect my existing business phone number?
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Yes! Growth and Enterprise plans include Twilio SIP forwarding. You can either provision a new local/toll-free phone number directly from your dashboard or forward calls from your existing PBX system.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Pricing;
