from dotenv import load_dotenv
import asyncio
import json

from livekit import agents, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, get_job_context
from livekit.agents.llm import function_tool
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from google.protobuf import duration_pb2

load_dotenv("../.env.local", override=True)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a trivia bot that calls a user and asks trivia questions. The questions should all be answerable with one word. Say nothing other than the question. Don't prompt the user for anything.")


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    dial_info = json.loads(ctx.job.metadata)
    phone_number = dial_info["phone_number"]
    trunk_id = dial_info["trunk_id"]
    duration = int(dial_info["duration"])

    sip_participant_identity = phone_number
    if phone_number is not None:
        try:
            print(f"[LOAD TEST] Dialing {phone_number}")
            print(f"[LOAD TEST] Room name: {ctx.room.name}")
            await ctx.api.sip.create_sip_participant(api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=trunk_id,
                sip_call_to=phone_number,
                participant_identity=sip_participant_identity,
                wait_until_answered=True,
            ))

            print("[LOAD TEST] Call picked up successfully")
        except api.TwirpError as e:
            print(f"[LOAD TEST] Error creating SIP participant: {e.message}, "
                  f"[LOAD TEST] SIP status: {e.metadata.get('sip_status_code')} "
                  f"[LOAD TEST] SIP status: {e.metadata.get('sip_status')}")
            ctx.shutdown()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o-mini", temperature=0.0),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )

    # Schedule a timer to end the call after the timer runs out
    async def duration_elapsed():
        try:
            print(f"[LOAD TEST] Duration elapsed: {duration} seconds")
            await ctx.delete_room()
        except Exception as e:
            print(f"[LOAD TEST] Failed to delete room after duration elapsed: {e}")
            # Room may have already been deleted or connection lost

    print(f"[LOAD TEST] Scheduling duration_elapsed task for {duration} seconds")
    # Create the timer task to run in background
    asyncio.create_task(asyncio.sleep(duration)).add_done_callback(
        lambda _: asyncio.create_task(duration_elapsed())
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, agent_name="outbound_agent"))
