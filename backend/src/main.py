from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models.workflow import (
    SetWeightsRequest,
    SubmitTasksRequest,
    SetConstraintsRequest,
    GenerateScheduleRequest,
    WorkflowResponse,
    WorkflowState,
)
from .orchestrator import (
    create_session,
    get_state,
    reset_session,
    phase1_set_weights,
    phase2_submit_tasks,
    phase3_set_constraints,
    phase4_generate_schedule,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/workflow/start")
async def start_workflow(session_id: str) -> WorkflowResponse:
    """Start a new workflow session."""
    state = create_session(session_id)
    return WorkflowResponse(state=state, message="Workflow started. Set utility weights.")


@app.get("/workflow/state/{session_id}")
async def get_workflow_state(session_id: str) -> WorkflowResponse:
    """Get current workflow state."""
    state = get_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return WorkflowResponse(state=state, message=f"Current phase: {state.phase}")


@app.post("/workflow/reset/{session_id}")
async def reset_workflow(session_id: str) -> WorkflowResponse:
    """Reset workflow to beginning."""
    state = reset_session(session_id)
    return WorkflowResponse(state=state, message="Workflow reset. Set utility weights.")


@app.post("/workflow/phase1/weights")
async def set_weights(request: SetWeightsRequest) -> WorkflowResponse:
    """Phase 1: Set utility weights for task categories."""
    try:
        state = await phase1_set_weights(request.session_id, request.weights)
        return WorkflowResponse(
            state=state,
            message="Weights set. Now submit your task list."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/workflow/phase2/tasks")
async def submit_tasks(request: SubmitTasksRequest) -> WorkflowResponse:
    """Phase 2: Submit tasks for LLM categorization."""
    try:
        state = await phase2_submit_tasks(request.session_id, request.tasks)
        return WorkflowResponse(
            state=state,
            message=f"Tasks categorized. Set time constraints for {len(state.categorised_tasks)} tasks."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/workflow/phase3/constraints")
async def set_constraints(request: SetConstraintsRequest) -> WorkflowResponse:
    """Phase 3: Set time constraints for tasks."""
    try:
        state = await phase3_set_constraints(
            request.session_id,
            request.tasks,
            request.window_start,
            request.window_end,
        )
        return WorkflowResponse(
            state=state,
            message="Constraints set. Ready to generate schedule."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/workflow/phase4/schedule")
async def generate_schedule(request: GenerateScheduleRequest) -> WorkflowResponse:
    """Phase 4: Generate optimized schedule."""
    try:
        state = await phase4_generate_schedule(request.session_id)
        return WorkflowResponse(
            state=state,
            message=f"Schedule generated using {state.selected_algorithm} algorithm."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
