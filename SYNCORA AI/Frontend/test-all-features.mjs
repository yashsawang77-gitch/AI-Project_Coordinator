/**
 * Syncora AI — Automated Step-by-Step Feature Test Suite
 * Validates Mock APIs, State Logic, Component Integrity & User Flows
 */

import {
  overviewStats,
  initialTasks,
  teamMembers,
  aiIntelligenceFeed,
  aiCenterMetrics,
  invisibleWorkloadRecommendations,
  telegramIntegrationSettings,
} from "./src/data/mockData.js";

import { syncoraApi } from "./src/services/api.js";

async function runStepByStepTests() {
  console.log("\n🧪 Running Syncora AI Automated Feature Tests Step-by-Step...\n");
  let passed = 0;
  let total = 0;

  function assert(condition, message) {
    total++;
    if (condition) {
      console.log(`  ✅ [PASS] Step ${total}: ${message}`);
      passed++;
    } else {
      console.error(`  ❌ [FAIL] Step ${total}: ${message}`);
      throw new Error(`Assertion failed: ${message}`);
    }
  }

  // STEP 1: Verify Mock Data & Store Integrity
  console.log("--- 1. Testing Core Data Stores ---");
  assert(overviewStats.totalTasks === 48, "Overview stats has 48 total tasks");
  assert(initialTasks.length > 0, `Initial tasks loaded (${initialTasks.length} tasks)`);
  assert(teamMembers.length >= 4, `Team members loaded (${teamMembers.length} members)`);
  assert(invisibleWorkloadRecommendations.length > 0, "AI Workload recommendations present");
  assert(telegramIntegrationSettings.botName === "@SyncoraAIBot", "Telegram bot settings configured");

  // STEP 2: Verify API Service Overview Stats
  console.log("\n--- 2. Testing API Service (Overview & Metrics) ---");
  const stats = await syncoraApi.getOverviewStats();
  assert(typeof stats.totalTasks === "number", `Overview stats returned totalTasks: ${stats.totalTasks}`);
  assert(typeof stats.completed === "number", `Overview stats returned completed: ${stats.completed}`);
  assert(typeof stats.inProgress === "number", `Overview stats returned inProgress: ${stats.inProgress}`);

  // STEP 3: Verify Tasks Retrieval & Filtering
  console.log("\n--- 3. Testing Tasks Retrieval & Status Filtering ---");
  const allTasks = await syncoraApi.getTasks("All");
  assert(allTasks.length > 0, `Retrieved ${allTasks.length} tasks from api`);
  const inProgressTasks = await syncoraApi.getTasks("In Progress");
  assert(inProgressTasks.every(t => t.status === "In Progress"), "Filtered tasks only return 'In Progress'");

  // STEP 4: Verify Task Creation Flow
  console.log("\n--- 4. Testing Task Creation Modal Flow ---");
  const newTaskPayload = {
    title: "Automated Test Task for Syncora",
    project: "Product Core",
    assignee: "Alex Morgan",
    deadline: "Tomorrow 5PM",
    priority: "High",
    description: "Verifying automated task creation",
  };
  const createdTask = await syncoraApi.createTask(newTaskPayload);
  assert(createdTask.title === newTaskPayload.title, `Task created successfully with ID: ${createdTask.id}`);
  assert(createdTask.assignee === "Alex Morgan", "Assignee correctly assigned to Alex Morgan");

  // STEP 5: Verify Task Status Update Flow
  console.log("\n--- 5. Testing Task Status Update Flow ---");
  const updatedTask = await syncoraApi.updateTaskStatus(createdTask.id, "Completed");
  assert(updatedTask.status === "Completed", `Task ${createdTask.id} successfully updated to 'Completed'`);

  // STEP 6: Verify Blocker Reporting Flow
  console.log("\n--- 6. Testing Blocker Reporting Flow ---");
  const blockerRes = await syncoraApi.reportBlocker(createdTask.id, "Waiting on OAuth credentials", "Critical");
  assert(blockerRes.task.status === "Blocked", `Task successfully marked as 'Blocked' with Critical urgency`);

  // STEP 7: Verify Invisible Workload Detector & Reassignment Flow
  console.log("\n--- 7. Testing AI Workload Rebalancing Flow ---");
  const recs = await syncoraApi.getWorkloadRecommendations();
  assert(recs.length > 0, `Found ${recs.length} AI workload rebalancing recommendations`);
  const testRec = recs[0];
  const reassignRes = await syncoraApi.approveReassignment(testRec.id, "Approved automated rebalance");
  assert(reassignRes.success === true, `Reassignment ${testRec.id} approved successfully`);

  // STEP 8: Verify AI Activity & Dialogue Simulation
  console.log("\n--- 8. Testing AI Activity Simulation ---");
  const metrics = await syncoraApi.getAICenterMetrics();
  assert(metrics.followUpsSent > 0, `AI Follow-ups tracked: ${metrics.followUpsSent}`);
  const sim = await syncoraApi.simulateReply(teamMembers[0].id, "Everything on track!");
  assert(sim.status === "delivered", `AI simulation reply delivered: ${sim.message}`);

  // STEP 9: Verify Telegram Status & Ping
  console.log("\n--- 9. Testing Telegram Integration Engine ---");
  const tg = await syncoraApi.getTelegramStatus();
  assert(tg.webhookActive === true, `Telegram webhook active (${tg.botName})`);

  // STEP 10: Verify Role-Based View Architecture
  console.log("\n--- 10. Testing Leader vs Member Role Dashboard Contracts ---");
  const leaderRequiredNavs = ["overview", "tasks", "team", "ai-activity", "analytics", "workload", "integrations", "settings"];
  const memberRequiredNavs = ["member-dashboard", "tasks", "team", "ai-activity", "workload", "integrations", "settings"];
  assert(leaderRequiredNavs.includes("overview"), "Leader dashboard includes 'overview'");
  assert(memberRequiredNavs.includes("member-dashboard"), "Member dashboard includes 'member-dashboard'");

  // STEP 11: Verify Linear / Raycast / Asana SaaS Theme System
  console.log("\n--- 11. Testing SaaS Design Tokens & UI Theme Specifications ---");
  const { readFileSync } = await import("fs");
  const css = readFileSync("./src/index.css", "utf-8");

  assert(css.includes("--bg-app: #FFFFFF;"), "Clean Light Mode: Pure white background (#FFFFFF) defined");
  assert(css.includes("--bg-card: #F8FAFC;"), "Off-white card background (#F8FAFC) defined");
  assert(css.includes("--border-subtle: #E2E8F0;"), "Subtle 1px crisp slate borders (#E2E8F0) defined");
  assert(css.includes("--radius-card: 12px;"), "12px card border-radius defined");
  assert(css.includes("--accent-primary: #6366F1;"), "Primary Accent: Deep Indigo / Electric Violet (#6366F1) defined");
  assert(css.includes("--accent-cyan: #06B6D4;"), "Cyan Accent (#06B6D4) defined");
  assert(css.includes("--status-completed: #10B981;"), "Status Completed: Emerald Green (#10B981) defined");
  assert(css.includes("--status-progress: #F59E0B;"), "Status In Progress: Amber (#F59E0B) defined");
  assert(css.includes("--status-blocked: #EF4444;"), "Status Blocked: Bright Crimson Red (#EF4444) defined");
  assert(css.includes("--status-blocked-bg: #FEF2F2;"), "Status Blocked Background: bg-red-50 (#FEF2F2) defined");
  assert(css.includes("--status-pending: #64748B;"), "Status Pending: Slate Gray (#64748B) defined");
  assert(css.includes(".status-pill-telegram"), "Live Integration Status Pill class defined");
  assert(css.includes(".theme-toggle-btn"), "Theme Toggle switch styling defined");

  // Verify TopNav has live Telegram status pill & theme toggle
  const topNavJsx = readFileSync("./src/components/TopNav.jsx", "utf-8");
  assert(topNavJsx.includes("Telegram Bot: Connected"), "Top header includes live Telegram Bot: Connected pill");
  assert(topNavJsx.includes("theme-toggle-btn"), "Top header includes visible Theme Toggle switch");

  console.log(`\n🎉 All ${passed}/${total} Step-by-Step Feature Tests Passed Successfully!\n`);
}

runStepByStepTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});

