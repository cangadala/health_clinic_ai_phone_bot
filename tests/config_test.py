import unittest
import config

class TestConfigVariables(unittest.TestCase):

    def test_openai_api_key(self):
        self.assertIsNotNone(config.openai_api_key, "openai_api_key is None!")

    def test_deepgram_api_key(self):
        self.assertIsNotNone(config.deepgram_api_key, "deepgram_api_key is None!")

    def test_azure_speech_key(self):
        self.assertIsNotNone(config.azure_speech_key, "azure_speech_key is None!")

    def test_azure_speech_region(self):
        self.assertIsNotNone(config.azure_speech_region, "azure_speech_region is None!")

    def test_twilio_secret_id(self):
        self.assertIsNotNone(config.twilio_secret_id, "twilio_secret_id is None!")

    def test_twilio_auth_token(self):
        self.assertIsNotNone(config.twilio_auth_token, "twilio_auth_token is None!")

    def test_eleven_labs_api_key(self):
        self.assertIsNotNone(config.eleven_labs_api_key, "eleven_labs_api_key is None!")

    def test_eleven_labs_voice_id(self):
        self.assertIsNotNone(config.eleven_labs_voice_id, "eleven_labs_voice_id is None!")

    def test_base_url(self):
        self.assertIsNotNone(config.base_url, "base_url is None!")

    def test_speechmatics_api_key(self):
        self.assertIsNotNone(config.speechmatics_api_key, "speechmatics_api_key is None!")

    def test_vocode_api_key(self):
        self.assertIsNotNone(config.vocode_api_key, "vocode_api_key is None!")

    # If you want to check other variables, you can continue adding test methods similarly.

if __name__ == "__main__":
    unittest.main()
