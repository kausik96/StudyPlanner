import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

async function requestTasks(path = '', options = {}) {
  const response = await fetch(`${API_URL}/tasks${path}`, options)
  if (!response.ok) {
    throw new Error(`Task request failed (HTTP ${response.status}).`)
  }
  return response.json()
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <a className="brand" href="#dashboard">STDNTS<span>.</span></a>
      <p className="nav-caption">YOUR WORKSPACE</p>
      <nav aria-label="Main navigation">
        <a className="nav-link active" href="#dashboard">Dashboard <span>01</span></a>
        <a className="nav-link" href="#tasks">My tasks</a>
        <a className="nav-link" href="#schedule">Study plan</a>
        <a className="nav-link" href="#materials">Materials <span className="demo-tag">Demo</span></a>
      </nav>
      <div className="sidebar-note">
        <span className="eyebrow">A LITTLE EVERY DAY</span>
        <p>Big goals.<br />Small steps.</p>
        <span>Make room for what matters.</span>
      </div>
      <div className="profile">
        <span className="avatar">ST</span>
        <div><strong>Student workspace</strong><small>Your next chapter starts here</small></div>
      </div>
    </aside>
  )
}

function SummaryCard({ label, value, detail, accent, demo = false }) {
  return (
    <article className={`summary-card ${accent || ''}`}>
      <div className="card-label">{label}{demo && <span className="demo-tag">Demo data</span>}</div>
      <strong className="metric">{value}</strong>
      <small>{detail}</small>
    </article>
  )
}

function TaskItem({ task, disabled, onToggle }) {
  return (
    <li className={`task-item ${task.completed ? 'is-complete' : ''}`}>
      <label>
        <input type="checkbox" checked={task.completed} disabled={disabled} onChange={() => onToggle(task)} />
        <span className="task-copy">
          <span className="task-title">{task.title}</span>
          <small>{task.completed ? 'Nice work. One step closer.' : 'One task at a time. You have this.'}</small>
        </span>
      </label>
      <span className="task-due">
        <small className="mobile-due-label">Due date</small>
        {task.due_date
          ? <time dateTime={task.due_date}>{new Date(`${task.due_date}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</time>
          : 'No due date'}
      </span>
      <span className={`task-status ${task.completed ? 'done' : ''}`}>
        {task.completed ? 'Completed' : 'To do'}
      </span>
    </li>
  )
}

function FocusTimer() {
  const duration = 25 * 60
  const [secondsLeft, setSecondsLeft] = useState(duration)
  const [endTime, setEndTime] = useState(null)
  const running = endTime !== null
  const finished = secondsLeft === 0
  const minutes = String(Math.floor(secondsLeft / 60)).padStart(2, '0')
  const seconds = String(secondsLeft % 60).padStart(2, '0')

  useEffect(() => {
    if (endTime === null) return

    function tick() {
      const remaining = Math.max(0, Math.ceil((endTime - Date.now()) / 1000))
      setSecondsLeft(remaining)
      if (remaining === 0) setEndTime(null)
    }

    const interval = setInterval(tick, 250)
    return () => clearInterval(interval)
  }, [endTime])

  function toggleTimer() {
    if (running) {
      setSecondsLeft(Math.max(0, Math.ceil((endTime - Date.now()) / 1000)))
      setEndTime(null)
    } else {
      setEndTime(Date.now() + secondsLeft * 1000)
    }
  }

  function resetTimer() {
    setEndTime(null)
    setSecondsLeft(duration)
  }

  return (
    <section className="focus-panel" aria-labelledby="focus-heading">
      <div className="section-heading"><h2 id="focus-heading">Focus session</h2><span className="demo-tag">25 minutes</span></div>
      <div className="timer-ring">
        <span role="timer" aria-label="Focus time remaining">{minutes}:{seconds}</span>
        <small>{running ? 'STAY FOCUSED' : finished ? 'WELL DONE' : 'TIME TO FOCUS'}</small>
      </div>
      <p role="status">{finished ? 'Session complete! Take a 5-minute break.' : running ? 'One thing. Your full attention.' : secondsLeft < duration ? 'Paused. Ready when you are.' : 'Ready for a little focused progress?'}</p>
      <div className="timer-controls">
        <button type="button" onClick={toggleTimer} disabled={finished}>
          {running ? 'Pause' : secondsLeft < duration ? 'Resume' : 'Start focus'}
        </button>
        <button type="button" onClick={resetTimer}>Reset</button>
      </div>
      <span className="timer-note">Refresh resets the timer. Keep this page open.</span>
    </section>
  )
}

function Schedule({ tasks, disabled }) {
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    async function loadPlan() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`${API_URL}/study-plan`, { signal: controller.signal })
        if (!response.ok) throw new Error(`Could not load saved plan (HTTP ${response.status}).`)
        setPlan(await response.json())
      } catch (error) {
        if (!controller.signal.aborted) setError(error.message)
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    loadPlan()
    return () => controller.abort()
  }, [tasks])

  async function generatePlan() {
    setGenerating(true)
    setError('')
    try {
      const response = await fetch(`${API_URL}/study-plan`, { method: 'POST', signal: AbortSignal.timeout(30000) })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (HTTP ${response.status}).`)
      }
      setPlan(await response.json())
    } catch (error) {
      setError(error.name === 'TimeoutError' ? 'Plan request timed out. Reload to check whether it was saved before retrying.' : error.message)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <section className="panel schedule" id="schedule" aria-labelledby="schedule-heading">
      <h2 id="schedule-heading">Weekly study plan</h2>
      <p className="plan-help">Next 7 days &middot; two 25-minute blocks daily.<br />4:25&ndash;4:30 PM: take a break. Local time.</p>
      <p className="plan-help">Generating with Azure sends task IDs, titles, and due dates to that service. Use demo tasks only.</p>
      <button className="plan-button" type="button" disabled={disabled || loading || generating} onClick={generatePlan}>
        {generating ? 'Planning your week...' : plan ? 'Regenerate week' : 'Generate week'}
      </button>
      {loading && <p className="plan-help" role="status">Loading saved plan...</p>}
      {error && <p className="error-message" role="alert">{error}</p>}
      {!loading && !plan && <p className="plan-help">Generate a plan from your incomplete tasks to get started.</p>}
      {plan && <div aria-live="polite">
        <span className="demo-tag">{plan.source === 'azure-openai' ? 'Azure OpenAI plan' : 'Rule-based demo (not AI)'}</span>
        {plan.stale && <p className="plan-warning">Tasks or dates have changed. Regenerate to update this saved plan.</p>}
        <p className="plan-help">A suggested plan, not a guarantee of finishing. Check deadlines and adjust your workload.</p>
        {plan.days.map((day) => (
          <div className="plan-day" key={day.date}>
            <h3><time dateTime={day.date}>{new Date(`${day.date}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</time></h3>
            <ol className="timeline">
              {day.sessions.map((session) => (
                <li key={session.start}>
                  <small>{session.start} - {session.end}</small>
                  <div>
                    <strong>{session.title}</strong>
                    <p>{session.action}</p>
                    {session.due_date && <span>Due {session.due_date}</span>}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>}
    </section>
  )
}

function RecentMaterials() {
  const materials = [
    { type: 'PDF', title: 'Math revision notes', detail: '12 pages of good ideas', color: 'blue' },
    { type: 'SLIDES', title: 'Science project deck', detail: 'Ready for your next big idea', color: 'green' },
    { type: 'NOTES', title: 'Your study playbook', detail: 'A little inspiration to begin', color: 'purple' },
  ]
  return (
    <section id="materials" aria-labelledby="materials-heading">
      <div className="section-heading"><h2 id="materials-heading">Recent materials</h2><span className="demo-tag">Demo data &middot; sample files only</span></div>
      <div className="materials-grid">
        {materials.map((material) => (
          <article className="material-card" key={material.title}>
            <span className={`file-type ${material.color}`}>{material.type}</span>
            <h3>{material.title}</h3><p>{material.detail}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function StudyAssistant({ disabled }) {
  const [suggestion, setSuggestion] = useState(null)
  const [requesting, setRequesting] = useState(false)
  const [error, setError] = useState('')

  async function handleSuggestion() {
    setRequesting(true)
    setSuggestion(null)
    setError('')
    try {
      const response = await fetch(`${API_URL}/study-suggestion`, {
        method: 'POST',
        signal: AbortSignal.timeout(30000),
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (HTTP ${response.status}).`)
      }
      setSuggestion(await response.json())
    } catch (error) {
      setError(error.name === 'TimeoutError' ? 'The request timed out. Please try again.' : `Could not get a suggestion: ${error.message}`)
    } finally {
      setRequesting(false)
    }
  }

  return (
    <section className="panel assistant-panel" aria-labelledby="assistant-heading">
      <div className="section-heading">
        <h2 id="assistant-heading">AI Study Assistant</h2>
        <span className="demo-tag">Azure AI or labeled demo</span>
      </div>
      <p>Plan your next study steps around overdue work and upcoming deadlines.</p>
      <p className="assistant-disclosure">When Azure AI is configured, incomplete task titles and due dates are sent to that service. Use non-sensitive demo tasks only.</p>
      <button type="button" onClick={handleSuggestion} disabled={disabled || requesting}>
        {requesting ? 'Preparing suggestion...' : 'Suggest my next step'}
      </button>
      <div aria-live="polite" aria-busy={requesting}>
        {suggestion && (
          <div className="assistant-result">
            <strong>{suggestion.source === 'azure-openai' ? 'Azure OpenAI recommendation' : 'Rule-based demo (not AI)'}</strong>
            <p>{suggestion.suggestion}</p>
            <small>Based on tasks at request time. Request again after editing tasks.</small>
          </div>
        )}
      </div>
      {error && <p className="error-message" role="alert">{error}</p>}
    </section>
  )
}

function App() {
  const [today] = useState(() => new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }))
  const [tasks, setTasks] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const completedCount = tasks.filter((task) => task.completed).length

  useEffect(() => {
    const controller = new AbortController()

    async function loadTasks() {
      try {
        const data = await requestTasks('', { signal: controller.signal })
        setTasks(data)
      } catch (error) {
        if (!controller.signal.aborted) {
          setError(`Could not load tasks: ${error.message} Check that the backend is running, then reload.`)
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    loadTasks()
    return () => controller.abort()
  }, [])

  async function handleAddTask() {
    const title = inputValue.trim()

    if (title === '') {
      alert('Please enter a task title.')
      return
    }

    setSaving(true)
    setError('')
    try {
      const newTask = await requestTasks('', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, due_date: dueDate || null }),
      })
      setTasks((currentTasks) => [...currentTasks, newTask])
      setInputValue('')
      setDueDate('')
    } catch (error) {
      setError(`Could not add task: ${error.message}`)
    } finally {
      setSaving(false)
    }
  }

  async function handleToggleTask(task) {
    setSaving(true)
    setError('')
    try {
      const updatedTask = await requestTasks(`/${task.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: !task.completed }),
      })
      setTasks((currentTasks) =>
        currentTasks.map((item) => item.id === updatedTask.id ? updatedTask : item),
      )
    } catch (error) {
      setError(`Could not update task: ${error.message}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main id="dashboard">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">{today}</p>
            <h1>My Study Planner<span className="heading-dot">.</span></h1>
            <p>A little structure. A lot of possibility.</p>
          </div>
          <span className="workspace-badge"><span /> YOUR STUDY SPACE</span>
        </header>
        <div className="dashboard-grid">
          <div className="main-column">
            <section className="summary-grid" aria-label="Study overview">
              <SummaryCard label="Current GPA" value="3.84" detail="A strong foundation" demo />
              <SummaryCard label="Study streak" value="14 days" detail="Consistency is your superpower" accent="warm" demo />
              <SummaryCard label="Tasks remaining" value={loading ? '--' : tasks.length - completedCount} detail="Small steps, real progress" />
              <SummaryCard label="Tasks completed" value={loading ? '--' : `${completedCount} / ${tasks.length}`} detail="Every bit of effort counts" accent="mint" />
            </section>
            <section className="panel tasks-panel" id="tasks" aria-labelledby="tasks-heading">
              <div className="section-heading">
                <div><h2 id="tasks-heading">Priority tasks</h2><p>Your next steps, all in one place.</p></div>
                <span className="live-badge">Saved to SQLite</span>
              </div>
              <form className="task-form" onSubmit={(event) => { event.preventDefault(); handleAddTask() }}>
                <div className="task-field task-title-field">
                <label htmlFor="task-title">Task title</label>
                <input id="task-title" type="text" placeholder="What would you like to work on?"
                  value={inputValue} disabled={loading || saving}
                  onChange={(event) => setInputValue(event.target.value)} />
                </div>
                <div className="task-field">
                  <label htmlFor="task-due-date">Due date <span>(optional)</span></label>
                  <input id="task-due-date" type="date" value={dueDate} max="9999-12-31"
                    disabled={loading || saving} onChange={(event) => setDueDate(event.target.value)} />
                </div>
                <button type="submit" disabled={loading || saving}>{saving ? 'Saving...' : '+ Add Task'}</button>
              </form>
              {loading && <p className="list-message" role="status">Loading your tasks...</p>}
              {error && <p className="error-message" role="alert">{error}</p>}
              {!loading && !error && tasks.length === 0 && <p className="list-message">A fresh start. Add your first task above.</p>}
              <div className="task-columns" aria-hidden="true"><span>Task</span><span>Due date</span><span>Status</span></div>
              <ul className="task-list">
                {tasks.map((task) => <TaskItem key={task.id} task={task} disabled={loading || saving} onToggle={handleToggleTask} />)}
              </ul>
              <div className="task-footer" aria-live="polite"><span>{completedCount} / {tasks.length} tasks completed</span><span>You set the pace.</span></div>
            </section>
            <StudyAssistant disabled={loading || saving} />
            <RecentMaterials />
          </div>
          <aside className="right-column" aria-label="Focus and schedule"><FocusTimer /><Schedule tasks={tasks} disabled={loading || saving} /></aside>
        </div>
        <footer className="page-footer">Built for your next chapter.<span>React + FastAPI + SQLite</span></footer>
      </main>
    </div>
  )
}

export default App
