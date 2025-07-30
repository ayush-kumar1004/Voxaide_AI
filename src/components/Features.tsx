import { Mic, Brain, Database, Users, BarChart3, Shield, Clock, Zap } from "lucide-react";

const Features = () => {
  const features = [
    {
      icon: Mic,
      title: "Voice-First Interface",
      description: "Natural conversation with customers through advanced speech recognition and synthesis"
    },
    {
      icon: Brain,
      title: "Contextual Memory",
      description: "Remembers conversation history and customer context for personalized interactions"
    },
    {
      icon: Database,
      title: "Custom Knowledge Base",
      description: "Integrates with your company data, FAQs, policies, and order management systems"
    },
    {
      icon: Users,
      title: "Human Escalation",
      description: "Seamlessly transfers complex queries to human agents when AI reaches its limits"
    },
    {
      icon: BarChart3,
      title: "Analytics Dashboard",
      description: "Track resolution rates, response times, customer satisfaction, and conversation insights"
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "SOC 2 compliant with end-to-end encryption and secure data handling"
    },
    {
      icon: Clock,
      title: "24/7 Availability",
      description: "Round-the-clock customer support without human agent limitations"
    },
    {
      icon: Zap,
      title: "Instant Responses",
      description: "Average response time under 2 seconds for improved customer experience"
    }
  ];

  return (
    <section className="py-20 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Powerful <span className="gradient-text">Features</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Everything you need to revolutionize your customer support with AI
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div 
                key={index} 
                className="bg-card rounded-xl p-6 shadow-soft border border-border card-hover group"
              >
                <div className="mb-4">
                  <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
};

export default Features;