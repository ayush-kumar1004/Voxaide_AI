import { useState } from "react";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Mail, Phone, MapPin, Calendar, Send } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Contact = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    message: "",
    inquiry: "demo"
  });

  const { toast } = useToast();
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  try {
    const payload = {
      fullName: formData.name,
      email: formData.email,
      company: formData.company,
      message: formData.message,
      inquiryType: formData.inquiry
    };

    const response = await fetch("http://localhost:5000/api/contact", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to send message.");
    }

    toast({
      title: "Message Sent!",
      description: data.message || "We'll get back to you within 24 hours."
    });

    setFormData({
      name: "",
      email: "",
      company: "",
      message: "",
      inquiry: "demo"
    });

  } catch (error: any) {
    toast({
      title: "Error Sending Message",
      description: error.message || "Something went wrong.",
      variant: "destructive"
    });
  }
};

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="pt-16">
        {/* Header */}
        <section className="py-20 bg-gradient-hero">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <h1 className="text-4xl sm:text-5xl font-bold mb-6">
              Get in <span className="gradient-text">Touch</span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Ready to transform your customer support? Let's talk about how Voxaide can help your business.
            </p>
          </div>
        </section>

        {/* Contact Form & Info */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
              {/* Contact Form */}
              <Card className="p-8 shadow-large border border-border">
                <h2 className="text-2xl font-bold mb-6">Send us a message</h2>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium mb-2">
                        Full Name *
                      </label>
                      <Input
                        id="name"
                        name="name"
                        type="text"
                        required
                        value={formData.name}
                        onChange={handleInputChange}
                        placeholder="John Doe"
                      />
                    </div>
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium mb-2">
                        Email Address *
                      </label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={handleInputChange}
                        placeholder="john@company.com"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="company" className="block text-sm font-medium mb-2">
                      Company Name
                    </label>
                    <Input
                      id="company"
                      name="company"
                      type="text"
                      value={formData.company}
                      onChange={handleInputChange}
                      placeholder="Your Company"
                    />
                  </div>

                  <div>
                    <label htmlFor="inquiry" className="block text-sm font-medium mb-2">
                      Inquiry Type
                    </label>
                    <select
                      id="inquiry"
                      name="inquiry"
                      value={formData.inquiry}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                    >
                      <option value="demo">Request Demo</option>
                      <option value="pricing">Pricing Questions</option>
                      <option value="technical">Technical Support</option>
                      <option value="partnership">Partnership</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="message" className="block text-sm font-medium mb-2">
                      Message *
                    </label>
                    <Textarea
                      id="message"
                      name="message"
                      required
                      value={formData.message}
                      onChange={handleInputChange}
                      placeholder="Tell us about your customer support needs..."
                      rows={6}
                    />
                  </div>

                  <Button type="submit" variant="hero" className="w-full" size="lg">
                    <Send className="mr-2 h-4 w-4" />
                    Send Message
                  </Button>
                </form>
              </Card>

              {/* Contact Information */}
              <div className="space-y-8">
                <div>
                  <h2 className="text-2xl font-bold mb-6">Get in touch</h2>
                  <p className="text-muted-foreground mb-8">
                    Have questions about Voxaide? Our team is here to help. Reach out using any of the methods below.
                  </p>
                </div>

                <div className="space-y-6">
                  <Card className="p-6 shadow-soft border border-border">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-primary-light rounded-lg">
                        <Mail className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-semibold">Email Us</h3>
                        <p className="text-muted-foreground">hello@voxaide.ai</p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-6 shadow-soft border border-border">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-accent-light rounded-lg">
                        <Phone className="h-6 w-6 text-accent" />
                      </div>
                      <div>
                        <h3 className="font-semibold">Call Us</h3>
                        <p className="text-muted-foreground">+1 (555) 123-4567</p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-6 shadow-soft border border-border">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-blue-100 rounded-lg">
                        <MapPin className="h-6 w-6 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold">Visit Us</h3>
                        <p className="text-muted-foreground">
                          123 AI Street<br />
                          San Francisco, CA 94107
                        </p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-6 shadow-soft border border-border">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-green-100 rounded-lg">
                        <Calendar className="h-6 w-6 text-green-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold">Schedule a Demo</h3>
                        <p className="text-muted-foreground mb-3">
                          See Voxaide in action with a personalized demo
                        </p>
                        <Button variant="outline" size="sm">
                          Book Meeting
                        </Button>
                      </div>
                    </div>
                  </Card>
                </div>

                {/* Response Time */}
                <Card className="p-6 bg-gradient-card shadow-soft border border-border">
                  <h3 className="font-semibold mb-3">Response Times</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>General Inquiries</span>
                      <span className="text-muted-foreground">24 hours</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Demo Requests</span>
                      <span className="text-muted-foreground">4 hours</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Technical Support</span>
                      <span className="text-muted-foreground">12 hours</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Enterprise Sales</span>
                      <span className="text-muted-foreground">2 hours</span>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-20 bg-muted/30">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Common Questions</h2>
              <p className="text-muted-foreground">Quick answers to questions you might have</p>
            </div>

            <div className="space-y-6">
              {[
                {
                  q: "How quickly can Voxaide be deployed?",
                  a: "Most customers are up and running within 48 hours. Enterprise deployments typically take 1-2 weeks."
                },
                {
                  q: "Do you offer custom integrations?",
                  a: "Yes, we offer custom integrations with your existing CRM, helpdesk, and business systems."
                },
                {
                  q: "What languages does Voxaide support?",
                  a: "Voxaide currently supports 12 languages including English, Spanish, French, German, and more."
                },
                {
                  q: "Is my data secure with Voxaide?",
                  a: "Absolutely. We're SOC 2 compliant with enterprise-grade security and encryption."
                }
              ].map((faq, index) => (
                <Card key={index} className="p-6 shadow-soft border border-border">
                  <h3 className="font-semibold mb-2">{faq.q}</h3>
                  <p className="text-muted-foreground">{faq.a}</p>
                </Card>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Contact;