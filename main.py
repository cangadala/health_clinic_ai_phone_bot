# ibrary imports
import logging

# others imports
from fastapi import FastAPI

# Vocode imports
import vocode
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.config_manager.redis_config_manager import RedisConfigManager
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.telephony.server.base import TwilioInboundCallConfig, TelephonyServer
from vocode.streaming.models.transcriber import DeepgramTranscriberConfig, PunctuationEndpointingConfig
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig
from vocode.streaming.models.synthesizer import AzureSynthesizerConfig

# Local imports
import config
from agent.health_info_agent import HealthInfoAgentFactory, HealthInfoAgentConfig
from constants.message_constants import INITIAL_MESSAGE

# logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# FastAPI app
app = FastAPI(docs_url=None)

# Vocode env vars
vocode.setenv(
    OPENAI_API_KEY=config.openai_api_key,
    DEEPGRAM_API_KEY=config.deepgram_api_key,
    AZURE_SPEECH_KEY=config.azure_speech_key,
    AZURE_SPEECH_REGION=config.azure_speech_region,
)

# config settings
BASE_URL = config.base_url
config_manager = RedisConfigManager()

# agent
outpatient_agent_config = HealthInfoAgentConfig(
    initial_message=BaseMessage(text=INITIAL_MESSAGE,)
)

# Telephony server
telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    inbound_call_configs=[
        TwilioInboundCallConfig(
            url="/inbound_call",
            agent_config=outpatient_agent_config,
            transcriber_config=DeepgramTranscriberConfig.from_telephone_input_device(
                endpointing_config=PunctuationEndpointingConfig()
            ),
            synthesizer_config=ElevenLabsSynthesizerConfig.from_telephone_output_device(
                api_key=config.eleven_labs_api_key,
                voice_id=config.eleven_labs_voice_id,
            ),
            twilio_config=TwilioConfig(
                account_sid=config.twilio_secret_id,
                auth_token=config.twilio_auth_token,
            ),
        )
    ],
    agent_factory=HealthInfoAgentFactory(),
    logger=logger,
)

# FastAPI app router connect
app.include_router(telephony_server.get_router())
