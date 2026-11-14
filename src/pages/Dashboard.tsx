import { useState, useEffect, useRef } from "react";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Upload, 
  FileText, 
  BarChart3, 
  MessageSquare, 
  Users, 
  Settings, 
  Trash2, 
  Search, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  Building2,
  FileSpreadsheet,
  Calendar,
  Phone,
  Bot,
  Send,
  Sparkles,
  Clock,
  ShieldAlert,
  PhoneIncoming,
  Database,
  Link2,
  ShieldCheck,
  Check,
  Code,
  Copy,
  CheckCheck,
  Play
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface KnowledgeDoc {
  id: string;
  company_id: string;
  filename: string;
  file_type: string;
  status: string;
  chunk_count: number;
  uploaded_at: string;
  metadata?: Record<string, any>;
}

interface AppointmentItem {
  id: string;
  company_id: string;
  customer_name: string;
  customer_phone: string;
  service: string;
  start_time: string;
  end_time: string;
  timezone: string;
  status: string;
  notes?: string;
}

interface ConversationItem {
  id: string;
  company_id: string;
  customer: string;
  channel: string;
  status: string;
  query: string;
  last_message: string;
  message_count: number;
  date: string;
  duration: string;
}

interface AnalyticsData {
  total_queries: number;
  total_conversations: number;
  resolution_rate: string;
  avg_response_time: string;
  appointments_scheduled: number;
  total_appointments: number;
  total_documents: number;
  total_chunks: number;
  escalations_count: number;
  categories: Array<{ category: string; percentage: number }>;
}

interface CallLogItem {
  call_sid: string;
  company_id: string;
  from_number: string;
  to_number: string;
  direction: string;
  status: string;
  duration_seconds: number;
  created_at: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ document_name: string; relevance_score: number; chunk_id: string }>;
  tools?: Array<{ name: string; result: any }>;
  latency_ms?: number;
}

const Dashboard = () => {
  const [companyId, setCompanyId] = useState<string>(() => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        if (user.company) {
          return user.company.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
        }
      }
    } catch (e) {}
    return "demo_company";
  });

  // State
  const [documents, setDocuments] = useState<KnowledgeDoc[]>([]);
  const [appointments, setAppointments] = useState<AppointmentItem[]>([]);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [callLogs, setCallLogs] = useState<CallLogItem[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  
  // Phone registration
  const [newPhoneNumber, setNewPhoneNumber] = useState<string>("");
  const [newPhoneLabel, setNewPhoneLabel] = useState<string>("Main Support Line");
  const [phoneNumbers, setPhoneNumbers] = useState<any[]>([]);

  // Test Agent Chat
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "intro",
      role: "assistant",
      content: "Hello! I am your company's AI Customer Support Agent. You can test asking me about company policies, checking availability, or booking an appointment."
    }
  ]);
  const [chatInput, setChatInput] = useState<string>("");
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const { toast } = useToast();

  const isLocal = typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");
  const apiBaseUrl = (import.meta as any).env?.VITE_API_URL || (isLocal ? "http://localhost:5000" : "https://voxaide-ai.onrender.com");

  const getHeaders = (targetCompany = companyId) => ({
    "Authorization": `Bearer dev_token_${targetCompany}`,
    "X-Company-ID": targetCompany,
    "X-Test-User-Id": `user_${targetCompany}`,
  });

  // Data Loaders
  const loadDocuments = async (targetCompany = companyId) => {
    setIsLoadingDocs(true);
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${targetCompany}/knowledge/documents`, {
        headers: getHeaders(targetCompany)
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error("Failed to load documents", err);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const loadAppointments = async (targetCompany = companyId) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${targetCompany}/appointments`, {
        headers: getHeaders(targetCompany)
      });
      if (res.ok) {
        const data = await res.json();
        setAppointments(data.appointments || []);
      }
    } catch (err) {
      console.error("Failed to load appointments", err);
    }
  };

  const loadConversations = async (targetCompany = companyId) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${targetCompany}/conversations`, {
        headers: getHeaders(targetCompany)
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (err) {
      console.error("Failed to load conversations", err);
    }
  };

  const loadAnalytics = async (targetCompany = companyId) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${targetCompany}/analytics`, {
        headers: getHeaders(targetCompany)
      });
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error("Failed to load analytics", err);
    }
  };

  const loadTelephony = async (targetCompany = companyId) => {
    try {
      const res1 = await fetch(`${apiBaseUrl}/api/companies/${targetCompany}/phone-numbers`, {
        headers: getHeaders(targetCompany)
      });
      if (res1.ok) {
        const data1 = await res1.json();
        setPhoneNumbers(data1.phone_numbers || []);
      }

      const res2 = await fetch(`${apiBaseUrl}/api/companies/${targetCompany}/call-logs`, {
        headers: getHeaders(targetCompany)
      });
      if (res2.ok) {
        const data2 = await res2.json();
        setCallLogs(data2.call_logs || []);
      }
    } catch (err) {
      console.error("Failed to load telephony data", err);
    }
  };

  // Database Connector State
  const [dbConfig, setDbConfig] = useState({
    host: "localhost",
    port: "5432",
    dbname: "ecommerce_db",
    user: "postgres",
    password: "",
    sslmode: "prefer",
    allowed_tables: ["orders", "products", "customers"]
  });
  const [dbStatus, setDbStatus] = useState<{ connected: boolean; message?: string; tables?: string[] }>({
    connected: false
  });
  const [isTestingDb, setIsTestingDb] = useState(false);
  const [isSavingDb, setIsSavingDb] = useState(false);

  const loadDbConnector = async (targetCompany = companyId) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${targetCompany}/connectors/postgres`, {
        headers: getHeaders(targetCompany)
      });
      if (res.ok) {
        const data = await res.json();
        if (data.connected && data.connector) {
          setDbStatus({
            connected: true,
            tables: data.connector.allowed_tables || []
          });
          setDbConfig(prev => ({
            ...prev,
            host: data.connector.host || prev.host,
            port: String(data.connector.port || prev.port),
            dbname: data.connector.dbname || prev.dbname,
            user: data.connector.user || prev.user,
            allowed_tables: data.connector.allowed_tables || prev.allowed_tables
          }));
        }
      }
    } catch (err) {
      console.warn("Could not load database connector", err);
    }
  };

  const handleTestDb = async () => {
    setIsTestingDb(true);
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${companyId}/connectors/postgres/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getHeaders(companyId)
        },
        body: JSON.stringify(dbConfig)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setDbStatus({
          connected: true,
          message: data.message,
          tables: data.tables || []
        });
        toast({
          title: "Connection Successful",
          description: data.message || "Connected to PostgreSQL database!"
        });
      } else {
        toast({
          title: "Connection Failed",
          description: data.error || "Could not connect to PostgreSQL.",
          variant: "destructive"
        });
      }
    } catch (err) {
      toast({
        title: "Connection Error",
        description: "Network error testing database.",
        variant: "destructive"
      });
    } finally {
      setIsTestingDb(false);
    }
  };

  const handleSaveDb = async () => {
    setIsSavingDb(true);
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${companyId}/connectors/postgres`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getHeaders(companyId)
        },
        body: JSON.stringify(dbConfig)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setDbStatus({
          connected: true,
          tables: data.connector?.allowed_tables || dbConfig.allowed_tables
        });
        toast({
          title: "Connector Saved",
          description: "PostgreSQL database is now active and ready for AI agent queries."
        });
      } else {
        toast({
          title: "Save Failed",
          description: data.error || "Could not save database connector.",
          variant: "destructive"
        });
      }
    } catch (err) {
      toast({
        title: "Save Error",
        description: "Failed to save database configuration.",
        variant: "destructive"
      });
    } finally {
      setIsSavingDb(false);
    }
  };

  // Multi-Agent State
  const [agents, setAgents] = useState<any[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>("agent_support_01");
  const [isCreatingAgent, setIsCreatingAgent] = useState(false);
  const [newAgent, setNewAgent] = useState({
    agent_name: "",
    role: "Inbound Sales",
    voice_model: "en-US-JennyNeural",
    greeting: "Hello! How can I help you today?",
    system_instructions: "You are an AI assistant. Answer inquiries politely and accurately using company knowledge.",
    allowed_tables: ["orders", "products"]
  });

  // Embed Widget State
  const [widgetTheme, setWidgetTheme] = useState("#2563EB");
  const [widgetTitle, setWidgetTitle] = useState("VoxAide Support");
  const [copiedScript, setCopiedScript] = useState(false);

  const loadAgents = async (targetCompany = companyId) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/agent/companies/${targetCompany}/agents`, {
        headers: getHeaders(targetCompany)
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data.agents || []);
        if (data.agents && data.agents.length > 0 && !selectedAgentId) {
          setSelectedAgentId(data.agents[0].agent_id);
        }
      }
    } catch (err) {
      console.warn("Could not load agents", err);
    }
  };

  const handleCreateAgent = async () => {
    if (!newAgent.agent_name.trim()) {
      toast({ title: "Name Required", description: "Please enter an agent name.", variant: "destructive" });
      return;
    }
    setIsCreatingAgent(true);
    try {
      const res = await fetch(`${apiBaseUrl}/api/agent/companies/${companyId}/agents`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getHeaders(companyId) },
        body: JSON.stringify(newAgent)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        toast({ title: "Agent Created!", description: `${data.agent.agent_name} is active.` });
        setNewAgent({
          agent_name: "",
          role: "Technical Support",
          voice_model: "en-US-JennyNeural",
          greeting: "Hello! How can I help you today?",
          system_instructions: "You are an AI assistant. Answer inquiries politely and accurately.",
          allowed_tables: ["orders"]
        });
        loadAgents(companyId);
      } else {
        toast({ title: "Error", description: data.error || "Could not create agent.", variant: "destructive" });
      }
    } catch (err) {
      toast({ title: "Error", description: "Failed to create agent.", variant: "destructive" });
    } finally {
      setIsCreatingAgent(false);
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/agent/companies/${companyId}/agents/${agentId}`, {
        method: "DELETE",
        headers: getHeaders(companyId)
      });
      if (res.ok) {
        toast({ title: "Agent Deleted", description: "Removed agent from workspace." });
        loadAgents(companyId);
      }
    } catch (err) {
      toast({ title: "Error", description: "Failed to delete agent.", variant: "destructive" });
    }
  };

  const copyWidgetScript = () => {
    const scriptTag = `<script src="${apiBaseUrl}/widget.js" data-company-id="${companyId}" data-agent-id="${selectedAgentId || 'agent_support_01'}" data-theme="${widgetTheme}" data-title="${widgetTitle}" async></script>`;
    navigator.clipboard.writeText(scriptTag);
    setCopiedScript(true);
    toast({ title: "Snippet Copied!", description: "Paste this code into any website before </body>." });
    setTimeout(() => setCopiedScript(false), 2500);
  };

  const refreshAll = (targetCompany = companyId) => {
    loadDocuments(targetCompany);
    loadAppointments(targetCompany);
    loadConversations(targetCompany);
    loadAnalytics(targetCompany);
    loadTelephony(targetCompany);
    loadDbConnector(targetCompany);
    loadAgents(targetCompany);
  };

  useEffect(() => {
    refreshAll(companyId);
  }, [companyId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Actions
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const validExtensions = [".pdf", ".txt", ".docx", ".csv"];
    const isValid = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!isValid) {
      toast({
        title: "Unsupported File Type",
        description: "Please upload a PDF, TXT, DOCX, or CSV file (<10MB).",
        variant: "destructive"
      });
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${companyId}/knowledge/upload`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer dev_token_${companyId}`,
          "X-Company-ID": companyId,
          "X-Test-User-Id": `user_${companyId}`,
        },
        body: formData
      });

      const data = await res.json();
      if (res.ok) {
        toast({
          title: "Document Ingested",
          description: `Indexed ${file.name} (${data.document?.chunk_count ?? 0} vector chunks).`
        });
        loadDocuments(companyId);
        loadAnalytics(companyId);
      } else {
        toast({
          title: "Upload Failed",
          description: data.error || "Failed to process document.",
          variant: "destructive"
        });
      }
    } catch (err: any) {
      toast({
        title: "Upload Error",
        description: err?.message || "Could not connect to backend server.",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const deleteFile = async (id: string, name: string) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${companyId}/knowledge/documents/${id}`, {
        method: "DELETE",
        headers: getHeaders()
      });

      if (res.ok) {
        toast({
          title: "Document Removed",
          description: `Deleted ${name} and purged vector chunks.`
        });
        loadDocuments(companyId);
        loadAnalytics(companyId);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const cancelAppointment = async (apptId: string) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${companyId}/appointments/${apptId}/cancel`, {
        method: "POST",
        headers: {
          ...getHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ reason: "Cancelled by company administrator." })
      });

      if (res.ok) {
        toast({
          title: "Appointment Cancelled",
          description: `Slot for appointment ${apptId} has been freed.`
        });
        loadAppointments(companyId);
        loadAnalytics(companyId);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRegisterPhone = async () => {
    if (!newPhoneNumber.trim()) return;
    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${companyId}/phone-numbers`, {
        method: "POST",
        headers: {
          ...getHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ phone_number: newPhoneNumber, label: newPhoneLabel })
      });
      if (res.ok) {
        toast({
          title: "Phone Connected",
          description: `Inbound calls to ${newPhoneNumber} will now route to ${companyId}.`
        });
        setNewPhoneNumber("");
        loadTelephony(companyId);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendTestChat = async (messageText?: string) => {
    const textToSend = messageText || chatInput;
    if (!textToSend.trim()) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: "user",
      content: textToSend
    };

    setChatMessages(prev => [...prev, userMsg]);
    if (!messageText) setChatInput("");
    setIsChatLoading(true);

    try {
      const res = await fetch(`${apiBaseUrl}/api/companies/${companyId}/agent/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getHeaders()
        },
        body: JSON.stringify({ message: textToSend })
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMsg: ChatMessage = {
          id: `ast_${Date.now()}`,
          role: "assistant",
          content: data.response || "Action completed.",
          sources: data.sources || [],
          tools: data.tool_calls || [],
          latency_ms: data.latency_ms
        };
        setChatMessages(prev => [...prev, assistantMsg]);
        // Refresh appointments if tool was used
        if (data.tool_calls && data.tool_calls.length > 0) {
          loadAppointments(companyId);
          loadAnalytics(companyId);
        }
      }
    } catch (err) {
      console.error("Chat error", err);
    } finally {
      setIsChatLoading(false);
    }
  };

  const formatTimestamp = (ts?: string) => {
    if (!ts) return "Recently";
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-3xl font-bold">Company Dashboard</h1>
                <Badge variant="outline" className="text-xs bg-primary/5 text-primary border-primary/20">
                  Enterprise SaaS
                </Badge>
              </div>
              <p className="text-muted-foreground mt-1">Manage your multi-tenant AI voice & knowledge platform</p>
            </div>
            
            {/* Tenant Selector */}
            <div className="flex items-center gap-2 bg-muted/60 p-2 rounded-lg border border-border">
              <Building2 className="h-4 w-4 text-primary" />
              <span className="text-xs font-semibold text-muted-foreground">Active Tenant:</span>
              <Input
                value={companyId}
                onChange={(e) => setCompanyId(e.target.value.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_'))}
                className="h-8 w-36 text-xs font-mono font-semibold bg-background"
                placeholder="company_id"
              />
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-8 px-2"
                onClick={() => refreshAll(companyId)}
                title="Refresh All Company Data"
              >
                <RefreshCw className={`h-4 w-4 ${isLoadingDocs ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="p-6">
              <div className="flex items-center space-x-4">
                <div className="p-2.5 bg-primary/10 rounded-lg text-primary">
                  <FileText className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{documents.length}</div>
                  <div className="text-xs text-muted-foreground">Indexed Documents</div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center space-x-4">
                <div className="p-2.5 bg-green-500/10 rounded-lg text-green-600">
                  <Calendar className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    {analytics?.appointments_scheduled ?? appointments.filter(a => a.status === "scheduled").length}
                  </div>
                  <div className="text-xs text-muted-foreground">Scheduled Appointments</div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center space-x-4">
                <div className="p-2.5 bg-blue-500/10 rounded-lg text-blue-600">
                  <PhoneIncoming className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{callLogs.length || phoneNumbers.length}</div>
                  <div className="text-xs text-muted-foreground">Telephony Calls / Lines</div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center space-x-4">
                <div className="p-2.5 bg-accent/10 rounded-lg text-accent">
                  <BarChart3 className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{analytics?.resolution_rate || "94%"}</div>
                  <div className="text-xs text-muted-foreground">Resolution Rate ({analytics?.avg_response_time || "1.8s"})</div>
                </div>
              </div>
            </Card>
          </div>

          {/* Navigation Tabs */}
          <Tabs defaultValue="agents" className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 h-auto p-1 gap-1">
              <TabsTrigger value="agents">
                <Bot className="h-3.5 w-3.5 mr-1" /> Agents
              </TabsTrigger>
              <TabsTrigger value="widget">
                <Code className="h-3.5 w-3.5 mr-1" /> Web Widget
              </TabsTrigger>
              <TabsTrigger value="knowledge">Knowledge</TabsTrigger>
              <TabsTrigger value="connectors">Database</TabsTrigger>
              <TabsTrigger value="appointments">Appointments</TabsTrigger>
              <TabsTrigger value="conversations">Inbox</TabsTrigger>
              <TabsTrigger value="telephony">Phone & Voice</TabsTrigger>
              <TabsTrigger value="test_agent" className="text-primary font-semibold">
                <Sparkles className="h-3.5 w-3.5 mr-1 text-primary" /> Test Agent
              </TabsTrigger>
            </TabsList>

            {/* Multi-Agent Studio Tab */}
            <TabsContent value="agents" className="space-y-6">
              <Card className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-border">
                  <div>
                    <h2 className="text-xl font-semibold">Multi-Agent Studio</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      Configure department-specific autonomous AI bots for sales, technical support, and scheduling.
                    </p>
                  </div>
                </div>

                {/* Agent Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  {agents.map((ag) => (
                    <div 
                      key={ag.agent_id}
                      className="p-5 rounded-xl border border-border bg-card shadow-soft hover:shadow-medium transition-all flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary font-bold text-lg">
                              🤖
                            </div>
                            <div>
                              <div className="font-bold text-foreground">{ag.agent_name}</div>
                              <div className="text-xs text-muted-foreground font-mono">{ag.agent_id}</div>
                            </div>
                          </div>
                          <Badge variant="secondary" className="bg-emerald-100 text-emerald-800 text-xs">
                            {ag.status || "active"}
                          </Badge>
                        </div>

                        <div className="space-y-2 text-xs mb-4">
                          <div>
                            <span className="font-semibold text-muted-foreground">Department / Role: </span>
                            <span className="text-foreground">{ag.role || "Customer Support"}</span>
                          </div>
                          <div>
                            <span className="font-semibold text-muted-foreground">Voice Model: </span>
                            <code className="bg-muted px-1.5 py-0.5 rounded text-foreground">{ag.voice_model || "en-US-JennyNeural"}</code>
                          </div>
                          <div>
                            <span className="font-semibold text-muted-foreground">Allowed DB Tables: </span>
                            <span className="text-foreground font-mono">{(ag.allowed_tables || ["orders"]).join(", ")}</span>
                          </div>
                          <div className="p-2.5 rounded-lg bg-muted/40 text-muted-foreground italic border border-border/40">
                            "{ag.greeting}"
                          </div>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-border flex justify-end">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="text-destructive hover:bg-destructive/10 text-xs h-8"
                          onClick={() => handleDeleteAgent(ag.agent_id)}
                          disabled={agents.length <= 1}
                        >
                          <Trash2 className="h-3.5 w-3.5 mr-1" /> Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Create Agent Form */}
                <div className="p-6 rounded-xl bg-muted/30 border border-border">
                  <h3 className="text-base font-bold text-foreground mb-4 flex items-center">
                    <Bot className="h-4 w-4 mr-2 text-primary" /> Create New AI Agent
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="text-xs font-semibold text-foreground mb-1 block">Agent Name</label>
                      <Input
                        placeholder="e.g. Maya - Inbound Sales"
                        value={newAgent.agent_name}
                        onChange={(e) => setNewAgent({ ...newAgent, agent_name: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-foreground mb-1 block">Role / Purpose</label>
                      <Input
                        placeholder="e.g. Lead Qualification & Pricing"
                        value={newAgent.role}
                        onChange={(e) => setNewAgent({ ...newAgent, role: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-foreground mb-1 block">Neural Voice Engine</label>
                      <Input
                        placeholder="en-US-JennyNeural, hi-IN-SwaraNeural, or ElevenLabs ID"
                        value={newAgent.voice_model}
                        onChange={(e) => setNewAgent({ ...newAgent, voice_model: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-foreground mb-1 block">Opening Greeting Message</label>
                      <Input
                        placeholder="Hello! Welcome to our sales desk. How can I help you today?"
                        value={newAgent.greeting}
                        onChange={(e) => setNewAgent({ ...newAgent, greeting: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="mb-4">
                    <label className="text-xs font-semibold text-foreground mb-1 block">Custom System Instructions & Tone</label>
                    <textarea
                      rows={3}
                      className="w-full bg-background border border-border rounded-lg p-2.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                      placeholder="You are an energetic sales representative. Recommend growth plans and guide visitors to schedule appointments..."
                      value={newAgent.system_instructions}
                      onChange={(e) => setNewAgent({ ...newAgent, system_instructions: e.target.value })}
                    />
                  </div>
                  <Button 
                    onClick={handleCreateAgent} 
                    disabled={isCreatingAgent || !newAgent.agent_name.trim()}
                    className="bg-primary text-white hover:bg-primary-hover shadow-soft"
                  >
                    {isCreatingAgent ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}
                    Deploy Agent to Workspace
                  </Button>
                </div>
              </Card>
            </TabsContent>

            {/* Embed Widget Generator Tab */}
            <TabsContent value="widget" className="space-y-6">
              <Card className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-border">
                  <div>
                    <h2 className="text-xl font-semibold">Embeddable Web Chat & Voice Widget</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      Add autonomous AI voice & text customer support to any website (Shopify, WordPress, Webflow, React) with one line of HTML.
                    </p>
                  </div>
                  <Button 
                    onClick={copyWidgetScript}
                    className="bg-primary text-white hover:bg-primary-hover shadow-soft"
                  >
                    {copiedScript ? <CheckCheck className="mr-2 h-4 w-4" /> : <Copy className="mr-2 h-4 w-4" />}
                    {copiedScript ? "Copied Snippet!" : "Copy Embed Code"}
                  </Button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Left: Customizer & Code Snippet */}
                  <div className="space-y-5">
                    <div>
                      <label className="text-xs font-semibold text-foreground mb-1 block">Active Agent to Handle Widget Calls</label>
                      <select 
                        value={selectedAgentId}
                        onChange={(e) => setSelectedAgentId(e.target.value)}
                        className="w-full bg-background border border-border rounded-lg p-2.5 text-sm"
                      >
                        {agents.map(a => (
                          <option key={a.agent_id} value={a.agent_id}>
                            {a.agent_name} ({a.role || 'Support'})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-foreground mb-1 block">Widget Title</label>
                        <Input 
                          value={widgetTitle}
                          onChange={(e) => setWidgetTitle(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-foreground mb-1 block">Theme Hex Color</label>
                        <div className="flex items-center gap-2">
                          <input 
                            type="color" 
                            value={widgetTheme}
                            onChange={(e) => setWidgetTheme(e.target.value)}
                            className="h-9 w-9 rounded border border-border cursor-pointer p-0.5 bg-background"
                          />
                          <Input 
                            value={widgetTheme}
                            onChange={(e) => setWidgetTheme(e.target.value)}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Syntax Highlighted Snippet Box */}
                    <div>
                      <label className="text-xs font-semibold text-foreground mb-1.5 block">
                        HTML Embed Code (Paste into your website right before <code className="text-primary font-mono">&lt;/body&gt;</code>):
                      </label>
                      <div className="relative bg-muted/80 rounded-xl p-4 font-mono text-xs border border-border text-foreground overflow-x-auto">
                        <pre className="whitespace-pre-wrap leading-relaxed">
{`<!-- VoxAide Autonomous Voice & Chat Widget -->
<script 
  src="${apiBaseUrl}/widget.js" 
  data-company-id="${companyId}" 
  data-agent-id="${selectedAgentId || 'agent_support_01'}"
  data-theme="${widgetTheme}"
  data-title="${widgetTitle}"
  async>
</script>`}
                        </pre>
                      </div>
                    </div>
                  </div>

                  {/* Right: Simulated Preview */}
                  <div className="p-6 rounded-2xl bg-muted/20 border border-border flex flex-col justify-between">
                    <div className="mb-4">
                      <div className="text-xs font-bold uppercase text-muted-foreground mb-1">Live Widget Simulator</div>
                      <div className="text-sm text-foreground">How your widget looks to visitors on your website:</div>
                    </div>

                    <div className="bg-card rounded-xl border border-border shadow-soft p-5 max-w-sm mx-auto w-full">
                      <div 
                        className="rounded-t-lg p-3 text-white flex items-center justify-between"
                        style={{ backgroundColor: widgetTheme }}
                      >
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-xs">🤖</div>
                          <div className="font-semibold text-xs">{widgetTitle}</div>
                        </div>
                        <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded">Online</span>
                      </div>
                      <div className="bg-muted/30 p-3 h-32 text-xs text-muted-foreground flex items-center justify-center border-x border-border">
                        "Hello! How can I help you today? You can speak or type your question."
                      </div>
                      <div className="p-2 border border-border rounded-b-lg bg-card flex gap-1">
                        <input 
                          disabled 
                          placeholder="Type or speak a question..." 
                          className="flex-1 bg-muted/40 rounded px-2 py-1 text-xs" 
                        />
                        <button 
                          className="px-2 py-1 rounded text-white text-xs font-bold"
                          style={{ backgroundColor: widgetTheme }}
                        >
                          ➤
                        </button>
                      </div>
                    </div>

                    <div className="text-center text-xs text-muted-foreground mt-4">
                      Supports Speech-to-Text & Neural Voice playback automatically.
                    </div>
                  </div>
                </div>
              </Card>
            </TabsContent>

            {/* 1. Knowledge Base Tab */}
            <TabsContent value="knowledge" className="space-y-6">
              <Card className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-xl font-semibold">Company Knowledge Base</h2>
                    <p className="text-sm text-muted-foreground">
                      Upload business documents (PDF, TXT, DOCX, CSV) strictly isolated under tenant <code className="text-primary font-mono">{companyId}</code>.
                    </p>
                  </div>
                  <div className="relative">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.txt,.docx,.csv"
                      onChange={handleFileUpload}
                      disabled={isUploading}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                    />
                    <Button variant="hero" disabled={isUploading}>
                      {isUploading ? (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                          Indexing...
                        </>
                      ) : (
                        <>
                          <Upload className="mr-2 h-4 w-4" />
                          Upload Document
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-3">
                  {documents.length === 0 ? (
                    <div className="text-center py-12 border border-dashed border-border rounded-lg bg-muted/20">
                      <FileText className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-40" />
                      <h3 className="font-medium text-foreground mb-1">No documents indexed yet</h3>
                      <p className="text-sm text-muted-foreground max-w-sm mx-auto mb-4">
                        Upload FAQs, pricing sheets, product catalogs, or service manuals to enable grounded AI responses.
                      </p>
                    </div>
                  ) : (
                    documents.map((file) => (
                      <div key={file.id} className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
                        <div className="flex items-center space-x-3 min-w-0">
                          <FileText className="h-6 w-6 text-primary" />
                          <div className="min-w-0">
                            <div className="font-medium truncate">{file.filename}</div>
                            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground mt-0.5">
                              <Badge variant="outline" className="uppercase font-mono text-[10px]">
                                {file.file_type}
                              </Badge>
                              <span>•</span>
                              <span>{file.chunk_count} vector chunks</span>
                              <span>•</span>
                              <span>Uploaded {formatTimestamp(file.uploaded_at)}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <Badge variant="secondary" className="bg-green-100 text-green-700">
                            {file.status}
                          </Badge>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            className="text-destructive hover:bg-destructive/10"
                            onClick={() => deleteFile(file.id, file.filename)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </Card>
            </TabsContent>

            {/* Database Connectors Tab */}
            <TabsContent value="connectors" className="space-y-6">
              <Card className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-border">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h2 className="text-xl font-semibold">PostgreSQL Database Connector</h2>
                      <Badge 
                        variant={dbStatus.connected ? "secondary" : "outline"} 
                        className={dbStatus.connected ? "bg-emerald-100 text-emerald-700" : "text-muted-foreground"}
                      >
                        {dbStatus.connected ? "Active & Connected" : "Not Connected"}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Allow your AI agents to answer customer inquiries by querying your PostgreSQL / Supabase database in real time.
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button 
                      variant="outline" 
                      onClick={handleTestDb} 
                      disabled={isTestingDb}
                    >
                      {isTestingDb ? (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                          Testing...
                        </>
                      ) : (
                        <>
                          <Link2 className="mr-2 h-4 w-4" />
                          Test Connection
                        </>
                      )}
                    </Button>
                    <Button 
                      className="bg-primary text-white hover:bg-primary-hover shadow-soft" 
                      onClick={handleSaveDb} 
                      disabled={isSavingDb}
                    >
                      {isSavingDb ? (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Check className="mr-2 h-4 w-4" />
                          Save Connector
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                {/* Security Banner */}
                <div className="mb-6 p-4 rounded-xl bg-accent/5 border border-accent/20 flex items-start space-x-3 text-xs sm:text-sm text-muted-foreground">
                  <ShieldCheck className="h-5 w-5 text-accent mt-0.5 shrink-0" />
                  <div>
                    <span className="font-semibold text-foreground">Zero-Modification Security Guarantee: </span>
                    All agent database queries are strictly executed in <code className="bg-muted px-1.5 py-0.5 rounded text-foreground font-mono">READ ONLY</code> transactions with a 3-second statement timeout. The AI cannot modify, insert, or delete any customer data.
                  </div>
                </div>

                {/* Connection Form Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="text-xs font-semibold text-foreground mb-1 block">Database Host</label>
                    <Input
                      placeholder="e.g. db.supabase.co or localhost"
                      value={dbConfig.host}
                      onChange={(e) => setDbConfig({ ...dbConfig, host: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-foreground mb-1 block">Port</label>
                    <Input
                      placeholder="5432"
                      value={dbConfig.port}
                      onChange={(e) => setDbConfig({ ...dbConfig, port: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-foreground mb-1 block">Database Name</label>
                    <Input
                      placeholder="e.g. ecommerce_db or postgres"
                      value={dbConfig.dbname}
                      onChange={(e) => setDbConfig({ ...dbConfig, dbname: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-foreground mb-1 block">Database User</label>
                    <Input
                      placeholder="postgres"
                      value={dbConfig.user}
                      onChange={(e) => setDbConfig({ ...dbConfig, user: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-foreground mb-1 block">Database Password</label>
                    <Input
                      type="password"
                      placeholder="••••••••••••"
                      value={dbConfig.password}
                      onChange={(e) => setDbConfig({ ...dbConfig, password: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-foreground mb-1 block">SSL Mode</label>
                    <Input
                      placeholder="prefer or require"
                      value={dbConfig.sslmode}
                      onChange={(e) => setDbConfig({ ...dbConfig, sslmode: e.target.value })}
                    />
                  </div>
                </div>

                {/* Allowed Tables Selection */}
                <div className="pt-4 border-t border-border">
                  <div className="mb-2">
                    <label className="text-xs font-semibold text-foreground block">
                      Allowed Tables for AI Agent Search (comma-separated):
                    </label>
                    <p className="text-xs text-muted-foreground">
                      The AI agent will only be granted permission to query tables listed here.
                    </p>
                  </div>
                  <Input
                    placeholder="orders, products, customers"
                    value={dbConfig.allowed_tables.join(", ")}
                    onChange={(e) => setDbConfig({
                      ...dbConfig,
                      allowed_tables: e.target.value.split(",").map(t => t.trim()).filter(Boolean)
                    })}
                    className="mb-3"
                  />

                  {/* Discovered Tables Badges */}
                  {dbStatus.tables && dbStatus.tables.length > 0 && (
                    <div>
                      <span className="text-xs text-muted-foreground block mb-1.5">
                        Discovered tables in database (click to toggle):
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {dbStatus.tables.map((t) => {
                          const isSelected = dbConfig.allowed_tables.includes(t);
                          return (
                            <button
                              key={t}
                              type="button"
                              onClick={() => {
                                const newTables = isSelected 
                                  ? dbConfig.allowed_tables.filter(tab => tab !== t)
                                  : [...dbConfig.allowed_tables, t];
                                setDbConfig({ ...dbConfig, allowed_tables: newTables });
                              }}
                              className={`text-xs px-2.5 py-1 rounded-md border font-mono transition-all ${
                                isSelected
                                  ? "bg-primary text-white border-primary"
                                  : "bg-muted text-muted-foreground border-border hover:text-foreground"
                              }`}
                            >
                              {isSelected ? `✓ ${t}` : `+ ${t}`}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            </TabsContent>

            {/* 2. Appointments Tab */}
            <TabsContent value="appointments" className="space-y-6">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold">Scheduled Appointments</h2>
                    <p className="text-sm text-muted-foreground">
                      Appointments booked autonomously by the AI Voice & Text agent for <code className="font-mono text-primary">{companyId}</code>.
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => loadAppointments(companyId)}>
                    <RefreshCw className="h-3.5 w-3.5 mr-1" /> Refresh
                  </Button>
                </div>

                {appointments.length === 0 ? (
                  <div className="text-center py-12 border border-dashed border-border rounded-lg bg-muted/20">
                    <Calendar className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-40" />
                    <h3 className="font-medium">No appointments scheduled yet</h3>
                    <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                      Customers can book appointments over the phone or in the chat playground.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border text-muted-foreground text-left">
                          <th className="py-3 font-medium">Customer</th>
                          <th className="py-3 font-medium">Contact Phone</th>
                          <th className="py-3 font-medium">Service</th>
                          <th className="py-3 font-medium">Date & Time</th>
                          <th className="py-3 font-medium">Status</th>
                          <th className="py-3 font-medium text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {appointments.map((appt) => (
                          <tr key={appt.id} className="border-b border-border hover:bg-muted/30">
                            <td className="py-3 font-medium">{appt.customer_name}</td>
                            <td className="py-3 font-mono text-xs">{appt.customer_phone}</td>
                            <td className="py-3">{appt.service}</td>
                            <td className="py-3">
                              <div className="flex items-center gap-1">
                                <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                                <span>{formatTimestamp(appt.start_time)}</span>
                              </div>
                            </td>
                            <td className="py-3">
                              <Badge 
                                variant="secondary" 
                                className={appt.status === "scheduled" ? "bg-green-100 text-green-700" : "bg-muted text-muted-foreground"}
                              >
                                {appt.status}
                              </Badge>
                            </td>
                            <td className="py-3 text-right">
                              {appt.status === "scheduled" && (
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  className="text-destructive text-xs hover:bg-destructive/10"
                                  onClick={() => cancelAppointment(appt.id)}
                                >
                                  Cancel
                                </Button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </TabsContent>

            {/* 3. Conversations Tab */}
            <TabsContent value="conversations" className="space-y-6">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold">Conversations & Caller Logs</h2>
                    <p className="text-sm text-muted-foreground">Turn-by-turn customer interaction history for {companyId}.</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => loadConversations(companyId)}>
                    <RefreshCw className="h-3.5 w-3.5 mr-1" /> Refresh
                  </Button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground text-left">
                        <th className="py-3 font-medium">Customer / User</th>
                        <th className="py-3 font-medium">Channel</th>
                        <th className="py-3 font-medium">First Query</th>
                        <th className="py-3 font-medium">Status</th>
                        <th className="py-3 font-medium">Date</th>
                        <th className="py-3 font-medium">Turns</th>
                      </tr>
                    </thead>
                    <tbody>
                      {conversations.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="text-center py-8 text-muted-foreground">
                            No conversations recorded yet.
                          </td>
                        </tr>
                      ) : (
                        conversations.map((conv) => (
                          <tr key={conv.id} className="border-b border-border hover:bg-muted/30">
                            <td className="py-3 font-medium">{conv.customer}</td>
                            <td className="py-3">
                              <Badge variant="outline" className="text-xs uppercase font-mono">
                                {conv.channel}
                              </Badge>
                            </td>
                            <td className="py-3 max-w-xs truncate">{conv.query}</td>
                            <td className="py-3">
                              <Badge variant="secondary" className="bg-green-100 text-green-700">
                                {conv.status}
                              </Badge>
                            </td>
                            <td className="py-3">{conv.date}</td>
                            <td className="py-3 text-muted-foreground">{conv.duration}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </Card>
            </TabsContent>

            {/* 4. Analytics Tab */}
            <TabsContent value="analytics" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Platform Performance</h3>
                  <div className="space-y-4 text-sm">
                    <div className="flex justify-between items-center py-1 border-b border-border">
                      <span>Total Inquiries Processed</span>
                      <span className="font-semibold">{analytics?.total_queries ?? 24}</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-border">
                      <span>Automated Resolution Rate</span>
                      <span className="font-semibold text-accent">{analytics?.resolution_rate ?? "94%"}</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-border">
                      <span>Average Response Latency</span>
                      <span className="font-semibold text-primary">{analytics?.avg_response_time ?? "1.8s"}</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-border">
                      <span>Appointments Booked via AI</span>
                      <span className="font-semibold text-green-600">{analytics?.appointments_scheduled ?? 3}</span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span>Escalated to Human</span>
                      <span className="font-semibold text-orange-500">{analytics?.escalations_count ?? 0}</span>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Query Topics Breakdown</h3>
                  <div className="space-y-4">
                    {(analytics?.categories || [
                      { category: "Appointments & Availability", percentage: 40 },
                      { category: "Company Information & FAQs", percentage: 35 },
                      { category: "Pricing & Service Policies", percentage: 15 },
                      { category: "General Support", percentage: 10 }
                    ]).map((cat, idx) => (
                      <div key={idx}>
                        <div className="flex justify-between text-xs mb-1">
                          <span>{cat.category}</span>
                          <span className="font-semibold">{cat.percentage}%</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div 
                            className="bg-primary h-2 rounded-full transition-all" 
                            style={{ width: `${cat.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </TabsContent>

            {/* 5. Telephony & Numbers Tab */}
            <TabsContent value="telephony" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="p-6 lg:col-span-1">
                  <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                    <Phone className="h-5 w-5 text-primary" /> Connect Phone Number
                  </h3>
                  <p className="text-xs text-muted-foreground mb-4">
                    Assign a virtual Twilio phone number to {companyId}. Incoming callers will be answered by your AI assistant.
                  </p>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Phone Number</label>
                      <Input
                        placeholder="+1 (415) 555-2671"
                        value={newPhoneNumber}
                        onChange={(e) => setNewPhoneNumber(e.target.value)}
                        className="mt-1 text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Label</label>
                      <Input
                        placeholder="Customer Service Line"
                        value={newPhoneLabel}
                        onChange={(e) => setNewPhoneLabel(e.target.value)}
                        className="mt-1 text-sm"
                      />
                    </div>
                    <Button className="w-full" onClick={handleRegisterPhone} disabled={!newPhoneNumber.trim()}>
                      Connect Number
                    </Button>
                  </div>

                  <div className="mt-6 p-3 bg-muted/60 rounded-lg text-xs space-y-1.5 border border-border">
                    <div className="font-semibold text-foreground">Twilio Webhook URL:</div>
                    <code className="text-[11px] block p-1.5 bg-background rounded border border-border break-all font-mono">
                      {apiBaseUrl}/api/telephony/voice/inbound?company_id={companyId}
                    </code>
                    <p className="text-muted-foreground text-[10px]">
                      Configure this as your Voice Webhook (POST) inside your Twilio Console.
                    </p>
                  </div>
                </Card>

                <Card className="p-6 lg:col-span-2">
                  <h3 className="text-lg font-semibold mb-4">Connected Lines & Call Logs</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                        Active Telephone Numbers ({phoneNumbers.length})
                      </h4>
                      {phoneNumbers.length === 0 ? (
                        <div className="text-xs text-muted-foreground p-3 border border-dashed rounded bg-muted/10">
                          No dedicated phone numbers connected yet. You can connect a Twilio number on the left.
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {phoneNumbers.map((num) => (
                            <div key={num.id} className="flex items-center justify-between p-3 border border-border rounded-lg bg-muted/20">
                              <div>
                                <div className="font-mono font-medium text-sm">{num.phone_number}</div>
                                <div className="text-xs text-muted-foreground">{num.label} • Provider: {num.provider}</div>
                              </div>
                              <Badge className="bg-green-100 text-green-700">Active</Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="pt-4 border-t border-border">
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                        Recent Inbound Calls ({callLogs.length})
                      </h4>
                      {callLogs.length === 0 ? (
                        <div className="text-xs text-muted-foreground p-4 text-center border border-dashed rounded bg-muted/10">
                          No calls received yet. Place a test call to your configured Twilio webhook.
                        </div>
                      ) : (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {callLogs.map((c) => (
                            <div key={c.call_sid} className="flex items-center justify-between p-2.5 border border-border rounded text-xs">
                              <div>
                                <div className="font-semibold">Caller: {c.from_number || "Anonymous"}</div>
                                <div className="text-muted-foreground text-[11px]">
                                  To: {c.to_number} • Duration: {c.duration_seconds}s • {formatTimestamp(c.created_at)}
                                </div>
                              </div>
                              <Badge variant="outline">{c.status}</Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              </div>
            </TabsContent>

            {/* 6. Test Agent Playground Tab */}
            <TabsContent value="test_agent" className="space-y-6">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                      <Bot className="h-5 w-5 text-primary" /> Test Agent Sandbox
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      Interact live with your multi-tenant assistant for <code className="text-primary font-mono">{companyId}</code>.
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => setChatMessages([])}>
                    Clear Chat
                  </Button>
                </div>

                {/* Quick Prompts */}
                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="text-xs text-muted-foreground self-center">Try:</span>
                  {[
                    "What are your business hours?",
                    "Can I check availability for tomorrow at 11 AM?",
                    "Book an appointment for John Doe (+15551234567) tomorrow at 11 AM",
                    "I want to speak with a human support manager"
                  ].map((chip, idx) => (
                    <Button 
                      key={idx} 
                      variant="outline" 
                      size="sm" 
                      className="text-xs h-7 px-2.5 rounded-full"
                      onClick={() => handleSendTestChat(chip)}
                      disabled={isChatLoading}
                    >
                      {chip}
                    </Button>
                  ))}
                </div>

                {/* Chat Message Box */}
                <div className="border border-border rounded-lg h-96 overflow-y-auto p-4 space-y-4 bg-muted/10 mb-4">
                  {chatMessages.map((msg) => (
                    <div 
                      key={msg.id} 
                      className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
                    >
                      <div 
                        className={`max-w-xl p-3.5 rounded-2xl text-sm leading-relaxed ${
                          msg.role === "user" 
                            ? "bg-primary text-primary-foreground rounded-br-none" 
                            : "bg-card border border-border rounded-bl-none shadow-sm"
                        }`}
                      >
                        {msg.content}
                      </div>

                      {/* Assistant Metadata: Sources & Tools */}
                      {msg.role === "assistant" && (msg.sources?.length || msg.tools?.length || msg.latency_ms) && (
                        <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground pl-1">
                          {msg.latency_ms && (
                            <span className="font-mono text-primary font-medium">⚡ {msg.latency_ms}ms</span>
                          )}
                          {msg.tools && msg.tools.map((t, idx) => (
                            <Badge key={idx} variant="secondary" className="text-[10px] font-mono bg-blue-100 text-blue-700">
                              Tool: {t.name}
                            </Badge>
                          ))}
                          {msg.sources && msg.sources.map((s, idx) => (
                            <Badge key={idx} variant="outline" className="text-[10px] border-primary/30">
                              Ref: {s.document_name} ({typeof s.relevance_score === 'number' ? s.relevance_score.toFixed(2) : s.relevance_score})
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}

                  {isChatLoading && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground pl-2">
                      <RefreshCw className="h-3.5 w-3.5 animate-spin text-primary" />
                      AI Agent is retrieving company knowledge and generating response...
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Input Bar */}
                <div className="flex gap-2">
                  <Input
                    placeholder="Type a query, question about services, or ask to book an appointment..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !isChatLoading && handleSendTestChat()}
                    disabled={isChatLoading}
                  />
                  <Button onClick={() => handleSendTestChat()} disabled={isChatLoading || !chatInput.trim()}>
                    <Send className="h-4 w-4 mr-1" /> Send
                  </Button>
                </div>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;