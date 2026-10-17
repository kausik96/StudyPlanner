# Prompt 8: Add an AI Study Assistant

> Add an AI Study Assistant feature. Create POST /study-suggestion in FastAPI that reads incomplete tasks from SQLite and requests a concise study recommendation from a configurable AI provider using a server-side API key stored in environment variables. Never expose the key to React. Add a button in the dashboard to request and display the recommendation. If no AI provider is configured, use a clearly labeled rule-based demo suggestion instead of pretending it is AI. Explain how React, FastAPI, SQLite, and the AI service collaborate. Include basic timeout and error handling. Stop.

Provider selected: Azure OpenAI. Configure credentials only in the backend environment.

## Weekly study plan extension

Replace the static sample schedule with an assistant-driven weekly study plan.
Generate/regenerate only when the user clicks a button, not automatically on
task changes. Use a rolling seven-day window starting today, with two 25-minute
blocks daily at 16:00-16:25 and 16:30-16:55 local time and a five-minute break.

Add GET /study-plan to load the latest saved plan (null if none exists), and
POST /study-plan to generate and save it in SQLite. Read incomplete tasks and
their due dates. Azure must return structured assignments to real task IDs;
validate the response, then attach canonical titles, dates, and fixed times on
the server. Prioritize overdue recovery and approaching deadlines, include
manageable study steps and progress checks, and do not guarantee completion.
Reject unknown/completed task IDs and future sessions scheduled after a due date.
Use review/planning sessions when appropriate rather than inventing tasks.

Persist only the latest complete valid plan. Keep it on provider errors.
Show all seven days, the plan's source, and a regenerate button in the schedule
panel. Mark it stale when incomplete tasks, deadlines, or the starting day change.
Do not erase or automatically regenerate a stale plan.

If Azure is unconfigured, produce and clearly label a deterministic rule-based
demo plan (not AI). With no incomplete tasks, use labeled non-AI review/planning
sessions without an Azure request. Incomplete Azure settings and provider errors
must remain explicit errors, never silent fallbacks. Never expose credentials.
Disclose that configured generation sends task IDs, titles, and dates to Azure.
Preserve the existing task features and concise study-suggestion endpoint.
Explain how React requests the plan, FastAPI reads SQLite and calls Azure,
validates structured output, persists it, and returns it for display. Stop.
