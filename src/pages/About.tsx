import Navigation from "@/components/Navigation";
import { Card } from "@/components/ui/card";
import { Brain, Target, Users, Zap } from "lucide-react";

const About = () => {
  const founders = [
    {
      name: "Alex Chen",
      role: "CEO & Co-Founder",
      bio: "Former Google AI researcher with 10+ years in conversational AI and machine learning.",
      image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face"
    },
    {
      name: "Sarah Rodriguez",
      role: "CTO & Co-Founder", 
      bio: "Ex-Microsoft engineer specializing in voice technologies and enterprise software architecture.",
      image: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face"
    },
    {
      name: "Michael Kumar",
      role: "Head of AI",
      bio: "PhD in Natural Language Processing, previously led AI initiatives at Salesforce and OpenAI.",
      image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&crop=face"
    }
  ];

  const values = [
    {
      icon: Brain,
      title: "AI-First Innovation",
      description: "We believe AI should augment human capabilities, not replace them. Our technology empowers support teams to deliver exceptional experiences."
    },
    {
      icon: Target,
      title: "Customer-Centric Design",
      description: "Every feature we build starts with understanding real customer pain points and designing solutions that truly make a difference."
    },
    {
      icon: Users,
      title: "Accessible Technology",
      description: "Advanced AI shouldn't be limited to tech giants. We make enterprise-grade conversational AI accessible to businesses of all sizes."
    },
    {
      icon: Zap,
      title: "Continuous Learning",
      description: "Our AI gets smarter with every interaction, constantly improving to better serve your customers and understand your business."
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="pt-16">
        {/* Hero Section */}
        <section className="py-20 bg-gradient-hero">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <h1 className="text-4xl sm:text-5xl font-bold mb-6">
              Revolutionizing Customer Support with <span className="gradient-text">Conversational AI</span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Founded in 2024, Voxaide emerged from a simple yet powerful vision: to make customer support more intelligent, efficient, and human-centered through the power of AI.
            </p>
          </div>
        </section>

        {/* Mission Section */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-3xl font-bold mb-6">Our Mission</h2>
                <p className="text-lg text-muted-foreground mb-6">
                  We're on a mission to transform customer support from a cost center into a competitive advantage. By combining cutting-edge AI with deep understanding of customer service dynamics, we help businesses deliver instant, accurate, and empathetic support at scale.
                </p>
                <p className="text-lg text-muted-foreground">
                  Our platform doesn't just answer questions – it understands context, learns from interactions, and continuously improves to provide increasingly better customer experiences.
                </p>
              </div>
              <div className="relative">
                <div className="bg-gradient-card rounded-2xl p-8 shadow-large border border-border">
                  <div className="grid grid-cols-2 gap-6 text-center">
                    <div>
                      <div className="text-3xl font-bold text-primary mb-2">500+</div>
                      <div className="text-sm text-muted-foreground">Companies Served</div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-accent mb-2">2M+</div>
                      <div className="text-sm text-muted-foreground">Queries Resolved</div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-blue-500 mb-2">99.9%</div>
                      <div className="text-sm text-muted-foreground">Uptime</div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-green-500 mb-2">4.9★</div>
                      <div className="text-sm text-muted-foreground">Customer Rating</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Values Section */}
        <section className="py-20 bg-muted/30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold mb-4">Our Values</h2>
              <p className="text-xl text-muted-foreground">The principles that guide everything we do</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {values.map((value, index) => {
                const Icon = value.icon;
                return (
                  <Card key={index} className="p-8 shadow-soft border border-border">
                    <div className="flex items-start space-x-4">
                      <div className="p-3 bg-gradient-primary rounded-lg">
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold mb-3">{value.title}</h3>
                        <p className="text-muted-foreground leading-relaxed">{value.description}</p>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>

        {/* Team Section */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold mb-4">Meet Our Team</h2>
              <p className="text-xl text-muted-foreground">The brilliant minds behind Voxaide</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {founders.map((founder, index) => (
                <Card key={index} className="p-6 text-center shadow-soft border border-border card-hover">
                  <div className="mb-6">
                    <img
                      src={founder.image}
                      alt={founder.name}
                      className="w-32 h-32 rounded-full mx-auto object-cover shadow-medium"
                    />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{founder.name}</h3>
                  <div className="text-primary font-medium mb-4">{founder.role}</div>
                  <p className="text-muted-foreground text-sm leading-relaxed">{founder.bio}</p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Technology Section */}
        <section className="py-20 bg-muted/30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold mb-4">Built on Cutting-Edge Technology</h2>
              <p className="text-xl text-muted-foreground">Powered by the latest advances in AI and cloud computing</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {[
                { name: "Google Vertex AI", description: "Advanced language models" },
                { name: "Cloud Speech APIs", description: "Real-time voice processing" },
                { name: "React & Flask", description: "Modern web architecture" },
                { name: "Enterprise Security", description: "SOC 2 compliance" }
              ].map((tech, index) => (
                <Card key={index} className="p-6 text-center shadow-soft border border-border">
                  <h3 className="font-semibold mb-2">{tech.name}</h3>
                  <p className="text-sm text-muted-foreground">{tech.description}</p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Story Section */}
        <section className="py-20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold mb-8">Our Story</h2>
              <div className="prose prose-lg max-w-none">
                <p className="text-muted-foreground mb-6">
                  The idea for Voxaide was born from a frustrating customer service experience. After spending hours on hold and being transferred multiple times for a simple order inquiry, our founders realized there had to be a better way.
                </p>
                <p className="text-muted-foreground mb-6">
                  With backgrounds in AI research and enterprise software, they set out to create an intelligent voice assistant that could understand customer needs, access company data, and provide instant, accurate responses – all while maintaining the empathy and understanding that customers deserve.
                </p>
                <p className="text-muted-foreground">
                  Today, Voxaide serves hundreds of companies worldwide, from startups to Fortune 500 enterprises, helping them deliver exceptional customer experiences while reducing costs and improving efficiency.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default About;