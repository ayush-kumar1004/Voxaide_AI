import { Button } from "@/components/ui/button";
import { ArrowRight, PlayCircle, Mic, Bot, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const Hero = () => {
  return (
    <section className="pt-16 pb-20 bg-gradient-hero relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      <div className="absolute top-20 left-10 animate-float">
        <Sparkles className="h-8 w-8 text-accent opacity-30" />
      </div>
      <div className="absolute top-40 right-20 animate-float" style={{animationDelay: '2s'}}>
        <Bot className="h-12 w-12 text-primary opacity-20" />
      </div>
      <div className="absolute bottom-20 left-20 animate-float" style={{animationDelay: '4s'}}>
        <Mic className="h-6 w-6 text-accent opacity-40" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center">
          {/* Badge */}
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-primary-light text-primary text-sm font-medium mb-8">
            <Sparkles className="h-4 w-4 mr-2" />
            Powered by Google Vertex AI
          </div>

          {/* Main Heading */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            Say Hello to{" "}
            <span className="gradient-text">Smarter Support</span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl sm:text-2xl text-muted-foreground max-w-3xl mx-auto mb-8 leading-relaxed">
            Your AI-powered voice assistant that understands customer needs, 
            provides instant solutions, and learns from your company data.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Link to="/demo">
              <Button variant="hero" size="xl" className="group">
                Request Demo
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/customer-chat">
              <Button variant="outline" size="xl" className="group">
                <PlayCircle className="mr-2 h-5 w-5" />
                Try Voice Chat
              </Button>
            </Link>
          </div>

          {/* AI Voice Demo Visualization */}
          <div className="relative max-w-4xl mx-auto">
            <div className="bg-card rounded-2xl shadow-large p-8 border border-border">
              <div className="flex items-center justify-center space-x-4 mb-6">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-accent rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-muted-foreground">Customer</span>
                </div>
                <div className="flex-1 h-px bg-border"></div>
                <div className="relative">
                  <Bot className="h-8 w-8 text-primary animate-pulse-slow" />
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-accent rounded-full animate-ping"></div>
                </div>
                <div className="flex-1 h-px bg-border"></div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Voxaide AI</span>
                  <div className="w-3 h-3 bg-primary rounded-full animate-pulse"></div>
                </div>
              </div>

              <div className="text-center">
                <div className="inline-flex items-center px-6 py-3 bg-accent-light rounded-full mb-4">
                  <Mic className="h-5 w-5 text-accent mr-2" />
                  <span className="text-accent font-medium">"Where is my order ZMT1003?"</span>
                </div>
                <div className="text-sm text-muted-foreground mb-4">Processing voice input...</div>
                <div className="inline-flex items-center px-6 py-3 bg-primary-light rounded-full">
                  <Bot className="h-5 w-5 text-primary mr-2" />
                  <span className="text-primary font-medium">
                    "Your order is delivered and marked as resolved!"
                  </span>
                </div>
              </div>
            </div>

            {/* Floating Stats */}
            <div className="absolute -left-4 top-4 bg-card rounded-lg shadow-medium p-3 border border-border">
              <div className="text-2xl font-bold text-primary">99.9%</div>
              <div className="text-xs text-muted-foreground">Accuracy</div>
            </div>
            <div className="absolute -right-4 bottom-4 bg-card rounded-lg shadow-medium p-3 border border-border">
              <div className="text-2xl font-bold text-accent">2s</div>
              <div className="text-xs text-muted-foreground">Response</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;