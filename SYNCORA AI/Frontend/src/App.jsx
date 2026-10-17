import React, { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { TopNav } from "./components/TopNav";
import { CreateTaskModal } from "./components/CreateTaskModal";
import { ReportBlockerModal } from "./components/ReportBlockerModal";
import { ReassignModal } from "./components/ReassignModal";
import { TaskDetailsModal } from "./components/TaskDetailsModal";

// Pages
import { LoginPage } from "./pages/LoginPage";
import { OverviewPage } from "./pages/OverviewPage";
import { TasksPage } from "./pages/TasksPage";
import { TeamPage } from "./pages/TeamPage";
import { AIActivityPage } from "./pages/AIActivityPage";
import { WorkloadPage } from "./pages/WorkloadPage";
import { MemberDashboardPage } from "./pages/MemberDashboardPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { IntegrationsPage } from "./pages/IntegrationsPage";
import { SettingsPage } from "./pages/SettingsPage";

// API Service
import { syncoraApi } from "./services/api";

// New Core Components (Phases 6 & 10)
import { AIChatbox } from "./components/AIChatbox";
import { DemoBar } from "./components/DemoBar";

export default function App() {
  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem("syncora_auth") === "true";
  });
  
  const [currentRole, setCurrentRole] = useState(() => {
    return localStorage.getItem("syncora_role") || "leader";
  });

  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem("syncora_user");
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.warn("User parse error:", e);
    }
    return {
      name: "Maya Chen",
      email: "maya.chen@novastudio.ai",
      role: "leader",
      title: "Team Leader",
      workspace: "Nova Studio",
    };
  });

  // Theme state: "light" | "dark" (Default: "light" mode as requested)
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("syncora_theme") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("syncora_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  const [activeNav, setActiveNav] = useState(() => {
    const role = localStorage.getItem("syncora_role") || "leader";
    return role === "member" ? "member-dashboard" : "overview";
  });

  // Data Stores
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({
    totalTasks: 48,
    completed: 21,
    inProgress: 12,
    pending: 8,
    blocked: 7,
  });
  const [members, setMembers] = useState([]);
  const [aiFeed, setAiFeed] = useState([]);
  const [aiMetrics, setAiMetrics] = useState({
    followUpsSent: 34,
    repliesReceived: 28,
    blockersDetected: 7,
    statusChanges: 19,
    clarifications: 4,
  });
  const [recommendations, setRecommendations] = useState([]);
  const [telegramSettings, setTelegramSettings] = useState({
    botName: "@SyncoraAIBot",
    botStatus: "Connected & Listening",
    webhookActive: true,
    linkedGroup: "Nova Studio Core Team (Telegram)",
    lastPing: "Just now",
    eventsHandledToday: 42,
  });

  // Modal States
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [isReportBlockerOpen, setIsReportBlockerOpen] = useState(false);
  const [activeReassignRec, setActiveReassignRec] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);

  // Search State
  const [searchQuery, setSearchQuery] = useState("");

  // Data loading & live background synchronization
  const refreshAllData = async () => {
    try {
      const [
        fetchedStats,
        fetchedTasks,
        fetchedMembers,
        fetchedFeed,
        fetchedMetrics,
        fetchedRecs,
        fetchedTg,
      ] = await Promise.all([
        syncoraApi.getOverviewStats(),
        syncoraApi.getTasks("All"),
        syncoraApi.getTeamMembers(),
        syncoraApi.getAIActivityFeed(),
        syncoraApi.getAICenterMetrics(),
        syncoraApi.getWorkloadRecommendations(),
        syncoraApi.getTelegramStatus(),
      ]);

      if (fetchedStats) setStats(fetchedStats);
      if (fetchedTasks) setTasks(fetchedTasks);
      if (fetchedMembers) setMembers(fetchedMembers);
      if (fetchedFeed) setAiFeed(fetchedFeed);
      if (fetchedMetrics) setAiMetrics(fetchedMetrics);
      if (fetchedRecs) setRecommendations(fetchedRecs);
      if (fetchedTg) setTelegramSettings(fetchedTg);
    } catch (err) {
      console.warn("Sync error:", err);
    }
  };

  useEffect(() => {
    refreshAllData();

    // 6-second live polling loop for two-way synchronization between Telegram and website
    const syncInterval = setInterval(() => {
      refreshAllData();
    }, 6000);

    return () => clearInterval(syncInterval);
  }, []);

  // Authentication Handlers
  const handleLoginSuccess = (user, role) => {
    const finalRole = role || user.role || "leader";
    const updatedUser = {
      ...user,
      role: finalRole,
      title: user.title || (finalRole === "leader" ? "Team Leader" : "Product Designer"),
      workspace: user.workspace || "Nova Studio",
    };
    setCurrentUser(updatedUser);
    setCurrentRole(finalRole);
    if (finalRole === "leader") {
      setActiveNav("overview");
    } else {
      setActiveNav("member-dashboard");
    }
    setIsAuthenticated(true);
    localStorage.setItem("syncora_auth", "true");
    localStorage.setItem("syncora_user", JSON.stringify(updatedUser));
    localStorage.setItem("syncora_role", finalRole);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem("syncora_auth");
  };

  // Switch between Leader and Member dashboards
  const toggleRole = () => {
    if (currentRole === "leader") {
      const memberUser = {
        name: "Alex Morgan",
        email: "alex.m@novastudio.ai",
        role: "member",
        title: "Product Designer",
        workspace: currentUser?.workspace || "Nova Studio",
      };
      setCurrentRole("member");
      setCurrentUser(memberUser);
      setActiveNav("member-dashboard");
      localStorage.setItem("syncora_role", "member");
      localStorage.setItem("syncora_user", JSON.stringify(memberUser));
    } else {
      const leaderUser = {
        name: "Maya Chen",
        email: "maya.chen@novastudio.ai",
        role: "leader",
        title: "Team Leader",
        workspace: currentUser?.workspace || "Nova Studio",
      };
      setCurrentRole("leader");
      setCurrentUser(leaderUser);
      setActiveNav("overview");
      localStorage.setItem("syncora_role", "leader");
      localStorage.setItem("syncora_user", JSON.stringify(leaderUser));
    }
  };

  // Handler for creating a new task
  const handleCreateTask = async (taskData) => {
    const created = await syncoraApi.createTask(taskData);
    setTasks((prev) => [created, ...prev]);
    // Refresh stats
    const updatedStats = await syncoraApi.getOverviewStats();
    setStats(updatedStats);
  };

  // Handler for reporting a blocker
  const handleReportBlocker = async (taskId, reason, urgency) => {
    await syncoraApi.reportBlocker(taskId, reason, urgency);
    const updatedTasks = await syncoraApi.getTasks("All");
    setTasks(updatedTasks);
    const updatedStats = await syncoraApi.getOverviewStats();
    setStats(updatedStats);
  };

  // Handler for updating a task status
  const handleUpdateTaskStatus = async (taskId, newStatus) => {
    await syncoraApi.updateTaskStatus(taskId, newStatus);
    const updatedTasks = await syncoraApi.getTasks("All");
    setTasks(updatedTasks);
    const updatedStats = await syncoraApi.getOverviewStats();
    setStats(updatedStats);
  };

  // Handler for approving a workload reassignment
  const handleApproveReassignment = async (recommendationId, note) => {
    await syncoraApi.approveReassignment(recommendationId);
    // Reload state
    const [updatedTasks, updatedRecs, updatedMembers] = await Promise.all([
      syncoraApi.getTasks("All"),
      syncoraApi.getWorkloadRecommendations(),
      syncoraApi.getTeamMembers(),
    ]);
    setTasks(updatedTasks);
    setRecommendations(updatedRecs);
    setMembers(updatedMembers);
  };

  // Calculate Header Title and Subtitle dynamically
  const getHeaderMeta = () => {
    if (currentRole === "member" && activeNav === "member-dashboard") {
      return {
        category: "COMMAND CENTER",
        title: `Good morning, ${currentUser?.name?.split(" ")[0] || "Alex"}`,
        subtitle: "Here's what's happening across your personal workflow today.",
      };
    }

    switch (activeNav) {
      case "overview":
        return {
          category: "COMMAND CENTER",
          title: `Good morning, ${currentUser?.name?.split(" ")[0] || "Maya"}`,
          subtitle: "Here's what's happening across your team today.",
        };
      case "tasks":
        return {
          category: "COMMAND CENTER",
          title: currentRole === "leader" ? "All Tasks" : "My Tasks",
          subtitle: "Plan, assign, and track work across every project.",
        };
      case "team":
        return {
          category: "COMMAND CENTER",
          title: "Team Management",
          subtitle: "Balance workloads and keep your people moving.",
        };
      case "ai-activity":
        return {
          category: "COMMAND CENTER",
          title: "AI Activity Center",
          subtitle: "See how Syncora is keeping work synchronized.",
        };
      case "workload":
        return {
          category: "COMMAND CENTER",
          title: "Invisible Workload Detector",
          subtitle: "AI-driven workload equilibrium and latent blocker forecasting.",
        };
      case "analytics":
        return {
          category: "COMMAND CENTER",
          title: "Sprint Analytics",
          subtitle: "Real-time task velocity and distribution breakdown.",
        };
      case "integrations":
        return {
          category: "COMMAND CENTER",
          title: "Telegram Integration",
          subtitle: "Manage bot sync, webhooks, and channel automation.",
        };
      case "settings":
        return {
          category: "COMMAND CENTER",
          title: "System Settings",
          subtitle: "Configure workspace preferences and backend API connection.",
        };
      default:
        return {
          category: "COMMAND CENTER",
          title: "Dashboard",
          subtitle: "Syncora AI Orchestrator",
        };
    }
  };

  // If not authenticated, show LoginPage
  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  const headerMeta = getHeaderMeta();

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        currentRole={currentRole}
        toggleRole={toggleRole}
        currentUser={currentUser}
        onLogout={handleLogout}
        onOpenCreateTask={() => setIsCreateTaskOpen(true)}
        onOpenReportBlocker={() => setIsReportBlockerOpen(true)}
      />

      {/* Main Content Area */}
      <main className="main-content">
        {/* Hackathon Demo Bar & Walkthrough Guide */}
        <DemoBar onResetSuccess={refreshAllData} />

        {/* Top Header */}
        <TopNav
          category={headerMeta.category}
          title={headerMeta.title}
          subtitle={headerMeta.subtitle}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          currentRole={currentRole}
          currentUser={currentUser}
          toggleRole={toggleRole}
          onLogout={handleLogout}
          theme={theme}
          toggleTheme={toggleTheme}
        />

        {/* Dynamic Route Content */}
        {activeNav === "overview" && (
          <OverviewPage
            stats={stats}
            tasks={tasks}
            teamMembers={members}
            aiFeed={aiFeed}
            currentUser={currentUser}
            onNavigateToTasks={() => setActiveNav("tasks")}
            onSelectTask={(task) => setSelectedTask(task)}
          />
        )}

        {activeNav === "tasks" && (
          <TasksPage
            tasks={tasks}
            onOpenCreateTask={() => setIsCreateTaskOpen(true)}
            onSelectTask={(task) => setSelectedTask(task)}
            currentRole={currentRole}
            globalSearch={searchQuery}
          />
        )}

        {activeNav === "team" && (
          <TeamPage members={members} inviteCode="NOVA-7X4K" currentUser={currentUser} />
        )}

        {activeNav === "ai-activity" && (
          <AIActivityPage metrics={aiMetrics} />
        )}

        {activeNav === "workload" && (
          <WorkloadPage
            recommendations={recommendations}
            members={members}
            onReviewReassignment={(rec) => setActiveReassignRec(rec)}
          />
        )}

        {activeNav === "member-dashboard" && (
          <MemberDashboardPage
            tasks={tasks}
            member={members.find((m) => m.name === "Alex Morgan")}
            currentUser={currentUser}
            onOpenReportBlocker={() => setIsReportBlockerOpen(true)}
            onSelectTask={(task) => setSelectedTask(task)}
          />
        )}

        {activeNav === "analytics" && (
          <AnalyticsPage stats={stats} tasks={tasks} />
        )}

        {activeNav === "integrations" && (
          <IntegrationsPage settings={telegramSettings} />
        )}

        {activeNav === "settings" && (
          <SettingsPage
            currentUser={currentUser}
            onLogout={handleLogout}
            onUpdateUser={(updated) => {
              setCurrentUser(updated);
              localStorage.setItem("syncora_user", JSON.stringify(updated));
            }}
          />
        )}
      </main>

      {/* Modals */}
      <CreateTaskModal
        isOpen={isCreateTaskOpen}
        onClose={() => setIsCreateTaskOpen(false)}
        onCreateTask={handleCreateTask}
        members={members}
      />

      <ReportBlockerModal
        isOpen={isReportBlockerOpen}
        onClose={() => setIsReportBlockerOpen(false)}
        tasks={tasks}
        onReportBlocker={handleReportBlocker}
      />

      <ReassignModal
        isOpen={Boolean(activeReassignRec)}
        onClose={() => setActiveReassignRec(null)}
        recommendation={activeReassignRec}
        onApprove={handleApproveReassignment}
        onReject={(recId) => {
          setRecommendations((prev) => prev.filter((r) => r.id !== recId));
        }}
      />

      <TaskDetailsModal
        isOpen={Boolean(selectedTask)}
        onClose={() => setSelectedTask(null)}
        task={selectedTask}
        onUpdateStatus={handleUpdateTaskStatus}
        onOpenReportBlocker={(task) => {
          setSelectedTask(null);
          setIsReportBlockerOpen(true);
        }}
        members={members}
      />

      {/* Floating Website AI Chatbox (Phase 6) */}
      <AIChatbox
        currentUser={currentUser}
        onTaskStatusUpdated={refreshAllData}
      />
    </div>
  );
}


