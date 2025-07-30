import { useState } from "react";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload, FileText, BarChart3, MessageSquare, Users, Settings, Download, Eye, Trash2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Dashboard = () => {
  const [uploadedFiles, setUploadedFiles] = useState([
    { id: 1, name: "company_faqs.txt", type: "FAQ", size: "15 KB", uploadDate: "2024-01-15" },
    { id: 2, name: "order_data.json", type: "Orders", size: "234 KB", uploadDate: "2024-01-14" },
    { id: 3, name: "policies.txt", type: "Policies", size: "45 KB", uploadDate: "2024-01-13" }
  ]);

  const [conversations] = useState([
    { id: 1, customer: "John Doe", query: "Order status for ZMT1003", status: "Resolved", date: "2024-01-15", duration: "2:34" },
    { id: 2, customer: "Sarah Smith", query: "Return policy question", status: "Resolved", date: "2024-01-15", duration: "1:45" },
    { id: 3, customer: "Mike Johnson", query: "Payment issue", status: "Escalated", date: "2024-01-15", duration: "5:12" }
  ]);

  const { toast } = useToast();

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const newFile = {
        id: Date.now(),
        name: file.name,
        type: file.name.includes('json') ? 'Orders' : file.name.includes('faq') ? 'FAQ' : 'Other',
        size: `${Math.round(file.size / 1024)} KB`,
        uploadDate: new Date().toISOString().split('T')[0]
      };
      setUploadedFiles(prev => [...prev, newFile]);
      toast({
        title: "File Uploaded",
        description: `${file.name} has been uploaded successfully.`
      });
    }
  };

  const deleteFile = (id: number) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== id));
    toast({
      title: "File Deleted",
      description: "File has been removed from your knowledge base."
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Company Dashboard</h1>
            <p className="text-muted-foreground">Manage your AI assistant and monitor customer interactions</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="p-6">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-primary-light rounded-lg">
                  <MessageSquare className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <div className="text-2xl font-bold">156</div>
                  <div className="text-sm text-muted-foreground">Total Queries</div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-accent-light rounded-lg">
                  <BarChart3 className="h-6 w-6 text-accent" />
                </div>
                <div>
                  <div className="text-2xl font-bold">94%</div>
                  <div className="text-sm text-muted-foreground">Resolution Rate</div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">89</div>
                  <div className="text-sm text-muted-foreground">Unique Customers</div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Settings className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">2.1s</div>
                  <div className="text-sm text-muted-foreground">Avg Response Time</div>
                </div>
              </div>
            </Card>
          </div>

          {/* Main Content */}
          <Tabs defaultValue="knowledge" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
              <TabsTrigger value="conversations">Conversations</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
            </TabsList>

            {/* Knowledge Base Tab */}
            <TabsContent value="knowledge">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold">Knowledge Base Management</h2>
                  <div className="relative">
                    <input
                      type="file"
                      accept=".txt,.json,.csv"
                      onChange={handleFileUpload}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <Button variant="hero">
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Files
                    </Button>
                  </div>
                </div>

                <div className="space-y-4">
                  {uploadedFiles.map((file) => (
                    <div key={file.id} className="flex items-center justify-between p-4 border border-border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <FileText className="h-8 w-8 text-primary" />
                        <div>
                          <div className="font-medium">{file.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {file.type} • {file.size} • Uploaded {file.uploadDate}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => deleteFile(file.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <h3 className="font-medium mb-2">Supported File Types</h3>
                  <p className="text-sm text-muted-foreground">
                    Upload your company data in TXT, JSON, or CSV format. Include FAQs, policies, order data, and knowledge articles.
                  </p>
                </div>
              </Card>
            </TabsContent>

            {/* Conversations Tab */}
            <TabsContent value="conversations">
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-6">Recent Conversations</h2>
                
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left py-3 font-medium">Customer</th>
                        <th className="text-left py-3 font-medium">Query</th>
                        <th className="text-left py-3 font-medium">Status</th>
                        <th className="text-left py-3 font-medium">Date</th>
                        <th className="text-left py-3 font-medium">Duration</th>
                        <th className="text-left py-3 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {conversations.map((conv) => (
                        <tr key={conv.id} className="border-b border-border">
                          <td className="py-3">{conv.customer}</td>
                          <td className="py-3 max-w-xs truncate">{conv.query}</td>
                          <td className="py-3">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              conv.status === 'Resolved' 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-orange-100 text-orange-700'
                            }`}>
                              {conv.status}
                            </span>
                          </td>
                          <td className="py-3">{conv.date}</td>
                          <td className="py-3">{conv.duration}</td>
                          <td className="py-3">
                            <Button variant="outline" size="sm">
                              View Details
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </TabsContent>

            {/* Analytics Tab */}
            <TabsContent value="analytics">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Resolution Analytics</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>Automated Resolutions</span>
                      <span className="font-semibold text-accent">94%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Escalated to Human</span>
                      <span className="font-semibold text-orange-500">6%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Average Response Time</span>
                      <span className="font-semibold text-primary">2.1s</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Customer Satisfaction</span>
                      <span className="font-semibold text-green-500">4.8/5</span>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Query Categories</h3>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Order Status</span>
                        <span>45%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div className="bg-primary h-2 rounded-full" style={{width: '45%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Returns & Refunds</span>
                        <span>30%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div className="bg-accent h-2 rounded-full" style={{width: '30%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Product Info</span>
                        <span>15%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div className="bg-orange-500 h-2 rounded-full" style={{width: '15%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Technical Support</span>
                        <span>10%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{width: '10%'}}></div>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;