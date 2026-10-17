# Study Planner frontend

## Interactive focus timer

The focus panel has a real 25-minute countdown with Start, Pause/Resume, and Reset.
It calculates remaining seconds from a target end time rather than counting
interval ticks, so delayed background-tab callbacks do not accumulate drift.
At zero it stops and announces completion with a five-minute break suggestion.
Reset returns to 25:00 and stops the timer. Refreshing resets it; no timer state
is stored in SQLite or used to change task completion. Closing/suspending the
page prevents timely notifications; no sound or background notification is sent.

## Current: weekly study plan

`Schedule` replaces placeholder classes with a saved, seven-day study plan.
It loads from GET `/study-plan` on mount/task changes and only generates with
POST `/study-plan` on button click. It owns loading/generating/error state and
displays the source and stale warning. Two 25-minute daily blocks begin at
4 PM with a five-minute break. See [Prompt 8](../prompts/prompt8.md) and the
[backend guide](../backend/README.md). No plan is generated automatically.

## Due dates (Step 9)

Add Task includes an optional date picker. Each task row displays a Due date
column (or "No due date"), with a stacked labeled layout on mobile. Dates are
formatted as local calendar dates without UTC day shifts. The assistant uses
deadlines to guide progress and study planning; its data-sharing notice includes
due dates. Existing undated tasks and completion behavior are preserved.
See [prompt9.md](../prompts/prompt9.md) and the backend guide for schema migration.

## AI assistant (Step 8)

`StudyAssistant` owns its request/loading/error state and displays a recommendation
from POST `/study-suggestion`. Only the backend reads Azure credentials and SQLite.
See the [backend guide](../backend/README.md) for Azure setup and demo mode.
No provider configured means a clearly labeled rule-based result, not AI.
Task CRUD and completion behavior are unchanged.

## Dashboard styling (Step 7)

The screenshot-inspired dashboard uses plain CSS in `src/App.css`. There are no
UI libraries or external font/icon services. GPA, streak, schedule, and materials
are labeled demo data. The focus timer is a labeled static preview, not a working
timer. Sidebar links navigate to real sections rather than unimplemented pages.

### Reusable components

- `App` owns task state and the existing GET, POST, and PATCH requests. It passes
  data and event handlers to children through props.
- `Sidebar` provides the workspace navigation.
- `SummaryCard` renders a label, metric, and supporting text. Reusing it keeps the
  four overview cards consistent; task metrics use real state.
- `TaskItem` renders one accessible checkbox, title, and completion status. It
  calls the parent handler rather than keeping a second copy of task state.
- `FocusTimer` owns the interactive countdown; `RecentMaterials` is demo data. `Schedule`
  displays the persisted weekly plan as described above.

CSS Grid arranges the sidebar, main content, and right rail. Media queries move
navigation to the top and stack content on smaller screens. The task form also
supports Enter to submit; loading, validation, and API errors remain visible.

The frontend now loads, adds, and completes tasks through FastAPI. Start both
servers using the [backend guide](../backend/README.md), which explains HTTP,
CORS, validation, and testing with `/docs`. Data is now saved in SQLite and
survives backend restarts; the React API calls and completion UI are unchanged.
Saved prompts are in [prompts](../prompts).

## Earlier lesson: Step 1

A React application created with Vite and JavaScript. This first lesson only
displays a heading and two hardcoded tasks. There is no state, event handling,
backend, database, or custom styling yet.

## Run the app

From the StudyPlanner folder:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite. Leave the terminal running while using the
app. Press Ctrl+C to stop it. On later runs, skip `npm install` unless dependencies
have changed.

## Understand every line of the original Step 1 App.jsx

See [src/App.jsx](src/App.jsx).

| Line | Code | Explanation |
| --- | --- | --- |
| 1 | `function App() {` | Declares a JavaScript function named `App`. Its capitalized name lets React recognize it as a component. The empty parentheses mean it takes no parameters; `{` starts its body. |
| 2 | `return (` | Returns what the component should display. Parentheses let the JSX continue across multiple lines. |
| 3 | `<div>` | Opens a container wrapping everything returned by this component. JSX looks like HTML but is syntax used inside JavaScript to describe the UI. |
| 4 | `<h1>My Study Planner</h1>` | Displays the main heading. The opening and closing tags surround its text. |
| 5 | `<ul>` | Opens an unordered (bulleted) list. |
| 6 | `<li>Math Homework</li>` | Displays the first list item, with its text written directly in the code (hardcoded). |
| 7 | `<li>Science Project</li>` | Displays the second hardcoded list item. |
| 8 | `</ul>` | Closes the list. |
| 9 | `</div>` | Closes the outer container. |
| 10 | `)` | Closes the parentheses around the returned JSX. |
| 11 | `}` | Ends the `App` function. |
| 12 | Blank line | Separates the function from its export for readability. It has no effect on the page. |
| 13 | `export default App` | Makes `App` this file's default export so `main.jsx` can import and display it. |

Vite transforms JSX for the browser. The starter `main.jsx` mounts `App` in the
page's root element. Its starter stylesheet import has been removed so this
lesson uses only the browser's default appearance.

## Check the project

```powershell
npm run lint
npm run build
```

The reusable lesson prompt is saved in [prompt1.md](../prompts/prompt1.md). Stop here
before introducing interactive features.
