import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import HowItWorks from "@/components/HowItWorks";
import Features from "@/components/Features";
import { Button } from "@/components/ui/button";
import { ArrowRight, Quote } from "lucide-react";
import { Link } from "react-router-dom";

const Home = () => {
  const testimonials = [
    {
      quote: "Voxaide reduced our support response time by 95% and improved customer satisfaction significantly.",
      author: "Sarah Johnson",
      role: "Head of Customer Success",
      company: "TechCorp"
    },
    {
      quote: "The AI understands our customers better than we expected. It's like having a super-agent available 24/7.",
      author: "Michael Chen",
      role: "CTO",
      company: "InnovateLabs"
    },
    {
      quote: "Implementation was seamless, and the ROI was visible within the first month of deployment.",
      author: "Emily Rodriguez",
      role: "Operations Director",
      company: "ScaleUp Inc"
    }
  ];

  return (
    <div className="min-h-screen">
      <Navigation />
      <Hero />
      <HowItWorks />
      <Features />
      
      {/* Testimonials Section */}
      <section className="py-20 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Trusted by <span className="gradient-text">Leading Teams</span>
            </h2>
            <p className="text-xl text-muted-foreground">
              See what our customers say about transforming their support
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-card rounded-xl p-6 shadow-soft border border-border">
                <Quote className="h-8 w-8 text-primary mb-4" />
                <blockquote className="text-muted-foreground mb-6 leading-relaxed">
                  "{testimonial.quote}"
                </blockquote>
                <div>
                  <div className="font-semibold">{testimonial.author}</div>
                  <div className="text-sm text-muted-foreground">
                    {testimonial.role} • {testimonial.company}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-hero">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to Transform Your Customer Support?
          </h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join hundreds of companies already using Voxaide to deliver exceptional customer experiences.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup">
              <Button variant="hero" size="xl" className="group">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
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

      {/* Footer */}
      <footer className="bg-muted/30 py-12 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="text-xl font-bold gradient-text">Voxaide</div>
              </div>
              <p className="text-muted-foreground text-sm">
                Your smartest customer support agent, powered by AI.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to="/features" className="hover:text-primary transition-colors">Features</Link></li>
                <li><Link to="/pricing" className="hover:text-primary transition-colors">Pricing</Link></li>
                <li><Link to="/demo" className="hover:text-primary transition-colors">Demo</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to="/about" className="hover:text-primary transition-colors">About</Link></li>
                <li><Link to="/contact" className="hover:text-primary transition-colors">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to="/docs" className="hover:text-primary transition-colors">Documentation</Link></li>
                <li><Link to="/help" className="hover:text-primary transition-colors">Help Center</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border pt-8 mt-8 text-center text-sm text-muted-foreground">
            <p>&copy; 2024 Voxaide. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;