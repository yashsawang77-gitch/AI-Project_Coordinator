/**
 * Syncora AI — Frontend API Service Client
 * 
 * BACKEND INTEGRATION SPECIFICATION:
 * Expected Endpoints for Backend Developer:
 * 
 * 1. GET  /api/dashboard/overview
 *    Response: { totalTasks, completed, inProgress, pending, blocked, trendRate }
 * 
 * 2. GET  /api/tasks?filter={all|in_progress|pending|blocked|completed}
 *    Response: Array of Task objects:
 *    [{ id, title, project, assignee, assigneeInitials, deadline, status, priority, estimatedHours, confidence }]
 * 
 * 3. POST /api/tasks
 *    Body: { title, project, assignee, deadline, priority, description }
 *    Response: Created Task object
 * 
 * 4. PATCH /api/tasks/:id/status
 *    Body: { status: "In Progress" | "Pending" | "Blocked" | "Completed", note?: string }
 *    Response: Updated Task object
 * 
 * 5. GET  /api/team/members
 *    Response: Array of TeamMember objects:
 *    [{ id, name, initials, role, title, activeTasks, completionRate, workload, workloadStatus, telegramHandle, online }]
 * 
 * 6. GET  /api/ai/activity-feed
 *    Response: Array of Activity objects
 * 
 * 7. GET  /api/ai/metrics
 *    Response: { followUpsSent, repliesReceived, blockersDetected, statusChanges, clarifications }
 * 
 * 8. POST /api/ai/simulate-reply
 *    Body: { memberId?: string, text?: string }
 *    Response: { step: number, status: string, message: string, timestamp: string }
 * 
 * 9. GET  /api/workload/invisible-detector
 *    Response: Array of WorkloadRecommendation objects:
 *    [{ id, priority, overburdenedMember, suggestedMember, taskToReassign, reasoning, actionProposed }]
 * 
 * 10. POST /api/workload/reassign
 *     Body: { recommendationId, approved: boolean, note?: string }
 *     Response: { success: boolean, message: string, updatedWorkload: object }
 * 
 * 11. POST /api/tasks/:id/report-blocker
 *     Body: { taskId, blockerReason, urgency: "High" | "Medium" | "Critical" }
 *     Response: { success: boolean, task: object }
 * 
 * 12. GET /api/integrations/telegram/status
 *     Response: { botName, botStatus, webhookActive, linkedGroup, lastPing, eventsHandledToday }
 */

import {
  overviewStats,
  initialTasks,
  teamMembers,
  aiIntelligenceFeed,
  aiCenterMetrics,
  invisibleWorkloadRecommendations,
  telegramIntegrationSettings,
} from "../data/mockData.js";

const API_BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  "http://localhost:8000/api";

// Local storage backup keys for rich persistence in demo mode
const STORAGE_KEYS = {
  TASKS: "syncora_tasks_cache",
  RECOMMENDATIONS: "syncora_recs_cache",
  FEED: "syncora_feed_cache",
};

// Memory fallback store for environments without window.localStorage
const memoryStorage = {};

const safeStorage = {
  getItem(key) {
    if (typeof localStorage !== "undefined") {
      return localStorage.getItem(key);
    }
    return memoryStorage[key] || null;
  },
  setItem(key, val) {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(key, val);
    } else {
      memoryStorage[key] = val;
    }
  },
};

const getStoredTasks = () => {
  try {
    const raw = safeStorage.getItem(STORAGE_KEYS.TASKS);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.warn("Storage read error:", e);
  }
  return initialTasks;
};

const saveStoredTasks = (tasks) => {
  try {
    safeStorage.setItem(STORAGE_KEYS.TASKS, JSON.stringify(tasks));
  } catch (e) {
    console.warn("Storage write error:", e);
  }
};

/**
 * Generic fetch wrapper with fallback to labeled mock data
 */
async function apiRequest(endpoint, options = {}, mockFallbackFn) {
  try {
    const token = safeStorage.getItem("syncora_token");
    const headers = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMsg = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
          errorMsg = errorData.detail;
        }
      } catch (e) {
        // use default
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (error) {
    // Graceful fallback to mock data if backend server is not running
    if (mockFallbackFn) {
      return await mockFallbackFn();
    }
    throw error;
  }
}

// Simulated network delay helper to show genuine loading states
const delay = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms));

export const syncoraApi = {
  // 1. Dashboard Overview Stats
  async getOverviewStats() {
    return apiRequest("/dashboard/overview", {}, async () => {
      await delay(120);
      const tasks = getStoredTasks();
      const completed = tasks.filter((t) => t.status === "Completed").length;
      const inProgress = tasks.filter((t) => t.status === "In Progress").length;
      const pending = tasks.filter((t) => t.status === "Pending").length;
      const blocked = tasks.filter((t) => t.status === "Blocked").length;
      const total = tasks.length;

      return {
        ...overviewStats,
        totalTasks: total,
        completed,
        inProgress,
        pending,
        blocked,
      };
    });
  },

  // 2. Fetch Tasks with filtering
  async getTasks(filter = "All") {
    return apiRequest(`/tasks?filter=${encodeURIComponent(filter)}`, {}, async () => {
      await delay(150);
      const tasks = getStoredTasks();
      if (!filter || filter === "All") return tasks;
      return tasks.filter((t) => t.status.toLowerCase() === filter.toLowerCase());
    });
  },

  // 3. Create Task
  async createTask(newTaskData) {
    return apiRequest(
      "/tasks",
      {
        method: "POST",
        body: JSON.stringify(newTaskData),
      },
      async () => {
        await delay(200);
        const tasks = getStoredTasks();
        const created = {
          id: `SYNC-${Math.floor(210 + Math.random() * 90)}`,
          title: newTaskData.title,
          project: newTaskData.project || "Product Core",
          assignee: newTaskData.assignee || "Maya Chen",
          assigneeInitials: (newTaskData.assignee || "MC")
            .split(" ")
            .map((n) => n[0])
            .join(""),
          assigneeBg: "#18e5b4",
          assigneeTextColor: "#090d16",
          deadline: newTaskData.deadline || "Tomorrow",
          deadlineStatus: "upcoming",
          status: newTaskData.status || "In Progress",
          priority: newTaskData.priority || "High",
          leftBarColor: newTaskData.priority === "Critical" ? "#f43f5e" : "#18e5b4",
          estimatedHours: newTaskData.estimatedHours || "6-10h",
          confidence: "90%",
          description: newTaskData.description || "",
        };

        const updated = [created, ...tasks];
        saveStoredTasks(updated);
        return created;
      }
    );
  },

  // 4. Update Task Status
  async updateTaskStatus(taskId, status) {
    return apiRequest(
      `/tasks/${taskId}/status`,
      {
        method: "PATCH",
        body: JSON.stringify({ status }),
      },
      async () => {
        await delay(150);
        const tasks = getStoredTasks();
        const updated = tasks.map((t) => (t.id === taskId ? { ...t, status } : t));
        saveStoredTasks(updated);
        return updated.find((t) => t.id === taskId);
      }
    );
  },

  // 5. Team Members
  async getTeamMembers() {
    return apiRequest("/team/members", {}, async () => {
      await delay(120);
      return teamMembers;
    });
  },

  // 6. AI Intelligence Feed
  async getAIActivityFeed() {
    return apiRequest("/ai/activity-feed", {}, async () => {
      await delay(100);
      return aiIntelligenceFeed;
    });
  },

  // 7. AI Metrics
  async getAICenterMetrics() {
    return apiRequest("/ai/metrics", {}, async () => {
      await delay(100);
      return aiCenterMetrics;
    });
  },

  // 8. Invisible Workload Recommendations
  async getWorkloadRecommendations() {
    return apiRequest("/workload/invisible-detector", {}, async () => {
      await delay(150);
      try {
        const stored = safeStorage.getItem(STORAGE_KEYS.RECOMMENDATIONS);
        if (stored) return JSON.parse(stored);
      } catch (e) {
        // fallback
      }
      return invisibleWorkloadRecommendations;
    });
  },

  // 8b. Simulate AI Reply / Follow-up parsing
  async simulateReply(memberId, text) {
    return apiRequest(
      "/ai/simulate-reply",
      {
        method: "POST",
        body: JSON.stringify({ memberId, text }),
      },
      async () => {
        await delay(120);
        return {
          step: 4,
          status: "delivered",
          message: text || "Update parsed and team ledger synchronized.",
          timestamp: new Date().toLocaleTimeString(),
        };
      }
    );
  },

  // 8c. In-App AI Chat
  async sendAIChat(memberId, message, taskId = null) {
    return apiRequest(
      "/ai/chat",
      {
        method: "POST",
        body: JSON.stringify({ memberId, message, taskId }),
      },
      async () => {
        await delay(250);
        return {
          reply: `✓ Evidence recognized: Captured note. Syncora updated team pulse automatically.`,
          interpretation: {
            confidence: "92%",
            summary: "Update parsed and recorded",
          },
          updatedTask: null,
          blockerAlert: false,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
      }
    );
  },


  // 9. Reassign Task with Leader Approval
  async approveReassignment(recommendationId) {
    return apiRequest(
      "/workload/reassign",
      {
        method: "POST",
        body: JSON.stringify({ recommendationId, approved: true }),
      },
      async () => {
        await delay(250);
        const recs = await syncoraApi.getWorkloadRecommendations();
        const targetRec = recs.find((r) => r.id === recommendationId);

        if (targetRec) {
          // Reassign task in store
          const tasks = getStoredTasks();
          const updatedTasks = tasks.map((t) => {
            if (t.id === targetRec.taskToReassign.id) {
              return {
                ...t,
                assignee: targetRec.suggestedMember,
                assigneeInitials: targetRec.suggestedMember
                  .split(" ")
                  .map((n) => n[0])
                  .join(""),
                status: "In Progress",
              };
            }
            return t;
          });
          saveStoredTasks(updatedTasks);

          // Mark recommendation as resolved
          const remainingRecs = recs.filter((r) => r.id !== recommendationId);
          safeStorage.setItem(STORAGE_KEYS.RECOMMENDATIONS, JSON.stringify(remainingRecs));
        }

        return { success: true, message: "Task successfully balanced & reassigned." };
      }
    );
  },

  // 9b. Deterministic Workload Analysis & Risk Detection
  async getTeamWorkloadAnalysis(windowDays = 7) {
    return apiRequest(`/workload/analysis?windowDays=${windowDays}`, {}, async () => {
      await delay(150);
      return {
        analysisWindowDays: windowDays,
        memberMetrics: [],
        confirmedRisks: [],
        potentialRisks: [],
        aiGeneratedEstimates: [],
        recommendations: invisibleWorkloadRecommendations,
        equilibriumSummary: "Deterministic analysis loaded.",
      };
    });
  },

  // 9c. AI-Assisted Effort Estimation
  async estimateTaskEffort(taskData) {
    return apiRequest(
      "/workload/estimate-effort",
      {
        method: "POST",
        body: JSON.stringify(taskData),
      },
      async () => {
        await delay(200);
        return {
          title: taskData.title,
          minEstimatedHours: 6.0,
          maxEstimatedHours: 12.0,
          estimatedHoursDisplay: "6-12h",
          assumptions: ["Based on component scope."],
          confidenceLevel: "Medium",
          informationNeeded: [],
          isAiEstimate: true,
        };
      }
    );
  },

  // 10. Report Blocker (Member action)
  async reportBlocker(taskId, blockerReason, urgency = "Critical") {
    return apiRequest(
      `/tasks/${taskId}/report-blocker`,
      {
        method: "POST",
        body: JSON.stringify({ taskId, blockerReason, urgency }),
      },
      async () => {
        await delay(200);
        const tasks = getStoredTasks();
        const updatedTasks = tasks.map((t) => {
          if (t.id === taskId) {
            return {
              ...t,
              status: "Blocked",
              blockerReason,
              leftBarColor: "#f43f5e",
            };
          }
          return t;
        });
        saveStoredTasks(updatedTasks);
        const updatedTask = updatedTasks.find((t) => t.id === taskId);
        return {
          success: true,
          task: updatedTask,
          message: "Blocker reported and team alerted via Telegram bot.",
        };
      }
    );
  },

  // 11. Telegram Settings & Bot Status
  async getTelegramStatus() {
    return apiRequest("/integrations/telegram/status", {}, async () => {
      await delay(100);
      return telegramIntegrationSettings;
    });
  },

  // 12. Authentication Methods
  async login(email, password, role = "leader") {
    const res = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, role }),
    }, async () => {
      await delay(150);
      const isLeader = role === "leader" || email.toLowerCase().includes("maya") || email.toLowerCase().includes("lead");
      const user = {
        id: isLeader ? "mem-1" : "mem-2",
        name: isLeader ? "Maya Chen" : "Alex Morgan",
        email: email,
        role: isLeader ? "leader" : "member",
        title: isLeader ? "Team Leader" : "Product Designer",
        workspace: "Nova Studio",
        isPhoneVerified: false,
        telegramConnected: false,
      };
      return {
        token: `syncora-jwt-${user.id}-${isLeader ? 1 : 0}`,
        user,
        message: "Demo fallback login successful."
      };
    });
    if (res && res.token) {
      safeStorage.setItem("syncora_token", res.token);
    }
    return res;
  },

  async register(data) {
    const res = await apiRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }, async () => {
      await delay(150);
      const isLeader = data.role === "Team Leader";
      const user = {
        id: `mem-${Date.now()}`,
        name: data.name,
        email: data.email,
        role: isLeader ? "leader" : "member",
        title: data.title || (isLeader ? "Team Leader" : "Team Member"),
        workspace: data.workspace || "Nova Studio",
        isPhoneVerified: false,
        telegramConnected: false,
      };
      return {
        token: `syncora-jwt-${user.id}-0`,
        user,
        message: "Registration successful."
      };
    });
    if (res && res.token) {
      safeStorage.setItem("syncora_token", res.token);
    }
    return res;
  },

  async forgotPassword(email) {
    return apiRequest("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }, async () => {
      await delay(150);
      return {
        success: true,
        resetToken: "DEMO-RESET-9876",
        message: "Password reset token generated: DEMO-RESET-9876"
      };
    });
  },

  async resetPassword(data) {
    return apiRequest("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify(data),
    }, async () => {
      await delay(150);
      return {
        success: true,
        message: "Password updated successfully."
      };
    });
  },

  async getMe() {
    return apiRequest("/auth/me", {}, async () => {
      await delay(100);
      return null;
    });
  },

  async updateProfile(updates) {
    return apiRequest("/auth/profile", {
      method: "PATCH",
      body: JSON.stringify(updates),
    }, async () => {
      await delay(120);
      return updates;
    });
  },

  // 13. Phone Number OTP Verification Methods
  async sendPhoneOtp(phoneNumber, countryCode = "+91") {
    return apiRequest("/auth/phone/send-otp", {
      method: "POST",
      body: JSON.stringify({ phoneNumber, countryCode }),
    }, async () => {
      await delay(200);
      return {
        success: true,
        phoneNumber,
        message: `Sandbox Demo: Verification OTP sent to ${phoneNumber}.`,
        expiresInSeconds: 300,
        provider: "dev",
        isDemoSandbox: true,
        sandboxOtp: "482910"
      };
    });
  },

  async verifyPhoneOtp(phoneNumber, otp) {
    return apiRequest("/auth/phone/verify-otp", {
      method: "POST",
      body: JSON.stringify({ phoneNumber, otp }),
    }, async () => {
      await delay(200);
      return {
        success: true,
        verified: true,
        phoneNumber,
        message: "Phone number verified successfully!",
        verifiedAt: new Date().toISOString()
      };
    });
  },

  async changePhoneNumber(newPhoneNumber = null) {
    return apiRequest("/auth/phone/change-number", {
      method: "POST",
      body: JSON.stringify({ newPhoneNumber }),
    }, async () => {
      await delay(150);
      return {
        success: true,
        message: "Phone number cleared. Please verify your new number."
      };
    });
  },

  async getPhoneStatus() {
    return apiRequest("/auth/phone/status", {}, async () => {
      await delay(100);
      return {
        phoneNumber: null,
        isVerified: false,
        verifiedAt: null,
        provider: "dev",
        providerConfigured: true
      };
    });
  },

  // 14. Telegram Deep Linking & Disconnect
  async getTelegramLinkToken() {
    return apiRequest("/integrations/telegram/link-token", {
      method: "POST",
    }, async () => {
      await delay(150);
      return {
        token: "SYNC_DEMO_LINK_TOKEN_12345",
        deepLink: "https://t.me/Syncoraaivalidbot?start=SYNC_DEMO_LINK_TOKEN_12345",
        botUsername: "@Syncoraaivalidbot",
        expiresAt: "In 10 minutes",
        instructions: "Tap the link to open Telegram and press Start."
      };
    });
  },

  async disconnectTelegram() {
    return apiRequest("/integrations/telegram/disconnect", {
      method: "POST",
    }, async () => {
      await delay(150);
      return {
        success: true,
        message: "Telegram account disconnected successfully."
      };
    });
  },

  // 15. AI Chat History
  async getAIChatHistory(memberId = "mem-1") {
    return apiRequest(`/ai/chat/history?memberId=${encodeURIComponent(memberId)}`, {}, async () => {
      await delay(100);
      return [];
    });
  },

  async clearAIChatHistory(memberId = "mem-1") {
    return apiRequest(`/ai/chat/history?memberId=${encodeURIComponent(memberId)}`, {
      method: "DELETE",
    }, async () => {
      await delay(100);
      return { success: true };
    });
  },

  // 16. Demo Mode Controls
  async resetDemoData() {
    return apiRequest("/demo/reset", {
      method: "POST",
    }, async () => {
      await delay(200);
      return {
        success: true,
        message: "Demo data reset successfully."
      };
    });
  },

  async getDemoState() {
    return apiRequest("/demo/state", {}, async () => {
      await delay(120);
      return null;
    });
  },
};

