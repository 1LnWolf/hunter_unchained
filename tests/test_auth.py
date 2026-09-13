import unittest
from unittest.mock import patch
from hunter.master_auth import gpg_auth

class TestAuth(unittest.TestCase):
    @patch("hunter.master_auth.gnupg.GPG")
    def test_gpg_auth_success(self, mock_gpg):
        config = {"master": {"gpg_key_fingerprint": "ABCDEF1234"}}
        mock_gpg.return_value.verify.return_value.valid = True
        mock_gpg.return_value.verify.return_value.fingerprint = "ABCDEF1234"
        mock_gpg.return_value.verify.return_value.data = b"challenge"
        with patch("builtins.input", return_value="signed"):
            self.assertTrue(gpg_auth(config))

if __name__ == "__main__":
    unittest.main()