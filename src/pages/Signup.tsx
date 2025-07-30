import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Eye, EyeOff, Mail, Lock, User, Building, Zap, Mic, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { getAuth, createUserWithEmailAndPassword } from "firebase/auth";
import { doc, setDoc } from "firebase/firestore";
import { db } from "@/firebase"; // make sure path is correct

const Signup = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    company: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      toast({
        title: "Password Mismatch",
        description: "Passwords don't match. Please try again.",
        variant: "destructive"
      });
      return;
    }

    if (!formData.acceptTerms) {
      toast({
        title: "Terms Required",
        description: "Please accept the terms and conditions to continue.",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);

const auth = getAuth();

try {
  const userCredential = await createUserWithEmailAndPassword(auth, formData.email, formData.password);
  const user = userCredential.user;

  const userData = {
    firstName: formData.firstName,
    lastName: formData.lastName,
    email: formData.email,
    company: formData.company,
    verified: false,
    accountType: formData.company ? "business" : "personal",
    joinDate: new Date().toISOString()
  };

  await setDoc(doc(db, "users", user.uid), userData);

  toast({
    title: "Welcome to Voxaide!",
    description: "Your account has been created successfully."
  });

  localStorage.setItem("user", JSON.stringify({ ...userData, isLoggedIn: true }));

  navigate("/", { replace: true });
} catch (error: any) {
  console.error("Signup error:", error);
  toast({
    title: "Signup Failed",
    description: error.message || "Something went wrong.",
    variant: "destructive"
  });
} finally {
  setIsLoading(false);
}


  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const benefits = [
    "Voice-powered AI customer support",
    "Real-time speech recognition & response",
    "Custom knowledge base integration",
    "24/7 automated customer assistance",
    "Advanced analytics and insights"
  ];

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Left side - Benefits */}
          <div className="hidden lg:block">
            <div className="text-center lg:text-left">
              <Link to="/" className="flex items-center justify-center lg:justify-start space-x-2 mb-8">
                <div className="relative">
                  <Zap className="h-10 w-10 text-primary" />
                  <Mic className="h-5 w-5 text-accent absolute -bottom-1 -right-1" />
                </div>
                <span className="text-2xl font-bold gradient-text">Voxaide</span>
              </Link>
              <h1 className="text-4xl font-bold mb-6">
                Transform Your Customer Support with AI
              </h1>
              <p className="text-xl text-muted-foreground mb-8">
                Join thousands of companies using Voxaide to deliver exceptional customer experiences.
              </p>

              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <div className="p-1 bg-accent rounded-full">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                    <span className="text-muted-foreground">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right side - Signup Form */}
          <div className="w-full max-w-md mx-auto">
            <div className="text-center mb-8 lg:hidden">
              <Link to="/" className="flex items-center justify-center space-x-2 mb-6">
                <div className="relative">
                  <Zap className="h-8 w-8 text-primary" />
                  <Mic className="h-4 w-4 text-accent absolute -bottom-1 -right-1" />
                </div>
                <span className="text-xl font-bold gradient-text">Voxaide</span>
              </Link>
            </div>

            <Card className="p-8 shadow-large border border-border">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold">Create your account</h2>
                <p className="text-muted-foreground mt-2">
                  Start your free trial today
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="firstName" className="block text-sm font-medium mb-1">
                      First name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="firstName"
                        name="firstName"
                        type="text"
                        required
                        value={formData.firstName}
                        onChange={handleInputChange}
                        placeholder="John"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="lastName" className="block text-sm font-medium mb-1">
                      Last name
                    </label>
                    <Input
                      id="lastName"
                      name="lastName"
                      type="text"
                      required
                      value={formData.lastName}
                      onChange={handleInputChange}
                      placeholder="Doe"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium mb-1">
                    Email address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      required
                      value={formData.email}
                      onChange={handleInputChange}
                      placeholder="john@company.com"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="company" className="block text-sm font-medium mb-1">
                    Company name
                  </label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="company"
                      name="company"
                      type="text"
                      required
                      value={formData.company}
                      onChange={handleInputChange}
                      placeholder="Your Company"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium mb-1">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      required
                      value={formData.password}
                      onChange={handleInputChange}
                      placeholder="Create a strong password"
                      className="pl-10 pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium mb-1">
                    Confirm password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      required
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      placeholder="Confirm your password"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    id="acceptTerms"
                    name="acceptTerms"
                    type="checkbox"
                    required
                    checked={formData.acceptTerms}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-primary border-border rounded focus:ring-primary"
                  />
                  <label htmlFor="acceptTerms" className="ml-2 block text-sm text-muted-foreground">
                    I agree to the{" "}
                    <Link to="/terms" className="text-primary hover:text-primary-hover">
                      Terms of Service
                    </Link>{" "}
                    and{" "}
                    <Link to="/privacy" className="text-primary hover:text-primary-hover">
                      Privacy Policy
                    </Link>
                  </label>
                </div>

                <Button
                  type="submit"
                  variant="hero"
                  className="w-full"
                  size="lg"
                  disabled={isLoading}
                >
                  {isLoading ? "Creating account..." : "Create account"}
                </Button>
              </form>

              <div className="mt-6">
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-border" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-card text-muted-foreground">Or sign up with</span>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3">
                  <Button variant="outline" className="w-full">
                    <svg className="h-4 w-4 mr-2" viewBox="0 0 24 24">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                    </svg>
                    Google
                  </Button>
                  <Button variant="outline" className="w-full">
                    <svg className="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
                    </svg>
                    GitHub
                  </Button>
                </div>
              </div>
            </Card>

            {/* Sign in link */}
            <div className="text-center mt-6">
              <p className="text-muted-foreground">
                Already have an account?{" "}
                <Link to="/login" className="text-primary hover:text-primary-hover font-medium">
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup; 