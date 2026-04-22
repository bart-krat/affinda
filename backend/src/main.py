import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError

from .models.workflow import (
    SetWeightsRequest,
    SubmitTasksRequest,
    SetConstraintsRequest,
    GenerateScheduleRequest,
    WorkflowResponse,
)
from .orchestrator import (
    create_session,
    get_state,
    reset_session,
    phase1_set_weights,
    phase2_submit_tasks,
    phase3_set_constraints,
    phase4_generate_schedule,
    ValidationError,
    APIError,
    WorkflowError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Daily Schedule Planner API",
    description="API for scheduling daily tasks with LLM categorization and optimization",
    version="1.0.0",
)

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
    try:
        state = create_session(session_id)
        return WorkflowResponse(
            state=state,
            message="Workflow started. Set utility weights.",
            warnings=[],
        )
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@app.get("/workflow/state/{session_id}")
async def get_workflow_state(session_id: str) -> WorkflowResponse:
    """Get current workflow state."""
    state = get_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return WorkflowResponse(
        state=state,
        message=f"Current phase: {state.phase}",
        warnings=state.schedule_warnings or [],
    )


@app.post("/workflow/reset/{session_id}")
async def reset_workflow(session_id: str) -> WorkflowResponse:
    """Reset workflow to beginning."""
    try:
        state = reset_session(session_id)
        return WorkflowResponse(
            state=state,
            message="Workflow reset. Set utility weights.",
            warnings=[],
        )
    except Exception as e:
        logger.error(f"Failed to reset workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset workflow: {str(e)}")


@app.post("/workflow/phase1/weights")
async def set_weights(request: SetWeightsRequest) -> WorkflowResponse:
    """Phase 1: Set utility weights for task categories."""
    try:
        state = await phase1_set_weights(request.session_id, request.weights)
        return WorkflowResponse(
            state=state,
            message="Weights set. Now submit your task list.",
            warnings=[],
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PydanticValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Phase 1 error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/workflow/phase2/tasks")
async def submit_tasks(request: SubmitTasksRequest) -> WorkflowResponse:
    """Phase 2: Submit tasks for LLM categorization."""
    try:
        state, warnings = await phase2_submit_tasks(request.session_id, request.tasks)
        return WorkflowResponse(
            state=state,
            message=f"Tasks categorized. Set time constraints for {len(state.categorised_tasks)} tasks.",
            warnings=warnings,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        raise HTTPException(
            status_code=503,
            detail=f"External service error: {str(e)}. Please try again."
        )
    except PydanticValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Phase 2 error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/workflow/phase3/constraints")
async def set_constraints(request: SetConstraintsRequest) -> WorkflowResponse:
    """Phase 3: Set time constraints for tasks."""
    try:
        state, warnings = await phase3_set_constraints(
            request.session_id,
            request.tasks,
            request.window_start,
            request.window_end,
        )
        message = "Constraints set. Ready to generate schedule."
        if warnings:
            message += f" ({len(warnings)} warning(s))"
        return WorkflowResponse(
            state=state,
            message=message,
            warnings=warnings,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PydanticValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Phase 3 error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/workflow/phase4/schedule")
async def generate_schedule(request: GenerateScheduleRequest) -> WorkflowResponse:
    """Phase 4: Generate optimized schedule."""
    try:
        state, warnings = await phase4_generate_schedule(request.session_id)
        return WorkflowResponse(
            state=state,
            message=f"Schedule generated using {state.selected_algorithm} algorithm.",
            warnings=warnings,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WorkflowError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Phase 4 error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
