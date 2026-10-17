# Weekly study plan (Prompt 8 extension)

The schedule panel now loads GET `/study-plan` and generates with POST
`/study-plan`. Click **Generate week** to create a rolling seven-day plan starting
on the backend's current local date. Every day has 16:00-16:25 and 16:30-16:55
study blocks, with a five-minute break. Future-day sessions never assign work
after its due date; overdue recovery is allowed today.

Azure receives incomplete task IDs, titles, and due dates and returns JSON
assignments. The backend validates exactly 14 assignments and known task IDs,
then attaches canonical titles and fixed dates/times. The model must support
JSON object output as well as chat completions. Without Azure configuration the
plan is labeled **Rule-based demo (not AI)**; no tasks also produces a non-AI
review plan without a provider call. Provider failures remain explicit errors.

SQLite's `study_plan` table stores only the latest valid plan and task snapshot.
GET returns `null` before first generation. Refresh/restart preserves the plan;
task/deadline changes or a new calendar day mark it stale. Regeneration is manual.
Failed generation leaves the previous plan intact. Existing task data is not
modified. Plans are guidance, not effort estimates or deadline guarantees.

Restart the backend after this update to create the new table and routes. Then
click **Generate week**; the UI never calls the paid provider automatically.
The settings remain the same as documented below. To validate:

```powershell
.\.venv\Scripts\python.exe -m unittest test_study_plan test_study_suggestion test_check_azure -v
```

## Due dates (Step 9)

New tasks accept optional `due_date` values in `YYYY-MM-DD` format or `null`.
For example POST `/tasks` with
`{"title":"Math revision","due_date":"2026-11-02"}`.
GET and PATCH responses include the date; completion changes do not erase it.
Dates are calendar dates, not timestamps; past dates are allowed for overdue work.

Startup checks the existing schema with `PRAGMA table_info(tasks)` and adds a
nullable `due_date TEXT` column using `ALTER TABLE` when needed. Existing IDs,
titles, and completion states remain intact with `due_date: null`. Restart the
backend to apply the migration. No database deletion or package install is needed.

The assistant reads incomplete tasks in deadline order (overdue first, then
nearest deadlines, undated last, insertion order for ties). Azure receives titles,
due dates, and the backend's current local calendar date to suggest next steps,
study blocks, breaks, and recovery plans. The non-AI demo follows the same order
and explains whether the next task is overdue, due today, upcoming, or undated.
It cannot estimate required effort or guarantee deadlines will be met.
The standalone Azure connection check still sends no task data.

Saved lesson: [prompt9.md](../prompts/prompt9.md).

## AI Study Assistant (Step 8)

`POST /study-suggestion` reads incomplete task titles directly from SQLite.
With no Azure settings it returns `source: "rule-based-demo"` and clearly states
that it is not AI. With all settings it returns `source: "azure-openai"`.
Partial configuration returns HTTP 503 instead of silently using demo mode.
No incomplete tasks means a labeled non-AI message without a paid service call.

## Configure Azure OpenAI (optional)

Use an organization-approved Azure OpenAI resource and a deployed chat-completions
model supporting the v1 API and `max_completion_tokens`, for example GPT-4.1.
Only non-sensitive demo data should be sent; requests send incomplete titles and due dates,
plus task IDs for weekly plans, never the database file. Charges and your Azure data-handling policies
apply. This local demo has no authentication and must not be exposed publicly.

Set these environment variables in the **backend terminal** before starting Uvicorn:

```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://YOUR-RESOURCE.openai.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "YOUR-DEPLOYMENT-NAME"
$secret = Read-Host "Azure OpenAI API key" -AsSecureString
$env:AZURE_OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $secret).Password
Remove-Variable secret
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Run that last command from `backend`. Stop any existing backend first.
The endpoint must be the resource root shown above (public Azure OpenAI domain),
not a deployment URL. The backend calls `/openai/v1/chat/completions` using the
deployment name as `model`; no API-version variable is needed.
Keys are never sent to React, placed in `VITE_*` variables, or printed in errors.
Environment settings are read by the backend process; restart it after changes.
No `.env` loader is included. Never paste credentials into chat or source files.
To return to demo mode, remove all three variables and restart:

```powershell
Remove-Item Env:AZURE_OPENAI_ENDPOINT, Env:AZURE_OPENAI_DEPLOYMENT, Env:AZURE_OPENAI_API_KEY -ErrorAction SilentlyContinue
```

## Check Azure independently

After setting all three environment variables above, run from `backend`:

```powershell
.\.venv\Scripts\python.exe check_azure.py
```

This does not require the backend or React to be running and does not access
SQLite. It sends only "Reply with only OK." to the same v1 chat endpoint and
deployment used by the app. One small Azure request may incur charges.
It reports missing configuration, invalid endpoints, HTTP error hints, network
timeouts, and unusable responses without printing the key or provider body.
Exit code 0 means basic chat generation succeeded; 1 means a check failed.
It does not prove that every model parameter, prompt, or future request will work.
It reads this terminal's environment only, not `.env` or a running server's
environment. Restart FastAPI from this terminal after the check passes.

## How the four parts collaborate

1. React's assistant button sends POST to FastAPI (no API key or task payload).
2. FastAPI queries SQLite with `WHERE completed = ?`, using `0` as the parameter.
3. FastAPI either applies the deadline-aware demo rule, or
   sends the incomplete titles and due dates to Azure OpenAI over HTTPS with the server key.
4. Azure returns a recommendation; FastAPI sends only the text and source label.
5. React displays plain text and labels the result as Azure AI or a non-AI demo.
   Suggestions are snapshots; request again after changing tasks.

Azure requests have a 15-second network timeout; React stops waiting after 30
seconds. Timeouts return 504, connection/provider/malformed-response errors return
502, and configuration errors return 503. Errors are shown in the dashboard;
provider failures never masquerade as successful demo recommendations. Logs
exclude credentials, task titles, and provider response bodies.

In `/docs`, execute POST `/study-suggestion` without a body to test either mode.
Live Azure integration requires your own valid configuration; automated tests mock
the service, send no data externally, and use a temporary SQLite file:

```powershell
.\.venv\Scripts\python.exe -m unittest test_study_suggestion -v
```

Saved instructions: [prompt8.md](../prompts/prompt8.md).

## SQLite foundation (Step 6)

Tasks now live in `backend/tasks.db`, using Python's built-in `sqlite3` module.
Browser refreshes and backend restarts keep the data. No SQLite package or ORM
is needed. The file is located relative to `main.py`, not the terminal directory.
It is created on startup with an empty tasks table; previous in-memory tasks
are not migrated.

## Setup

From the StudyPlanner workspace in PowerShell:

```powershell
cd backend
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

In one terminal, from StudyPlanner:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, from StudyPlanner:

```powershell
cd frontend
npm run dev -- --port 5173 --strictPort
```

Open the frontend at http://localhost:5173 or http://127.0.0.1:5173.
Only those two origins are allowed by CORS. Stop each server with Ctrl+C.

## Request/response flow

1. React's `useEffect` loads tasks when the component mounts.
2. `fetch` sends `GET http://127.0.0.1:8000/tasks`. FastAPI returns a JSON array.
3. `response.json()` reads the data; `setTasks` triggers a React render.
4. Add Task sends `POST /tasks` with JSON such as `{"title":"English Essay"}`.
5. Pydantic trims the title and rejects empty/whitespace-only or non-string titles
   with HTTP 422. FastAPI assigns an ID, inserts into SQLite, and returns the
   created task with HTTP 201. React adds that returned object to its state.
6. A checkbox sends `PATCH /tasks/{id}` with `{"completed":true}` (or `false`).
   The backend updates the matching task and returns it. React replaces that task
   using `map`, updating the checkbox, strike-through, and computed counter.
7. Failed requests display an error instead of pretending the operation worked.
   Controls are disabled during loading/saving to avoid overlapping edits.

Different ports mean different browser origins. CORS lets the browser call this
backend from the approved frontend origins. JSON writes may first trigger an
automatic `OPTIONS` preflight, handled by the CORS middleware.

## Test with the automatic API docs

Open http://127.0.0.1:8000/docs. Expand each endpoint, select **Try it out**, then
**Execute**:

1. `GET /tasks`: expect HTTP 200 and the current array.
2. `POST /tasks`: use `{"title":"English Essay"}`; expect HTTP 201 and a task with
   a generated `id` and `completed: false`. Copy its ID.
3. `PATCH /tasks/{task_id}`: paste that ID and use `{"completed":true}`; expect
   HTTP 200 and `completed: true`.
4. Repeat GET to see the saved completion. Refresh React to load those changes.
5. POST `{"title":"   "}`: expect HTTP 422.
6. PATCH an unknown ID: expect HTTP 404.

Changes made through `/docs` appear in React on refresh; this lesson does not
implement polling or real-time synchronization.

## Understand the SQL

- `CREATE TABLE IF NOT EXISTS tasks (...)` creates the table once. Each row has
  a unique text `id`, a nonempty `title`, and an integer `completed` (`0` or `1`).
  Running this again does not erase existing rows.
- `INSERT INTO tasks (id, title, completed) VALUES (?, ?, ?)` adds a row.
  The values are supplied separately as a Python tuple.
- `SELECT id, title, completed FROM tasks ORDER BY rowid` reads rows in insertion
  order. `WHERE id = ?` reads only the row with that ID.
- `UPDATE tasks SET completed = ? WHERE id = ?` changes the matching row.
  A zero affected-row count means the ID was not found, so the API returns 404.

The `?` placeholders are parameterized SQL: values stay data rather than being
interpreted as SQL commands. Titles containing quotes work normally.

`database_connection()` opens a connection for each operation, commits a
successful transaction (or rolls it back on error), and always closes it.
`task_from_row()` converts SQLite's `0`/`1` into a JSON boolean, keeping the same
API response shape: `id`, `title`, and `completed`. FastAPI's lifespan function
initializes the table when the server starts.

## Verify persistence across a restart

1. Add a task named "Restart test" in React and check its checkbox.
2. Refresh the browser: the task should remain completed.
3. In the backend terminal, press Ctrl+C. Leave the frontend running.
4. Restart with the same Uvicorn command shown above.
5. Refresh React again, or execute `GET /tasks` in `/docs`.
6. Confirm the same task ID, title, and `completed: true` are still present.

Do not remove `tasks.db` between these steps: it is the persistent data file.
The reusable instructions are in [prompt6.md](../prompts/prompt6.md). Stop here.
