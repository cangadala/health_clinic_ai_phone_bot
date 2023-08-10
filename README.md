# Doctor Fakir's Clinic Telephony System

Doctor Fakir's Clinic offers a telephony system to streamline the patient introduction process, ensuring a seamless interaction from the start of the call.

### Details

- Automated patient introduction form process.
  Built using Vocode and other tools

### Prerequisites

- Ensure you have the required API keys for OpenAI, Deepgram, Azure Speech, and Eleven Labs.
- Install necessary Python packages (FastAPI, Vocode, etc.)
- Install the required Python packages:
```bash
pip install -r requirements.txt
```

### Configuration

Update the `config.py` file (or related configuration files) with the necessary API keys and other configuration parameters.

### Running the Server

To start the FastAPI server, run:
```bash
docker build -t vocode-telephony-app .
docker-compose up
```

### Usage

Once the server is up and running, you can interact with the telephony system by calling the provided number or endpoint. The system will guide patients through the introduction form process.

### File Structure

- `main.py`: The main server file containing the FastAPI instance and telephony configuration.
- `config.py`: Holds all the configuration parameters and API keys.
- `agent/`: Directory containing the agent's logic for handling the telephony interactions.
- `models/`: Contains the class models for some of the classes used.
- `constants/`: Contains constant values, messages, and configurations for the system.
- `data/`: Holds the mock data for the clinic doctor appointments.
