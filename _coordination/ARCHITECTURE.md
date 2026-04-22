# Architecture

**Scope of this document:** Foundation, stack, roadmap, and Bootstrap completion criteria. Feature-level behaviour (user flows, detailed acceptance criteria) is out of scope and belongs in a separate features document.

**How implementers should use this file:** Work one milestone at a time, in order. Bootstrap is complete when every bullet in its Done-when list verifies — do not declare Bootstrap complete without reference to the list. Core and Hardening completion is decided at the point those milestones are reached, informed by what was actually built.

## What We're Building

A daily schedule planner that takes a list of tasks, categorises them using an LLM (Personal, Health, Work), accepts time constraints from the user, and outputs an optimised calendar-block schedule via an optimisation algorithm.

**Key user needs:**
- Quick input of multiple tasks via chat-style interface
- Automatic categorisation without manual tagging
- Constraint-aware scheduling that respects durations, fixed times, and day boundaries

**Out of scope:**
- Recurring tasks / multi-day planning
- Calendar sync (Google, Outlook)
- Collaboration / sharing
- Mobile app
- User accounts / saved history
- Persistence between sessions

## Tech Stack

**Language:** Python 3.12 (backend), TypeScript (frontend)
**Frontend:** React (Node 24)
**Backend:** FastAPI with submodule orchestration pattern
**LLM Provider:** OpenAI (API key in root)
**Optimisation:** Python-based solver (scipy.optimize or PuLP — decision deferred to implementation)
**Deployment:** Local only

**Rationale:** FastAPI provides async API with minimal boilerplate. React handles the calendar-block UI well. OpenAI handles categorisation without needing to train a custom model. Submodule orchestration keeps backend concerns separated while routing through a single entry point.

## Hard Constraints

- Python 3.12 exactly
- Node 24 exactly
- OpenAI as LLM provider
- Backend architecture: submodules orchestrated through single script
- Local deployment only
- Single user — no auth, no scaling considerations

## System Components

- **Frontend (React):** Chat-style task input, time constraint form, calendar-block schedule display
- **API Layer (FastAPI):** Single orchestration entry point routing to submodules
- **Categoriser Submodule:** Calls OpenAI to classify tasks into Personal/Health/Work
- **Optimiser Submodule:** Takes categorised tasks + constraints, outputs scheduled blocks
- **Scheduler Core:** Constraint model and optimisation algorithm

## File Structure

```
frontend/
  src/
    components/
      TaskInput.tsx
      ConstraintForm.tsx
      CalendarView.tsx
    App.tsx
    api.ts
  package.json

backend/
  src/
    main.py              # FastAPI app + orchestration
    submodules/
      categoriser.py     # OpenAI categorisation logic
      optimiser.py       # Scheduling algorithm
    models/
      task.py            # Task, Constraint, Schedule models
    config.py            # OpenAI key loading
  requirements.txt

.env                     # OpenAI API key
```

## Roadmap

### Milestone: Bootstrap — get it running

**Work items (priority order):**
1. FastAPI skeleton with single health endpoint
2. React app with basic task input form that submits to backend
3. Categoriser submodule calling OpenAI to classify task list
4. Wire frontend → backend → OpenAI → frontend response displayed

**Done when** *(every bullet must verify — treat as binary checks)*:
- Backend starts without errors on `uvicorn backend.src.main:app`
- `GET /health` returns 200
- Frontend starts without errors on `npm run dev`
- User can type a list of tasks in the frontend and click submit
- Backend receives the task list and calls OpenAI categorisation
- Frontend displays the returned categories (Personal/Health/Work) for each task

---

### Milestone: Core — primary functionality

**Work items (priority order):**
4. Constraint input UI (duration per task, optional fixed start time, day window)
5. Optimiser submodule with scheduling algorithm
6. Calendar-block output display
7. Utility weighting configuration (relative priority of Personal/Health/Work)

*Completion criteria for this milestone are defined when the milestone is reached.*

---

### Milestone: Hardening — production readiness

**Work items (priority order):**
8. Input validation and error handling (malformed tasks, API failures)
9. Loading states and error UI in frontend
10. Edge cases in optimiser (overlapping fixed times, impossible constraints)

*Completion criteria for this milestone are defined when the milestone is reached.*

## Production Considerations

**Security:** API key loaded from environment, not hardcoded. No auth needed for single-user local use.
**Error Handling:** Graceful handling of OpenAI API failures with user-facing error messages. Optimiser returns partial schedule if full optimisation fails.
**Logging:** Backend logs API calls and optimiser decisions to stdout for debugging.
**Performance:** Not a concern at single-user scale; optimiser should complete in <2s for typical daily task loads (~20 tasks).

## Data Model

```
Task:
  id: string
  description: string
  category: "Personal" | "Health" | "Work" (assigned by LLM)
  duration_minutes: int
  fixed_start_time: datetime | null

DayConstraints:
  window_start: time (e.g. 08:00)
  window_end: time (e.g. 18:00)

ScheduledBlock:
  task_id: string
  start_time: datetime
  end_time: datetime

UtilityWeights:
  personal: float
  health: float
  work: float
```

## API Design

```
POST /categorise
  Request: { tasks: string[] }
  Response: { categorised: [{ description: string, category: string }] }

POST /schedule
  Request: {
    tasks: [{ description, category, duration_minutes, fixed_start_time? }],
    constraints: { window_start, window_end },
    weights: { personal, health, work }
  }
  Response: { schedule: [{ task_id, start_time, end_time }] }

GET /health
  Response: { status: "ok" }
```
