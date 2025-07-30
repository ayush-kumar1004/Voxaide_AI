import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Check, Star, Zap } from "lucide-react";
import { Link } from "react-router-dom";

const Pricing = () => {
  const plans = [
    {
      name: "Starter",
      price: "Free",
      description: "Perfect for testing our AI voice support",
      features: [
        "100 minutes/month included",
        "1 AI agent",
        "Basic voice chat",
        "Standard knowledge base",
        "Email support",
        "Usage analytics"
      ],
      cta: "Start Free",
      popular: false
    },
    {
      name: "Business",
      price: "$5",
      period: "/year",
      description: "Ideal for growing businesses with multiple agents",
      features: [
        "5 AI agents included",
        "Unlimited knowledge base files",
        "$0.02/minute usage billing",
        "Advanced voice chat",
        "Priority support",
        "Detailed analytics",
        "API access",
        "Monthly usage reports"
      ],
      cta: "Start Business Plan",
      popular: true
    },
    {
      name: "Enterprise",
      price: "$10",
      period: "/year",
      description: "For larger teams with high-volume support needs",
      features: [
        "10 AI agents included",
        "Advanced AI training",
        "$0.02/minute usage billing",
        "Custom integrations",
        "Dedicated support",
        "White-label options",
        "SSO integration",
        "SLA guarantee",
        "Custom deployment"
      ],
      cta: "Start Enterprise Plan",
      popular: false
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="pt-16">
        {/* Header */}
        <section className="py-20 bg-gradient-hero">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <h1 className="text-4xl sm:text-5xl font-bold mb-6">
              Simple, <span className="gradient-text">Transparent</span> Pricing
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Choose the perfect plan for your business. Start free and scale as you grow.
            </p>
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {plans.map((plan, index) => (
                <Card 
                  key={index} 
                  className={`relative p-8 ${plan.popular ? 'ring-2 ring-primary shadow-glow' : 'shadow-soft'}`}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <div className="bg-primary text-primary-foreground px-4 py-1 rounded-full text-sm font-medium flex items-center">
                        <Star className="h-4 w-4 mr-1" />
                        Most Popular
                      </div>
                    </div>
                  )}

                  <div className="text-center mb-8">
                    <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                    <div className="mb-4">
                      <span className="text-4xl font-bold">{plan.price}</span>
                      {plan.period && (
                        <span className="text-muted-foreground">{plan.period}</span>
                      )}
                    </div>
                    <p className="text-muted-foreground">{plan.description}</p>
                  </div>

                  <div className="space-y-4 mb-8">
                    {plan.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center space-x-3">
                        <Check className="h-5 w-5 text-accent flex-shrink-0" />
                        <span className="text-sm">{feature}</span>
                      </div>
                    ))}
                  </div>

                  <Link to={plan.name === "Enterprise" ? "/contact" : "/signup"}>
                    <Button 
                      variant={plan.popular ? "hero" : "outline"} 
                      className="w-full"
                      size="lg"
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-20 bg-muted/30">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Frequently Asked Questions</h2>
              <p className="text-muted-foreground">Everything you need to know about our pricing</p>
            </div>

            <div className="space-y-6">
              {[
                {
                  q: "Can I change plans anytime?",
                  a: "Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately."
                },
                {
                  q: "What happens if I exceed my query limit?",
                  a: "We'll notify you when you're approaching your limit. You can upgrade your plan or purchase additional queries."
                },
                {
                  q: "Is there a setup fee?",
                  a: "No setup fees. You only pay for your chosen plan, and you can start with our free tier."
                },
                {
                  q: "Do you offer annual discounts?",
                  a: "Yes, save 20% when you pay annually. Contact our sales team for enterprise pricing."
                },
                {
                  q: "What kind of support do you provide?",
                  a: "All plans include email support. Pro and Enterprise plans get priority support and dedicated assistance."
                }
              ].map((faq, index) => (
                <Card key={index} className="p-6">
                  <h3 className="font-semibold mb-2">{faq.q}</h3>
                  <p className="text-muted-foreground">{faq.a}</p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-gradient-hero">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-center mb-6">
              <Zap className="h-12 w-12 text-primary mr-4" />
              <h2 className="text-3xl font-bold">Ready to Get Started?</h2>
            </div>
            <p className="text-xl text-muted-foreground mb-8">
              Join hundreds of companies already using Voxaide to transform their customer support.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/signup">
                <Button variant="hero" size="xl">
                  Start Free Trial
                </Button>
              </Link>
              <Link to="/demo">
                <Button variant="outline" size="xl">
                  Schedule Demo
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Pricing;