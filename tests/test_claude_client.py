import unittest
from app.core.claude_client import ClaudeClient
from app.utils.logger import ClaudeLogger

class TestClaudeClient(unittest.TestCase):
    def setUp(self):
        self.client = ClaudeClient()
        self.logger = ClaudeLogger()
    
    def test_basic_response(self):
        prompt = "Hello, how are you?"
        response = self.client.generate_response(prompt)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
    
    def test_error_handling(self):
        prompt = ""  # Prompt vacío para forzar error
        with self.assertRaises(ValueError):
            self.client.generate_response(prompt)

if __name__ == '__main__':
    unittest.main() 