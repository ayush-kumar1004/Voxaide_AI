import { useState } from "react";
import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import HowItWorks from "@/components/HowItWorks";
import Features from "@/components/Features";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { ArrowRight, Quote, Calculator, TrendingUp, Clock, DollarSign, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const Home = () => {
  const [monthlyCalls, setMonthlyCalls] = useState<number[]>([2500]);

  const calls = monthlyCalls[0];
  const humanCost = Math.round(calls * 4.5); // Approx $4.50 per human support call
  const voxaideCost = Math.round(calls * 0.45); // Approx $0.45 per AI call
  const savings = humanCost - voxaideCost;
  const hoursSaved = Math.round((calls * 8) / 60); // 8 mins per call saved

  const testimonials = [
    {
      quote: "VoxAide resolved 78% of our customer order tracking calls automatically via PostgreSQL live lookups. Our team can now focus on high-touch enterprise accounts.",
      author: "Sarah Johnson",
      role: "VP of Customer Operations",
      company: "Logistiq Worldwide"
    },
    {
      quote: "We switched from standard IVRs to VoxAide voice agents. Call abandonment dropped to under 1.5%, and customers love that the bot has zero hold time.",
      author: "Michael Chen",
      role: "CTO",
      company: "InnovateLabs"
    },
    {
      quote: "The zero-cost voice engine and simple database connection made setup effortless. We went live on our support phone lines in less than two days.",
      author: "Emily Rodriguez",
      role: "Operations Director",
      company: "ScaleUp Commerce"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <Hero />
      <HowItWorks />
      <Features />

      {/* Interactive ROI Calculator Section */}
      <section className="py-24 bg-background border-t border-border">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-accent/10 text-accent text-xs font-semibold mb-3">
              <Calculator className="h-3.5 w-3.5 mr-1.5" />
              ROI Impact Estimator
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
              Calculate Your <span className="gradient-text">Cost & Time Savings</span>
            </h2>
            <p className="text-lg text-muted-foreground">
              See how much your organization saves by replacing legacy IVR queues with VoxAide voice agents.
            </p>
          </div>

          <div className="bg-card rounded-2xl p-8 sm:p-10 shadow-large border border-border">
            <div className="mb-8">
              <div className="flex justify-between items-center mb-3">
                <span className="font-semibold text-foreground text-sm sm:text-base">
                  Estimated Monthly Inbound / Outbound Calls:
                </span>
                <span className="text-2xl font-extrabold text-primary font-mono">
                  {calls.toLocaleString()} calls
                </span>
              </div>
              <Slider
                value={monthlyCalls}
                onValueChange={setMonthlyCalls}
                min={500}
                max={20000}
                step={250}
                className="py-4"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>500 calls/mo</span>
                <span>10,000 calls/mo</span>
                <span>20,000+ calls/mo</span>
              </div>
            </div>

            {/* Savings Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-6 border-t border-border">
              <div className="bg-muted/40 rounded-xl p-5 border border-border/50 text-center">
                <div className="flex items-center justify-center text-primary mb-2">
                  <DollarSign className="h-5 w-5 mr-1" />
                  <span className="text-xs uppercase tracking-wider font-semibold">Monthly Savings</span>
                </div>
                <div className="text-3xl sm:text-4xl font-extrabold text-accent font-mono">
                  ${savings.toLocaleString()}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  vs. traditional $4.50/call human agent
                </div>
              </div>

              <div className="bg-muted/40 rounded-xl p-5 border border-border/50 text-center">
                <div className="flex items-center justify-center text-primary mb-2">
                  <Clock className="h-5 w-5 mr-1" />
                  <span className="text-xs uppercase tracking-wider font-semibold">Hours Saved</span>
                </div>
                <div className="text-3xl sm:text-4xl font-extrabold text-foreground font-mono">
                  {hoursSaved.toLocaleString()} hrs
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Queue and handle time eliminated
                </div>
              </div>

              <div className="bg-muted/40 rounded-xl p-5 border border-border/50 text-center">
                <div className="flex items-center justify-center text-primary mb-2">
                  <TrendingUp className="h-5 w-5 mr-1" />
                  <span className="text-xs uppercase tracking-wider font-semibold">Cost Reduction</span>
                </div>
                <div className="text-3xl sm:text-4xl font-extrabold text-primary font-mono">
                  ~90%
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Average customer service margin gain
                </div>
              </div>
            </div>

            <div className="mt-8 text-center">
              <Link to="/pricing">
                <Button size="lg" className="bg-primary hover:bg-primary-hover text-white shadow-soft">
                  Start Automating Calls Today
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-24 bg-muted/20 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
              Trusted by <span className="gradient-text">Leading Support Teams</span>
            </h2>
            <p className="text-lg text-muted-foreground">
              See how modern enterprises transform customer experience with VoxAide.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-card rounded-2xl p-7 shadow-soft border border-border flex flex-col justify-between">
                <div>
                  <Quote className="h-8 w-8 text-primary/40 mb-4" />
                  <blockquote className="text-foreground text-sm sm:text-base mb-6 leading-relaxed">
                    "{testimonial.quote}"
                  </blockquote>
                </div>
                <div className="pt-4 border-t border-border/60">
                  <div className="font-bold text-foreground text-sm">{testimonial.author}</div>
                  <div className="text-xs text-muted-foreground">
                    {testimonial.role} • <span className="text-primary font-medium">{testimonial.company}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-hero border-t border-border">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold mb-4">
            <Sparkles className="h-3.5 w-3.5 mr-1.5" />
            Zero Setup Fee • 14-Day Free Trial
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-6">
            Ready to Automate Your Voice Support?
          </h2>
          <p className="text-lg sm:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
            Connect your PostgreSQL database, upload your company documents, and deploy your first voice agent in minutes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup">
              <Button size="xl" className="bg-primary hover:bg-primary-hover text-white shadow-glow group">
                Create Free Account
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button variant="outline" size="xl" className="border-border bg-card/60 backdrop-blur-sm">
                Explore Pricing Plans
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-muted/40 py-14 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-2xl font-extrabold gradient-text">Voxaide</span>
              </div>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Autonomous voice & omnichannel customer service platform for modern enterprises. Sub-300ms latency, PostgreSQL connected, 24/7 available.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground text-sm">Product</h4>
              <ul className="space-y-2.5 text-sm text-muted-foreground">
                <li><Link to="/features" className="hover:text-primary transition-colors">Features</Link></li>
                <li><Link to="/pricing" className="hover:text-primary transition-colors">Pricing & Plans</Link></li>
                <li><Link to="/customer-chat" className="hover:text-primary transition-colors">Customer Chat Demo</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground text-sm">Platform</h4>
              <ul className="space-y-2.5 text-sm text-muted-foreground">
                <li><Link to="/dashboard" className="hover:text-primary transition-colors">Tenant Dashboard</Link></li>
                <li><Link to="/about" className="hover:text-primary transition-colors">About Us</Link></li>
                <li><Link to="/contact" className="hover:text-primary transition-colors">Contact Sales</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground text-sm">Legal & Support</h4>
              <ul className="space-y-2.5 text-sm text-muted-foreground">
                <li><Link to="/terms" className="hover:text-primary transition-colors">Terms of Service</Link></li>
                <li><Link to="/privacy" className="hover:text-primary transition-colors">Privacy Policy</Link></li>
                <li><Link to="/help" className="hover:text-primary transition-colors">Help Center</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border pt-8 mt-12 flex flex-col sm:flex-row items-center justify-between text-xs text-muted-foreground">
            <p>&copy; 2026 Voxaide AI Inc. All rights reserved.</p>
            <p className="mt-2 sm:mt-0">Powered by Agentic Voice AI & Multi-Tenant RAG</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
