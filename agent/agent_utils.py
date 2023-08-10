import logging
import re
import openai
from datetime import datetime
from typing import List, Tuple

# Local Imports
from utils.text_utils import ordinal
from models.appointment_info import AppointmentInfo
import constants.message_constants as message_constants
import constants.clinic_constants as clinic_constants

logger = logging.getLogger(__name__)
appointment_data = AppointmentInfo.from_json("data/mock_data/appointments.json")

def is_affirmed(response: str) -> bool:
    affirmative_responses = ["yes", "yep", "yeah", "understood", "got it", "okay", "ok"]
    return any(word in response.lower() for word in affirmative_responses)

def is_denied(response: str) -> bool:
    negative_responses = ["no", "nah", "not now"]
    return any(word in response.lower() for word in negative_responses)

def is_valid_name(name: str) -> bool:
    return len(name.split()) >= 2

def is_valid_dob(dob: str) -> Tuple[bool, str]:
    prompt = f"Convert the date '{dob}' into a numerical 'month/day/year' format and respond only with that format."
    logger.debug(f"LLM dob input: {dob}")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    parsed_date = completion.choices[0]['message']['content']
    logger.debug(f"LLM dob response: {parsed_date}")
    return bool(re.match(r"\d{2}/\d{2}/\d{4}", parsed_date)), parsed_date


def is_valid_insurance_provider(insurance_provider_input: str) -> str:
    accepted_insurance = '\n'.join(clinic_constants.ACCEPTED_INSURANCE_PROVIDERS)
    unaccepted_insurance = '\n'.join(clinic_constants.UNACCEPTED_INSURANCE_PROVIDERS)

    for insurance_type, insurance_list in [("Accepted", accepted_insurance), ("Unaccepted", unaccepted_insurance)]:
        prompt = (f"Please tell me if this input: {insurance_provider_input}, closely resembles any of the lines in here: "
                  f"{insurance_list}. Please respond with 'Yes' if so or 'No' if not.")
        
        logger.debug(f"LLM section input: {insurance_provider_input}")
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        output = completion.choices[0]['message']['content']
        logger.debug(f"LLM parsed input response: {output}")

        if output == "Yes":
            return insurance_type

    return ""


def is_valid_insurance_id(insurance_id_input: str) -> bool:
    return len(insurance_id_input) == 4


def is_valid_physician_name(name: str) -> bool:
    first_name, last_name = name.split()[:2]
    doctor = appointment_data.get_doctor_by_name(first_name, last_name)
    return bool(doctor)


def is_valid_address(address: str) -> bool:
    # TODO: Implement proper address validation if needed
    return True


def is_valid_phone_number(phone_num: str) -> Tuple[bool, str]:
    prompt = f"Convert the string '{phone_num}' into a numerical format (e.g., 'four, Four, Four, four' becomes '4444')."
    logger.debug(f"LLM phone input: {phone_num}")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    parsed_num = completion.choices[0]['message']['content']
    logger.debug(f"LLM phone num response: {parsed_num}")
    return bool(len(parsed_num) == 10), parsed_num



def read_patient_data(patient_data, has_referred_physician):
    return (
        f"Let's confirm the following information:\n"
        f"Your first name is: {patient_data.first_name}\n"
        f"Your last name is: {patient_data.last_name}\n"
        f"Your date of birth is: {patient_data.dob}\n"
        f"The name of your Insurance Provider is: {patient_data.insurance_provider}\n"
        f"Your Insurance ID is: {patient_data.insurance_id}\n"
        f"Referred physician (if any): {patient_data.referred_physician_first_name}{' '}{patient_data.referred_physician_last_name}\n"
        f"The reason you're calling is: {patient_data.call_reason}\n"
        f"Your address is: {patient_data.address}\n"
        f"Your contact number is: {patient_data.contact_number}\n"
        f"Is all this information correct?"
    )
   

    
def which_section_incorrect(section_input):
    prompt = f"These are the different input sections in my form. 1. name, 2. date of birth, 3. insurance firm, 4. insurance id, 5. referred physician, 6. reason for calling, 7. address, or 8. contact number. One of them has been inputted incorrectly. Which of the previous sections is the following user input:'{section_input}' referring to? Please respond solely with the singular numerical value of the associated section."
    logger.debug(f"LLM section input: {section_input}")  
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract and log the response
    parsed_section = completion.choices[0]['message']['content']
    logger.debug(f"LLM parsed section response: {parsed_section}")
    return parsed_section

def is_patient_info_corrected(ConversationState, section):
        if section == "1":
            return message_constants.response[2], ConversationState.ASK_NAME
        elif section == "2":
            return message_constants.response[3], ConversationState.ASK_DOB
        elif section == "3":
            return message_constants.response[4], ConversationState.ASK_INSURANCE_FIRM
        elif section == "4":
            return message_constants.response[5], ConversationState.ASK_INSURANCE_ID
        elif section == "5":
            return message_constants.response[7], ConversationState.ASK_REFERRAL_INFO
        elif section == "6":
            return message_constants.response[8], ConversationState.ASK_CALL_REASON
        elif section == "7":
            return message_constants.response[9], ConversationState.ASK_ADDRESS
        elif section == "8":
            return message_constants.response[10], ConversationState.ASK_CONTACT
        else:
            return "I didn't catch that, could you please repeat it?", ConversationState.ASK_PATIENT_INFO_CORRECTIONS

def is_available_when(first_name, last_name):
    doctor = appointment_data.get_doctor_by_name(first_name, last_name)

    if not doctor.availability:
        return [f"Dr. {first_name} {last_name} has no available appointments."]

    sentences = []
    for date_str, times in doctor.availability.items():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = f"{date_obj.strftime('%B')} {ordinal(date_obj.day)}"
        
        # Convert times to AM/PM format
        formatted_times = [datetime.strptime(time, "%I:%M %p").strftime("%-I %p") for time in times]
        times_str = ', '.join(formatted_times[:-1]) + ' and ' + formatted_times[-1] if len(formatted_times) > 1 else formatted_times[0]
        
        sentences.append(f"Dr. {first_name} {last_name} is available on {formatted_date} at {times_str}.")
    
    return sentences

def closest_appointments(start_num=0, end_num=5):
    all_slots = []

    for doctor in appointment_data.doctors:
        for date_str, times in doctor.availability.items():
            for time in times:
                datetime_obj = datetime.strptime(f"{date_str} {time}", "%Y-%m-%d %I:%M %p")
                all_slots.append((datetime_obj, doctor))

    # Sort the appointments by datetime
    sorted_slots = sorted(all_slots, key=lambda x: x[0])

    # Take the first five appointments
    closest_five = sorted_slots[start_num:end_num]

    sentences = []
    for slot in closest_five:
        datetime_obj, doctor = slot
        formatted_date = f"{datetime_obj.strftime('%B')} {ordinal(datetime_obj.day)}"
        time_str = datetime_obj.strftime("%-I %p")
        
        sentences.append(f"Dr. {doctor.first_name} {doctor.last_name} has an opening on {formatted_date} at {time_str}.")
    
    sentences.append("Which of these appointment times works best for you? Would you like me to repeat the list of available times? Or do none of these times work for you?")
    return sentences


def book_appointment(question, human_input):
    prompt = f"This is the information posed to a reader: {question}, they responded saying: {human_input}. If they are asking to repeat the information please only reply with the one word, 'repeat'. If they are confirming one of the dates, please reply with the date they are trying to confirm solely in the format 'MM/DD/YYYY'."
    logger.debug(f"LLM human input: {human_input}")  
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    logger.debug(f"LLM all response: {completion.values}") 
    output = completion.choices[0]['message']['content']
    logger.debug(f"LLM book appointment response: {output}")
    return output

def read_booked_appointment(appointment_info):
    return (f"Let's confirm the booked appointment time:\n"
        f"The appointment you booked was for: {appointment_info}\n"
        f"Does that sound correct?\n"
    )