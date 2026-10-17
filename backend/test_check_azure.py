import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import httpx

import check_azure


class AzureCheckTests(unittest.TestCase):
    def run_check(self, settings, outcome=None):
        output = io.StringIO()
        with patch.dict(os.environ, settings, clear=True):
            with patch.object(check_azure.httpx, "Client") as client:
                post = client.return_value.__enter__.return_value.post
                if isinstance(outcome, Exception):
                    post.side_effect = outcome
                else:
                    post.return_value = outcome
                with redirect_stdout(output):
                    status = check_azure.main()
        return status, output.getvalue(), client

    def test_missing_configuration_does_not_send_request(self):
        status, output, client = self.run_check({})
        self.assertEqual(status, 1)
        self.assertIn("MISSING", output)
        client.assert_not_called()

    def test_invalid_endpoint_does_not_send_key(self):
        status, _, client = self.run_check({
            **self.settings(), "AZURE_OPENAI_ENDPOINT": "https://example.com",
        })
        self.assertEqual(status, 1)
        client.assert_not_called()

    def settings(self):
        return {
            "AZURE_OPENAI_ENDPOINT": "https://demo.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "fake-test-secret",
            "AZURE_OPENAI_DEPLOYMENT": "demo-deployment",
        }

    def test_success_and_request_shape(self):
        response = httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})
        status, output, client = self.run_check(self.settings(), response)
        self.assertEqual(status, 0)
        self.assertIn("PASS", output)
        self.assertNotIn("fake-test-secret", output)
        client.assert_called_once_with(timeout=15.0, follow_redirects=False)
        args, kwargs = client.return_value.__enter__.return_value.post.call_args
        self.assertEqual(args[0], "https://demo.openai.azure.com/openai/v1/chat/completions")
        self.assertEqual(kwargs["json"]["model"], "demo-deployment")
        self.assertEqual(kwargs["json"]["messages"][0]["content"], "Reply with only OK.")

    def test_errors_are_nonzero_and_do_not_expose_response_bodies(self):
        for outcome in [
            httpx.ReadTimeout("fake-test-secret"),
            httpx.ConnectError("fake-test-secret"),
            *[httpx.Response(code, text="fake-test-secret") for code in (400, 401, 403, 404, 429, 500)],
            httpx.Response(200, text="fake-test-secret"),
            httpx.Response(200, json={"choices": []}),
            httpx.Response(200, json={"choices": [{"message": {"content": ""}}]}),
        ]:
            with self.subTest(outcome=repr(outcome)):
                status, output, _ = self.run_check(self.settings(), outcome)
                self.assertEqual(status, 1)
                self.assertIn("FAIL", output)
                self.assertNotIn("fake-test-secret", output)


if __name__ == "__main__":
    unittest.main()
