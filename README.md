# How it Works
The basic test is: An outbound agent is dispatched to a room where it uses create_sip_participant to make a call to an inbound agent (so Room A: contains the outbound agent and a sip participant). The inbound agent is dispatched via Dispatch Rule and joins its own room (so Room B: contains a sip participant and the inbound agent). The agents converse with each for a configurable amount of time before the outbound agent deletes the room. 


# New/Local Setup
### Telephony
1. Setup inbound trunk with one number
2. Setup outbound trunk with a different number
3. Setup dispatch rule
    - Rule type: Individual
    - Room prefix: call-
    - Agent dispatch
        - Agent name: `inbound_agent`
    - Match trunks
        - The inbound trunk ^
### Agents
- Both `inbound_agent` and `outbound_agent` must be running
- If running more than a few calls (~10), it's recommended to deploy both agents to LiveKit cloud
    - I recommend setting up a new LiveKit project so that the agents don't mess up any other testing on your main project

### Environment
- Add `secrets.txt` with STT/LLM/TTS provider keys
    ```bash
    DEEPGRAM_API_KEY=""
    OPENAI_API_KEY=""
    CARTESIA_API_KEY=""
    ```
- Add `.env.local` with LiveKit creds for the project you'll be running on
    ```bash 
    LIVEKIT_URL=
    LIVEKIT_API_KEY=
    LIVEKIT_API_SECRET=
    ```

# Load Test
`uv run load_test.py --help`