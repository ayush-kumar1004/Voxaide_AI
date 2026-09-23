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
  PhoneIncoming
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

  const refreshAll = (targetCompany = companyId) => {
    loadDocuments(targetCompany);
    loadAppointments(targetCompany);
    loadConversations(targetCompany);
    loadAnalytics(targetCompany);
    loadTelephony(targetCompany);
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
          <Tabs defaultValue="knowledge" className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 md:grid-cols-6 h-auto p-1">
              <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
              <TabsTrigger value="appointments">Appointments</TabsTrigger>
              <TabsTrigger value="conversations">Conversations</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="telephony">Phone & Voice</TabsTrigger>
              <TabsTrigger value="test_agent" className="text-primary font-semibold">
                <Sparkles className="h-3.5 w-3.5 mr-1 text-primary" /> Test Agent
              </TabsTrigger>
            </TabsList>

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