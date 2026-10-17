import json
import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import main
from test_study_suggestion import AZURE_CONFIG


class WeeklyPlanTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch.object(main, "DATABASE_PATH", Path(directory) / "tasks.db"))
        self.enterContext(patch.dict(os.environ, {}, clear=True))
        self.client = self.enterContext(TestClient(main.app))

    def task(self, title="Math", due=None):
        response = self.client.post("/tasks", json={"title": title, "due_date": due})
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_demo_shape_persistence_staleness_and_deadlines(self):
        self.assertIsNone(self.client.get("/study-plan").json())
        today = date.today()
        self.task("Overdue", (today - timedelta(days=1)).isoformat())
        task = self.task("Today", today.isoformat())
        self.task("Undated")
        response = self.client.post("/study-plan")
        self.assertEqual(response.status_code, 200)
        plan = response.json()
        self.assertEqual(plan["source"], "rule-based-demo")
        self.assertEqual(len(plan["days"]), 7)
        self.assertFalse(plan["stale"])
        self.assertEqual(plan["days"][0]["sessions"][0]["title"], "Overdue")
        for offset, day in enumerate(plan["days"]):
            self.assertEqual(day["date"], (today + timedelta(days=offset)).isoformat())
            self.assertEqual([(s["start"], s["end"]) for s in day["sessions"]],
                             [("16:00", "16:25"), ("16:30", "16:55")])
            if offset:
                self.assertTrue(all(s["title"] == "Undated" for s in day["sessions"]))
        with TestClient(main.app) as restarted:
            self.assertEqual(restarted.get("/study-plan").json(), plan)
        self.client.patch(f"/tasks/{task['id']}", json={"completed": True})
        self.assertTrue(self.client.get("/study-plan").json()["stale"])
        with patch.object(main, "date") as mocked_date:
            mocked_date.today.return_value = today + timedelta(days=1)
            self.assertTrue(self.client.get("/study-plan").json()["stale"])

    def test_empty_plan_makes_no_ai_call(self):
        with patch.dict(os.environ, AZURE_CONFIG), patch.object(main, "request_azure_text") as ai:
            plan = self.client.post("/study-plan").json()
        self.assertEqual(plan["source"], "rule-based-demo")
        self.assertTrue(all(s["task_id"] is None for d in plan["days"] for s in d["sessions"]))
        ai.assert_not_called()

    def test_azure_output_validated_and_saved(self):
        task = self.task()
        assignments = {"sessions": [{"task_id": task["id"], "action": "Practice and check progress."}] * 14}
        with patch.dict(os.environ, AZURE_CONFIG), patch.object(
            main, "request_azure_text", return_value=json.dumps(assignments)
        ) as ai:
            response = self.client.post("/study-plan")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "azure-openai")
        payload = ai.call_args.args[2]
        context = json.loads(payload["messages"][1]["content"])
        self.assertEqual(context["tasks"][0]["id"], task["id"])
        self.assertEqual(context["start_date"], date.today().isoformat())
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertNotIn(AZURE_CONFIG["AZURE_OPENAI_API_KEY"], response.text)

    def test_invalid_ai_plan_preserves_previous_plan(self):
        task = self.task(due=date.today().isoformat())
        self.client.post("/study-plan")
        previous = self.client.get("/study-plan").json()
        for raw in (
            "not json",
            json.dumps({"sessions": []}),
            json.dumps({"sessions": [{"task_id": "unknown", "action": "Study"}] * 14}),
            json.dumps({"sessions": [{"task_id": task["id"], "action": "Study"}] * 14}),
        ):
            with self.subTest(raw=raw[:40]), patch.dict(os.environ, AZURE_CONFIG):
                with patch.object(main, "request_azure_text", return_value=raw):
                    self.assertEqual(self.client.post("/study-plan").status_code, 502)
            self.assertEqual(self.client.get("/study-plan").json(), previous)
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "fake"}):
            self.assertEqual(self.client.post("/study-plan").status_code, 503)


if __name__ == "__main__":
    unittest.main()
