from typing import List, Dict, Union
import json

from models.doctor_info import Doctor

class AppointmentInfo:
    def __init__(self, doctors: List[Doctor]):
        self.doctors = doctors

    @classmethod
    def from_json(cls, json_file_path: str):
        with open(json_file_path, 'r') as f:
            data = json.load(f)
            doctors = [Doctor(**doctor_data) for doctor_data in data['doctors']]
            return cls(doctors)

    def get_doctor_by_name(self, first_name: str, last_name: str) -> Union[Doctor, None]:
        for doctor in self.doctors:
            if doctor.first_name == first_name and doctor.last_name == last_name:
                return doctor
        return None

    def __repr__(self):
        return f"AppointmentInfo({self.doctors})"
