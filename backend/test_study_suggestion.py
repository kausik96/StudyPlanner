import os
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main

AZURE_CONFIG = {
    "AZURE_OPENAI_ENDPOINT": "https://demo.openai.azure.com",
    "AZURE_OPENAI_API_KEY": "test-key-not-a-real-secret",
    "AZURE_OPENAI_DEPLOYMENT": "study-demo",
}


class StudySuggestionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database_patch = patch.object(
            main, "DATABASE_PATH", Path(self.directory.name) / "tasks.db"
        )
        self.database_patch.start()
        self.addCleanup(self.database_patch.stop)
        self.environment_patch = patch.dict(os.environ, {}, clear=True)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)
        self.client = self.enterContext(TestClient(main.app))

    def add_task(self, title, completed=False):
        response = self.client.post("/tasks", json={"title": title})
        self.assertEqual(response.status_code, 201)
        task = response.json()
        if completed:
            self.client.patch(f"/tasks/{task['id']}", json={"completed": True})
        return task

    def test_demo_uses_only_incomplete_tasks_and_does_not_call_ai(self):
        self.add_task("Already done", completed=True)
        self.add_task("Math homework")
        with patch.object(main, "request_ai_suggestion") as ai:
            response = self.client.post("/study-suggestion")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "rule-based-demo")
        self.assertIn("Math homework", response.json()["suggestion"])
        self.assertNotIn("Already done", response.json()["suggestion"])
        ai.assert_not_called()

    def test_no_incomplete_tasks_does_not_call_ai(self):
        self.add_task("Done", completed=True)
        with patch.dict(os.environ, AZURE_CONFIG):
            with patch.object(main, "request_ai_suggestion") as ai:
                response = self.client.post("/study-suggestion")
        self.assertEqual(response.json()["source"], "rule-based-demo")
        self.assertIn("No incomplete tasks", response.json()["suggestion"])
        ai.assert_not_called()

    def test_partial_configuration_is_an_explicit_error(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test-key"}):
            response = self.client.post("/study-suggestion")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("test-key", response.text)

    def test_configured_endpoint_passes_only_incomplete_titles(self):
        self.add_task("Finished", completed=True)
        biology = self.add_task("Biology")
        with patch.dict(os.environ, AZURE_CONFIG):
            with patch.object(main, "request_ai_suggestion", return_value="Review biology.") as ai:
                response = self.client.post("/study-suggestion")
        self.assertEqual(response.json(), {
            "source": "azure-openai", "suggestion": "Review biology."
        })
        ai.assert_called_once_with(*AZURE_CONFIG.values(), [main.Task(**biology)])
        self.assertNotIn(AZURE_CONFIG["AZURE_OPENAI_API_KEY"], response.text)

    def test_provider_request_shape_and_timeout(self):
        request = httpx.Request("POST", "https://demo.openai.azure.com")
        response = httpx.Response(
            200, request=request,
            json={"choices": [{"message": {"content": "  Review biology.  "}}]},
        )
        with patch.object(main.httpx, "Client") as client:
            client.return_value.__enter__.return_value.post.return_value = response
            suggestion = main.request_ai_suggestion(*AZURE_CONFIG.values(), [main.Task(id="1", title="Biology", due_date=date(2026, 11, 2))])
        self.assertEqual(suggestion, "Review biology.")
        client.assert_called_once_with(timeout=15.0, follow_redirects=False)
        args, kwargs = client.return_value.__enter__.return_value.post.call_args
        self.assertEqual(args[0], "https://demo.openai.azure.com/openai/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["api-key"], AZURE_CONFIG["AZURE_OPENAI_API_KEY"])
        self.assertEqual(kwargs["json"]["model"], "study-demo")
        self.assertIn("Biology", kwargs["json"]["messages"][1]["content"])
        context = json.loads(kwargs["json"]["messages"][1]["content"])
        self.assertEqual(context["today"], date.today().isoformat())
        self.assertEqual(context["incomplete_tasks"], [{"title": "Biology", "due_date": "2026-11-02"}])

    def test_provider_errors_do_not_fall_back_or_leak_details(self):
        request = httpx.Request("POST", "https://demo.openai.azure.com")
        for outcome, expected in [
            (httpx.ReadTimeout("private details"), 504),
            (httpx.ConnectError("private details"), 502),
            (httpx.Response(401, request=request, text="private details"), 502),
            (httpx.Response(429, request=request), 502),
            (httpx.Response(200, request=request, json={"choices": []}), 502),
            (httpx.Response(200, request=request, json={"choices": [{"message": {"content": None}}]}), 502),
            (httpx.Response(200, request=request, text="not json"), 502),
        ]:
            with self.subTest(outcome=type(outcome).__name__, expected=expected):
                with patch.object(main.httpx, "Client") as client:
                    post = client.return_value.__enter__.return_value.post
                    if isinstance(outcome, Exception):
                        post.side_effect = outcome
                    else:
                        post.return_value = outcome
                    with self.assertRaises(HTTPException) as error:
                        main.request_ai_suggestion(*AZURE_CONFIG.values(), [main.Task(id="1", title="Biology")])
                self.assertEqual(error.exception.status_code, expected)
                self.assertNotIn("private details", error.exception.detail)

    def test_non_azure_endpoint_is_rejected_before_sending_key(self):
        with patch.object(main.httpx, "Client") as client:
            with self.assertRaises(HTTPException) as error:
                main.request_ai_suggestion("https://example.com", "test-key", "demo", [main.Task(id="1", title="Math")])
        self.assertEqual(error.exception.status_code, 503)
        client.assert_not_called()

    def test_cors_allows_react_post(self):
        response = self.client.options(
            "/study-suggestion",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")

    def test_due_date_round_trip_completion_and_restart(self):
        response = self.client.post("/tasks", json={"title": "Exam", "due_date": "2026-11-02"})
        self.assertEqual(response.status_code, 201)
        task = response.json()
        self.assertEqual(task["due_date"], "2026-11-02")
        updated = self.client.patch(f"/tasks/{task['id']}", json={"completed": True}).json()
        self.assertEqual(updated["due_date"], task["due_date"])
        with TestClient(main.app) as restarted:
            self.assertEqual(restarted.get("/tasks").json(), [updated])
        undated = self.add_task("No date")
        self.assertIsNone(undated["due_date"])

    def test_invalid_dates_rejected(self):
        for value in ("2026-02-30", "tomorrow", "", 12345, "2026-11-02T00:00:00"):
            with self.subTest(value=value):
                response = self.client.post("/tasks", json={"title": "Exam", "due_date": value})
                self.assertEqual(response.status_code, 422)

    def test_migration_preserves_existing_rows_and_is_repeatable(self):
        with main.database_connection() as connection:
            connection.execute("DROP TABLE tasks")
            connection.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT, completed INTEGER)")
            connection.execute("INSERT INTO tasks VALUES (?, ?, ?)", ("legacy", "Old task", 1))
        main.initialize_database()
        main.initialize_database()
        self.assertEqual(self.client.get("/tasks").json(), [
            {"id": "legacy", "title": "Old task", "completed": True, "due_date": None}
        ])

    def test_deadline_priority_and_demo_branches(self):
        today = date.today()
        self.add_task("Undated first")
        for title, due in (
            ("Later", today + timedelta(days=5)),
            ("Today", today),
            ("Overdue", today - timedelta(days=2)),
        ):
            self.client.post("/tasks", json={"title": title, "due_date": due.isoformat()})
        response = self.client.post("/study-suggestion").json()
        self.assertIn('Start with "Overdue"', response["suggestion"])
        self.assertIn("Overdue since", response["suggestion"])
        with patch.dict(os.environ, AZURE_CONFIG):
            with patch.object(main, "request_ai_suggestion", return_value="Plan") as ai:
                self.client.post("/study-suggestion")
        ordered = ai.call_args.args[-1]
        self.assertEqual([task.title for task in ordered], ["Overdue", "Today", "Later", "Undated first"])
        self.client.patch(f"/tasks/{ordered[0].id}", json={"completed": True})
        self.assertIn("Due today", self.client.post("/study-suggestion").json()["suggestion"])
        self.client.patch(f"/tasks/{ordered[1].id}", json={"completed": True})
        self.assertIn("(5 day(s) away)", self.client.post("/study-suggestion").json()["suggestion"])
        self.client.patch(f"/tasks/{ordered[2].id}", json={"completed": True})
        self.assertIn("No due date", self.client.post("/study-suggestion").json()["suggestion"])


if __name__ == "__main__":
    unittest.main()
