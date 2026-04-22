import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskInput } from "./TaskInput";

describe("TaskInput", () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("should render the form elements", () => {
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    expect(screen.getByText("Step 2: Enter Your Tasks")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("should update textarea value when user types", async () => {
    const user = userEvent.setup();
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "Go to gym");

    expect(textarea).toHaveValue("Go to gym");
  });

  it("should have disabled button when input is empty", () => {
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    const submitButton = screen.getByRole("button");
    expect(submitButton).toBeDisabled();
  });

  it("should have disabled button when loading", async () => {
    const user = userEvent.setup();
    render(<TaskInput onSubmit={mockOnSubmit} loading={true} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "Go to gym");

    const submitButton = screen.getByRole("button");
    expect(submitButton).toBeDisabled();
  });

  it("should not call onSubmit when input is empty", async () => {
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    // Force click even if disabled
    const form = document.querySelector("form")!;
    form.dispatchEvent(new Event("submit", { bubbles: true }));

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("should not call onSubmit when input contains only whitespace", async () => {
    const user = userEvent.setup();
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "   \n   \n   ");
    await user.clear(textarea);
    await user.type(textarea, "   ");

    // Button should still be disabled
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("should call onSubmit with parsed tasks on submit", async () => {
    const user = userEvent.setup();
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "Go to gym\nCall mom");

    const submitButton = screen.getByRole("button");
    await user.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalledWith(["Go to gym", "Call mom"]);
  });

  it("should display loading state while submitting", () => {
    render(<TaskInput onSubmit={mockOnSubmit} loading={true} />);

    expect(screen.getByRole("button")).toHaveTextContent("Categorizing...");
  });

  it("should display normal text when not loading", async () => {
    const user = userEvent.setup();
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "Task");

    expect(screen.getByRole("button")).toHaveTextContent(
      "Categorize Tasks & Continue"
    );
  });

  it("should trim whitespace from tasks", async () => {
    const user = userEvent.setup();
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "  Go to gym  \n  Call mom  ");

    const submitButton = screen.getByRole("button");
    await user.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalledWith(["Go to gym", "Call mom"]);
  });

  it("should filter out empty lines", async () => {
    const user = userEvent.setup();
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "Go to gym\n\n\nCall mom\n\n");

    const submitButton = screen.getByRole("button");
    await user.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalledWith(["Go to gym", "Call mom"]);
  });

  it("should not call onSubmit when all lines are empty after trim", async () => {
    const user = userEvent.setup();
    render(<TaskInput onSubmit={mockOnSubmit} loading={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "\n\n\n");

    // Even if we somehow submit, it should not call onSubmit
    const form = document.querySelector("form")!;
    form.dispatchEvent(new Event("submit", { bubbles: true }));

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });
});
