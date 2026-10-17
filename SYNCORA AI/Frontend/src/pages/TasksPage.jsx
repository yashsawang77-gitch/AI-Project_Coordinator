import React, { useState } from "react";
import { Search, Plus, Filter } from "lucide-react";
import { TaskRow } from "../components/TaskRow";

export function TasksPage({
  tasks = [],
  onOpenCreateTask,
  onSelectTask,
  currentRole = "leader",
  globalSearch = "",
}) {
  const [filter, setFilter] = useState("All");
  const [taskSearch, setTaskSearch] = useState("");
  const [memberOnlyFilter, setMemberOnlyFilter] = useState(currentRole === "member");

  const filterTabs = ["All", "In Progress", "Pending", "Blocked", "Completed"];

  // Filter tasks based on selected tab, search query, and member filter
  const effectiveSearch = (taskSearch || globalSearch || "").trim().toLowerCase();

  const filteredTasks = (tasks || []).filter((task) => {
    if (memberOnlyFilter && task.assignee !== "Alex Morgan") {
      return false;
    }

    const matchesFilter =
      filter === "All" || task.status.toLowerCase() === filter.toLowerCase();

    const matchesSearch =
      !effectiveSearch ||
      task.title.toLowerCase().includes(effectiveSearch) ||
      task.project.toLowerCase().includes(effectiveSearch) ||
      task.id.toLowerCase().includes(effectiveSearch) ||
      task.assignee.toLowerCase().includes(effectiveSearch);

    return matchesFilter && matchesSearch;
  });

  return (
    <div>
      {/* Search, Filter Tabs & Create Task Action Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "20px",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px", flex: 1 }}>
          {/* Search Tasks Input */}
          <div
            className="search-input-box"
            style={{ width: "240px", backgroundColor: "var(--bg-app)" }}
          >
            <Search size={16} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={taskSearch}
              onChange={(e) => setTaskSearch(e.target.value)}
            />
          </div>

          {/* Filter Tabs */}
          <div className="filter-tabs-bar">
            {filterTabs.map((tab) => (
              <button
                key={tab}
                type="button"
                className={`filter-tab ${filter === tab ? "active" : ""}`}
                onClick={() => setFilter(tab)}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Member Scope Toggle */}
          {currentRole === "member" && (
            <div style={{ display: "flex", gap: "4px", backgroundColor: "var(--bg-app)", padding: "3px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
              <button
                type="button"
                className={`filter-tab ${memberOnlyFilter ? "active" : ""}`}
                style={{ padding: "4px 10px", fontSize: "12px" }}
                onClick={() => setMemberOnlyFilter(true)}
              >
                My Tasks
              </button>
              <button
                type="button"
                className={`filter-tab ${!memberOnlyFilter ? "active" : ""}`}
                style={{ padding: "4px 10px", fontSize: "12px" }}
                onClick={() => setMemberOnlyFilter(false)}
              >
                All Tasks
              </button>
            </div>
          )}
        </div>

        {/* Create Task Button */}
        <button
          type="button"
          className="btn-primary"
          onClick={onOpenCreateTask}
        >
          <Plus size={18} />
          Create task
        </button>
      </div>

      {/* Tasks Table Container Card */}
      <div className="tasks-container-card">
        {/* Table Header Row */}
        <div className="table-header-row">
          <div>TASK</div>
          <div>ASSIGNEE</div>
          <div>DEADLINE</div>
          <div>STATUS</div>
          <div></div>
        </div>

        {/* Task Rows */}
        {filteredTasks.length === 0 ? (
          <div
            style={{
              padding: "48px 24px",
              textAlign: "center",
              color: "#94a3b8",
              fontSize: "16px",
            }}
          >
            No tasks found matching filter "{filter}".
          </div>
        ) : (
          filteredTasks.map((task) => (
            <TaskRow
              key={task.id}
              task={task}
              onClick={() => onSelectTask && onSelectTask(task)}
            />
          ))
        )}
      </div>
    </div>
  );
}

