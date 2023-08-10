from typing import List, Dict, Union
import json

class Doctor:
    def __init__(self, first_name: str, last_name: str, availability: Dict[str, List[str]]):
        self.first_name = first_name
        self.last_name = last_name
        self.availability = availability

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_available(self, date: str, time: str = None) -> bool:
        if date in self.availability:
            if time:
                return time in self.availability[date]
            return True
        return False

    def __repr__(self):
        return f"Doctor({self.full_name}, {self.availability})"
