import { Upload, Bot, MessageCircle, CheckCircle } from "lucide-react";

const HowItWorks = () => {
  const steps = [
    {
      icon: Upload,
      title: "Upload Your Data",
      description: "Upload company FAQs, order data, policies, and knowledge base in JSON, TXT, or structured formats.",
      color: "text-blue-500"
    },
    {
      icon: Bot,
      title: "AI Training",
      description: "Voxaide trains a custom voice bot specifically for your support team using Google Vertex AI technology.",
      color: "text-purple-500"
    },
    {
      icon: MessageCircle,
      title: "Voice Interaction",
      description: "Customers speak their questions naturally, and Voxaide provides contextual, intelligent responses in real-time.",
      color: "text-green-500"
    },
    {
      icon: CheckCircle,
      title: "Smart Resolution",
      description: "AI solves issues, updates records automatically, and escalates to human agents when needed.",
      color: "text-orange-500"
    }
  ];

  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            How <span className="gradient-text">Voxaide</span> Works
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Transform your customer support in four simple steps with our AI-powered voice assistant
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="relative">
                {/* Connection Line */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-12 left-full w-full h-0.5 bg-gradient-to-r from-border to-transparent z-0"></div>
                )}
                
                <div className="relative bg-card rounded-2xl p-6 shadow-soft border border-border card-hover text-center">
                  {/* Step Number */}
                  <div className="absolute -top-3 -left-3 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>

                  {/* Icon */}
                  <div className="mb-4">
                    <div className={`w-16 h-16 mx-auto bg-gradient-to-br from-background to-muted rounded-full flex items-center justify-center shadow-soft`}>
                      <Icon className={`h-8 w-8 ${step.color}`} />
                    </div>
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Technical Details */}
        <div className="mt-16 bg-gradient-card rounded-2xl p-8 border border-border">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold mb-2">Powered by Advanced AI</h3>
            <p className="text-muted-foreground">Built with industry-leading technologies for enterprise-grade reliability</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div>
              <div className="text-2xl font-bold text-primary mb-1">Vertex AI</div>
              <div className="text-sm text-muted-foreground">Google Cloud</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-primary mb-1">Speech-to-Text</div>
              <div className="text-sm text-muted-foreground">Real-time STT</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-primary mb-1">Text-to-Speech</div>
              <div className="text-sm text-muted-foreground">Natural TTS</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-primary mb-1">Session Memory</div>
              <div className="text-sm text-muted-foreground">Context Aware</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;