import logging
import json
from datetime import datetime, timedelta
from enum import Enum

from typing import (
    Any, Dict, List, Optional, Tuple, Union, cast, AsyncGenerator
)

# External Imports
import openai
from vocode.streaming.models.agent import AgentConfig, AgentType, ChatGPTAgentConfig
from vocode.streaming.agent.base_agent import BaseAgent, RespondAgent
from vocode.streaming.agent.factory import AgentFactory

# Local Imports
from models.patient_data import IndividualPatientData
from models.appointment_info import AppointmentInfo
import agent.agent_utils as agent_utils
import constants.message_constants as message_constants
import utils.text_utils as text_utils

appointment_data = AppointmentInfo.from_json("data/mock_data/appointments.json")

class ConversationState(Enum):
    CONFIRM_UNDERSTOOD = 1
    ASK_NAME = 2
    ASK_DOB = 3
    ASK_INSURANCE_PROVIDER = 4
    ASK_INSURANCE_ID = 5
    ASK_IF_REFERRAL = 6
    ASK_REFERRAL_INFO = 7
    ASK_CALL_REASON = 8
    ASK_ADDRESS = 9
    ASK_CONTACT = 10
    ASK_PATIENT_INFO_CONFIRMATION = 11
    ASK_PATIENT_INFO_CORRECTIONS = 12
    ASK_BEST_APPOINTMENT_TIMES = 13
    ASK_CONFIRM_APPOINTMENT = 14
    END_CONVERSATION = 100

class HealthInfoAgentConfig(AgentConfig, type="health_info_agent"):
    pass

class HealthInfoAgent(RespondAgent[HealthInfoAgentConfig]):
    def __init__(self, agent_config: HealthInfoAgentConfig, logger: Optional[logging.Logger] = None):
        super().__init__(agent_config=agent_config, logger=logger)
        self.conversation_state = ConversationState.CONFIRM_UNDERSTOOD
        self.patient_info_read = False
        self.appointment_info_read = False
        self.appointment_confirmed = False
        self.has_referred_physician = False
        self.patient_data = IndividualPatientData()
        self.available_appointments = []

    async def respond(self, human_input, conversation_id: str, is_interrupt: bool = False) -> Tuple[str, bool]:
        if self.conversation_state == ConversationState.CONFIRM_UNDERSTOOD:
            if agent_utils.is_denied(human_input):
                response = message_constants.GOODBYES["get_info"]
                self.conversation_state = ConversationState.END_CONVERSATION
            else:
                response = message_constants.RESPONSE[self.conversation_state.value]
                self.conversation_state = ConversationState.ASK_NAME
                
        elif self.conversation_state == ConversationState.ASK_NAME:
            response = await self.handle_name(human_input, ConversationState.ASK_DOB)

        elif self.conversation_state == ConversationState.ASK_DOB:
            response = await self.handle_dob(human_input, ConversationState.ASK_INSURANCE_PROVIDER)

        elif self.conversation_state == ConversationState.ASK_INSURANCE_PROVIDER:
            response = await self.handle_insurance_provider(human_input, ConversationState.ASK_INSURANCE_ID)

        elif self.conversation_state == ConversationState.ASK_INSURANCE_ID:
            response = await self.handle_insurance_id(human_input, ConversationState.ASK_IF_REFERRAL)

        elif self.conversation_state == ConversationState.ASK_IF_REFERRAL:
            if agent_utils.is_affirmed(human_input):
                response = message_constants.RESPONSE[ConversationState.ASK_REFERRAL_INFO.value]
                self.conversation_state = ConversationState.ASK_REFERRAL_INFO
            else:
                self.available_appointments = agent_utils.five_closest_appointments()
                response = message_constants.GREETINGS["no_problem"] + message_constants.SPACE + message_constants.RESPONSE[ConversationState.ASK_CALL_REASON.value]
                self.conversation_state = ConversationState.ASK_CALL_REASON
        
        elif self.conversation_state == ConversationState.ASK_REFERRAL_INFO:
            response = await self.handle_referral_information(human_input, ConversationState.ASK_CALL_REASON)

        elif self.conversation_state == ConversationState.ASK_CALL_REASON:
            response = await self.handle_call_reason(human_input, ConversationState.ASK_ADDRESS)

        elif self.conversation_state == ConversationState.ASK_ADDRESS:
            response = await self.handle_address_info(human_input, ConversationState.ASK_CONTACT)

        elif self.conversation_state == ConversationState.ASK_CONTACT:
            response = await self.handle_contact_info(human_input, ConversationState.ASK_PATIENT_INFO_CONFIRMATION)

        elif self.conversation_state == ConversationState.ASK_PATIENT_INFO_CONFIRMATION:
            response = await self.handle_patient_info_confirmation(human_input)

        elif self.conversation_state == ConversationState.ASK_PATIENT_INFO_CORRECTIONS:
            response = await self.handle_patient_info_corrections(human_input)
        
        elif self.conversation_state == ConversationState.ASK_BEST_APPOINTMENT_TIMES:
            if self.has_referred_physician:
                response = await self.handle_doctor_appointment_times(human_input, ConversationState.ASK_CONFIRM_APPOINTMENT)
            else:
                response = await self.handle_general_appointment_times(human_input, ConversationState.ASK_CONFIRM_APPOINTMENT)
        
        elif self.conversation_state == ConversationState.ASK_CONFIRM_APPOINTMENT:
            response = await self.handle_confirm_appointment(human_input, ConversationState.END_CONVERSATION)

        elif self.conversation_state == ConversationState.END_CONVERSATION:
            response = message_constants.GOODBYES['thanks']
            
        return response, False

    async def generate_response(self, human_input: str, conversation_id: str, is_interrupt: bool = False) -> AsyncGenerator[Union[str, None], None]:
        
        response = await self.respond(human_input, conversation_id, is_interrupt)
        yield response[0]

    async def handle_name(self, human_input, next_state):
        if agent_utils.is_valid_name(human_input):
            self.patient_data.first_name = text_utils.strip_punctuation(human_input.split()[0])
            self.patient_data.last_name = text_utils.strip_punctuation(human_input.split()[1])
            self.previous_state = self.conversation_state
            self.conversation_state = next_state
            return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[next_state.value]
        else:
            return message_constants.GREETINGS["sorry"]  + message_constants.SPACE +  message_constants.REPEAT["name"]

    async def handle_dob(self, human_input, next_state):
        valid, parsed_date = agent_utils.is_valid_dob(human_input)
        if valid:
            self.patient_data.dob = parsed_date
            self.conversation_state = next_state
            return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[next_state.value]
        else:
            return message_constants.GREETINGS["sorry"]  + message_constants.SPACE +  message_constants.REPEAT["dob"]

    async def handle_insurance_provider(self, human_input, next_state):
        human_input = text_utils.strip_punctuation(human_input)
        insurance_provider_status = agent_utils.is_valid_insurance_provider(human_input)
        if insurance_provider_status == "Accepted":
            self.patient_data.insurance_provider = human_input
            self.conversation_state = next_state
            return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[next_state.value]
        elif insurance_provider_status == "Unaccepted":
            self.patient_data.insurance_provider = human_input
            self.conversation_state = ConversationState.ASK_IF_REFERRAL
            return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[101]
        else:
            return message_constants.GREETINGS["sorry"]  + message_constants.SPACE +  message_constants.REPEAT["insurance_provider"]

    async def handle_insurance_id(self, human_input, next_state):
        human_input = text_utils.strip_punctuation(human_input)
        if agent_utils.is_valid_insurance_id(human_input):
            self.patient_data.insurance_id = human_input 
            self.conversation_state = next_state
            return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[next_state.value]
        else:
            return message_constants.GREETINGS["sorry"]  + message_constants.SPACE +  message_constants.REPEAT["insurance_id"]

    async def handle_referral_information(self, human_input, next_state):
        human_input = text_utils.strip_punctuation(human_input)
        if agent_utils.is_valid_physician_name(human_input):
            self.has_referred_physician = True
            self.patient_data.referred_physician_first_name = human_input.split()[0]
            self.patient_data.referred_physician_last_name = human_input.split()[1]
            self.available_appointments = agent_utils.is_available_when(human_input.split()[0], human_input.split()[1])
            self.conversation_state = next_state
            return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[next_state.value]
        else:
            return message_constants.GREETINGS["sorry"]  + message_constants.SPACE +  message_constants.REPEAT["referral_physician"]
    
    async def handle_call_reason(self, human_input, next_state):
        self.patient_data.call_reason = human_input
        self.conversation_state = next_state
        return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[next_state.value]
        #else:
            #return "I'm sorry I didn't catch that. Could you please repeat your reason for calling?"
            
    async def handle_address_info(self, human_input, next_state):
        if agent_utils.is_valid_address(human_input):
            self.patient_data.address = human_input
            self.conversation_state = next_state
            return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[next_state.value]
        else:
            return message_constants.GREETINGS["sorry"]  + message_constants.SPACE +  message_constants.REPEAT["address"]

    async def handle_contact_info(self, human_input, next_state):
        valid, phone_num = agent_utils.is_valid_phone_number(human_input)
        if valid:
            self.patient_data.contact_number = phone_num
            self.conversation_state = next_state
            return message_constants.GREETINGS["thanks"] + message_constants.SPACE + message_constants.RESPONSE[next_state.value]
        else:
            return message_constants.GREETINGS["sorry"]  + message_constants.SPACE +  message_constants.REPEAT["contact_number"]

    async def handle_patient_info_confirmation(self, human_input):
        if not self.patient_info_read:
            self.patient_info_read = True
            return agent_utils.read_patient_data(self.patient_data, self.has_referred_physician)
        
        if agent_utils.is_affirmed(human_input):
            self.conversation_state = ConversationState.ASK_BEST_APPOINTMENT_TIMES
            return "Now let's move onto booking an appointment. Does that sound fine?"
        elif agent_utils.is_denied(human_input):
            self.conversation_state = ConversationState.ASK_PATIENT_INFO_CORRECTIONS
            return ("I'm sorry for that. "
                "What is one section that is incorrect? Please specify so I can assist you further.")
        else:
            return message_constants.GREETINGS["sorry"]  + message_constants.SPACE + message_constants.REPEAT["confirm_patient_info"]

    async def handle_patient_info_corrections(self, human_input):
        section = self.which_section_incorrect(human_input)
        response, next_state = agent_utils.is_patient_info_corrected(ConversationState, section)
        self.conversation_state = next_state
        return response

    async def handle_doctor_appointment_times(self, human_input, next_state):
        if not self.appointment_info_read:
            self.appointment_info_read = True
            return '\n'.join(self.available_appointments)
        
        book_appointment_result = agent_utils.book_appointment('\n'.join(self.available_appointments), human_input)
        if book_appointment_result == "repeat":
            return '\n'.join(self.available_appointments)
        else:
            self.patient_data.appointment = book_appointment_result
            self.conversation_state = next_state
            return message_constants.RESPONSE[next_state.value]
        
    
    async def handle_general_appointment_times(self, human_input, next_state):
        if not self.appointment_info_read:
            self.appointment_info_read = True
            return '\n'.join(self.available_appointments)
        
        book_appointment_result = agent_utils.book_appointment('\n'.join(self.available_appointments), human_input)
        if book_appointment_result == "repeat":
            return '\n'.join(self.available_appointments)
        else:
            self.conversation_state = next_state
            self.patient_data.appointment = book_appointment_result
            return message_constants.RESPONSE[next_state.value]

    async def handle_confirm_appointment(self, human_input, next_state):
        if not self.appointment_confirmed:
            self.appointment_confirmed = True
            return agent_utils.read_booked_appointment(self.patient_data.appointment_date)

        if agent_utils.is_affirmed(human_input):
            self.conversation_state = next_state
            return message_constants.GOODBYES["complete"]
        if agent_utils.is_denied(human_input):
            self.conversation_state = ConversationState.ASK_BEST_APPOINTMENT_TIMES
            return "I apologize, let us rebook your appointment." 
        else:
            return message_constants.GREETINGS["sorry"] + message_constants.SPACE + message_constants.REPEAT["confirm_appointment"]
    
class HealthInfoAgentFactory(AgentFactory):
    def create_agent(self, agent_config: AgentConfig, logger: Optional[logging.Logger] = None) -> BaseAgent:
        if agent_config.type == "health_info_agent":
            return HealthInfoAgent(agent_config=cast(HealthInfoAgentConfig, agent_config))
        raise Exception("Invalid agent config")
