import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  startWorkflow,
  getWorkflowState,
  resetWorkflow,
  setWeights,
  submitTasks,
  setConstraints,
  generateSchedule,
} from "./api";
import type { WorkflowResponse } from "./api";

describe("api", () => {
  const originalFetch = global.fetch;
  const mockResponse: WorkflowResponse = {
    state: {
      session_id: "test-123",
      phase: "weights",
      weights: null,
      raw_tasks: null,
      categorised_tasks: null,
      tasks_with_constraints: null,
      window_start: null,
      window_end: null,
      selected_algorithm: null,
      schedule: null,
    },
    message: "Success",
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe("startWorkflow", () => {
    it("should start a new workflow session", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await startWorkflow("test-123");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/workflow/start?session_id=test-123",
        { method: "POST" }
      );
      expect(result.state.session_id).toBe("test-123");
    });

    it("should throw error on failure", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      });

      await expect(startWorkflow("test")).rejects.toThrow("API error: 500");
    });
  });

  describe("getWorkflowState", () => {
    it("should fetch workflow state", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await getWorkflowState("test-123");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/workflow/state/test-123"
      );
      expect(result.state.session_id).toBe("test-123");
    });
  });

  describe("resetWorkflow", () => {
    it("should reset workflow", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await resetWorkflow("test-123");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/workflow/reset/test-123",
        { method: "POST" }
      );
    });
  });

  describe("setWeights", () => {
    it("should set utility weights", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await setWeights("test-123", { personal: 1.0, health: 2.0, work: 1.5 });

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/workflow/phase1/weights",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: "test-123",
            weights: { personal: 1.0, health: 2.0, work: 1.5 },
          }),
        }
      );
    });
  });

  describe("submitTasks", () => {
    it("should submit tasks for categorization", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await submitTasks("test-123", ["Go to gym", "Call mom"]);

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/workflow/phase2/tasks",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: "test-123",
            tasks: ["Go to gym", "Call mom"],
          }),
        }
      );
    });
  });

  describe("setConstraints", () => {
    it("should set task constraints", async () => {
      const tasks = [
        {
          id: "1",
          description: "Task",
          category: "Work",
          duration_minutes: 30,
          fixed_start_time: null,
        },
      ];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await setConstraints("test-123", tasks, "08:00", "18:00");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/workflow/phase3/constraints",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: "test-123",
            tasks,
            window_start: "08:00",
            window_end: "18:00",
          }),
        }
      );
    });
  });

  describe("generateSchedule", () => {
    it("should generate schedule", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await generateSchedule("test-123");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/workflow/phase4/schedule",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: "test-123" }),
        }
      );
    });
  });
});
