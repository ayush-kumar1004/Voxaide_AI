import { useState, useEffect } from "react";
import Navigation from "@/components/Navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { 
  Building2, 
  Users, 
  PhoneCall, 
  Bot, 
  ShieldCheck, 
  Search, 
  RefreshCw, 
  Database,
  Sparkles,
  ArrowUpRight
} from "lucide-react";
import { Link } from "react-router-dom";

interface TenantSummary {
  id: string;
  name: string;
  slug: string;
  industry: string;
  plan: string;
  agentsCount: number;
  callsCount: number;
  status: "active" | "suspended" | "trial";
  createdAt: string;
}

const SuperAdmin = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [tenants, setTenants] = useState<TenantSummary[]>([
    {
      id: "demo_company",
      name: "VoxAide Demo Enterprises",
      slug: "demo-company",
      industry: "Technology",
      plan: "Enterprise",
      agentsCount: 2,
      callsCount: 1420,
      status: "active",
      createdAt: "2026-08-02"
    },
    {
      id: "cmp_apex942",
      name: "Apex Logistics Global",
      slug: "apex-logistics",
      industry: "Logistics",
      plan: "Growth",
      agentsCount: 4,
      callsCount: 3890,
      status: "active",
      createdAt: "2026-09-14"
    },
    {
      id: "cmp_caremed",
      name: "CareMed Health Clinics",
      slug: "caremed-health",
      industry: "Healthcare",
      plan: "Starter",
      agentsCount: 1,
      callsCount: 430,
      status: "active",
      createdAt: "2026-10-21"
    }
  ]);

  const filteredTenants = tenants.filter(t => 
    t.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    t.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <div className="pt-20 pb-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold mb-2">
              <ShieldCheck className="h-3.5 w-3.5 mr-1" />
              VoxAide Internal Operations
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">Super Admin Platform Overview</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Global tenant directory, agent deployment statistics, and system telemetry.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/dashboard">
              <Button variant="outline">Open Tenant Dashboard</Button>
            </Link>
          </div>
        </div>

        {/* Global Key Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <Card className="p-5 shadow-soft border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase text-muted-foreground">Active Companies</span>
              <Building2 className="h-4 w-4 text-primary" />
            </div>
            <div className="text-3xl font-bold font-mono text-foreground">{tenants.length}</div>
            <div className="text-xs text-accent mt-1 flex items-center">
              <span>+100% tenant retention</span>
            </div>
          </Card>

          <Card className="p-5 shadow-soft border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase text-muted-foreground">Deployed AI Agents</span>
              <Bot className="h-4 w-4 text-purple-500" />
            </div>
            <div className="text-3xl font-bold font-mono text-foreground">
              {tenants.reduce((acc, t) => acc + t.agentsCount, 0)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Multi-department bots</div>
          </Card>

          <Card className="p-5 shadow-soft border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase text-muted-foreground">Total Calls Processed</span>
              <PhoneCall className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="text-3xl font-bold font-mono text-foreground">
              {tenants.reduce((acc, t) => acc + t.callsCount, 0).toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Phone & Web chats</div>
          </Card>

          <Card className="p-5 shadow-soft border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase text-muted-foreground">Platform Health</span>
              <Sparkles className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-3xl font-bold font-mono text-accent">99.98%</div>
            <div className="text-xs text-muted-foreground mt-1">Sub-300ms SLA active</div>
          </Card>
        </div>

        {/* Tenant Directory Table */}
        <Card className="p-6 shadow-soft border-border">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-lg font-bold text-foreground">Registered Tenant Workspaces</h2>
              <p className="text-xs text-muted-foreground">Direct access to tenant subscription plans and active agents.</p>
            </div>
            <div className="relative w-full sm:w-72">
              <Search className="h-4 w-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
              <Input
                placeholder="Search by company or industry..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 text-xs"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground text-left text-xs uppercase">
                  <th className="py-3 font-semibold">Company</th>
                  <th className="py-3 font-semibold">Industry</th>
                  <th className="py-3 font-semibold">Active Plan</th>
                  <th className="py-3 font-semibold text-center">Agents</th>
                  <th className="py-3 font-semibold text-right">Calls Handled</th>
                  <th className="py-3 font-semibold text-center">Status</th>
                  <th className="py-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredTenants.map((tenant) => (
                  <tr key={tenant.id} className="border-b border-border/60 hover:bg-muted/30 transition-colors">
                    <td className="py-3.5">
                      <div className="font-semibold text-foreground">{tenant.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{tenant.id}</div>
                    </td>
                    <td className="py-3.5 text-muted-foreground">{tenant.industry}</td>
                    <td className="py-3.5">
                      <Badge variant="outline" className="font-semibold">
                        {tenant.plan}
                      </Badge>
                    </td>
                    <td className="py-3.5 text-center font-mono font-bold text-primary">
                      {tenant.agentsCount}
                    </td>
                    <td className="py-3.5 text-right font-mono font-semibold">
                      {tenant.callsCount.toLocaleString()}
                    </td>
                    <td className="py-3.5 text-center">
                      <Badge variant="secondary" className="bg-emerald-100 text-emerald-800 text-[11px]">
                        {tenant.status}
                      </Badge>
                    </td>
                    <td className="py-3.5 text-right">
                      <Link to={`/dashboard`}>
                        <Button variant="ghost" size="sm" className="h-7 text-xs">
                          Inspect <ArrowUpRight className="h-3.5 w-3.5 ml-1" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SuperAdmin;
