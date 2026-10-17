# Prompt 9: Due dates and deadline-aware study planning

Add an optional Due date field to the Add Task form and a Due date column on the
dashboard. Save dates in SQLite and include them in GET, POST, and PATCH task
responses. Preserve old tasks with no due date through a non-destructive schema
update. Keep task completion and the responsive dashboard working.

Use incomplete tasks and their due dates to recommend progress toward deadlines.
Prioritize overdue work, then the nearest deadlines, keeping undated work in the
study plan. Include the current date in the Azure prompt. Keep rule-based demo
suggestions clearly labeled and make them deadline-aware too. Do not expose keys.
