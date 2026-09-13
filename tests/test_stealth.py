import unittest
from hunter.stealth_wrapper import StealthWrapper

class TestStealthWrapper(unittest.TestCase):
    def test_wrap_execute(self):
        config = {"stealth": {"process_masquerade": True}}
        wrapper = StealthWrapper(config)
        result = wrapper.wrap_execute("/bin/echo", ["hello"], "low")
        self.assertIn("hello", result.stdout)

if __name__ == "__main__":
    unittest.main()