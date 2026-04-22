import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";
import * as api from "./api";

vi.mock("./api");

describe("App", () => {
  const mockStartWorkflow = vi.mocked(api.startWorkflow);

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("should render the title", async () => {
    mockStartWorkflow.mockResolvedValue({
      state: {
        session_id: "test",
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
      message: "Started",
    });

    render(<App />);

    expect(screen.getByText("Daily Schedule Planner")).toBeInTheDocument();
  });

  it("should show WeightsForm in weights phase", async () => {
    mockStartWorkflow.mockResolvedValue({
      state: {
        session_id: "test",
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
      message: "Set weights",
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Step 1/i)).toBeInTheDocument();
    });
  });

  it("should display error on API failure", async () => {
    mockStartWorkflow.mockRejectedValue(new Error("Network error"));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  it("should display progress indicator when state is loaded", async () => {
    mockStartWorkflow.mockResolvedValue({
      state: {
        session_id: "test",
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
      message: "Started",
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("1. Set Weights")).toBeInTheDocument();
    });
  });
});
