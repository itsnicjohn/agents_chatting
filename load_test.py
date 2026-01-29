import os
import asyncio
import random
import argparse
from livekit import api
from dotenv import load_dotenv
from datetime import datetime


load_dotenv(".env.local", override=True)

async def create_outbound_dispatch(load_test_id, call_index, phone_number, trunk_id, duration):
    async with api.LiveKitAPI() as lkapi:
        return await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
            agent_name="outbound_agent", 
            room=f"load_test_{load_test_id}_{call_index}",
                metadata=(
                    '{'
                    f'"phone_number": "{phone_number}", '
                    f'"trunk_id": "{trunk_id}", '
                    f'"duration": {duration}'
                    '}'
                )
            )
        )
    
async def get_outbound_trunk_details(trunk_id):
    async with api.LiveKitAPI() as lkapi:
        results = await lkapi.sip.list_sip_outbound_trunk(api.ListSIPOutboundTrunkRequest(trunk_ids=[trunk_id]))
        return results.items[0]
    
async def get_inbound_trunk_details(phone_number):
    async with api.LiveKitAPI() as lkapi:
        results = await lkapi.sip.list_sip_inbound_trunk(api.ListSIPInboundTrunkRequest(numbers=[phone_number]))
        return results.items[0]


def parse_args():
    parser = argparse.ArgumentParser(description="LiveKit Load Test")
    parser.add_argument(
        "--phone_number",
        type=str,
        help="Phone number that the outbound agent will call (e.g. +12223334444)",
        required=True
    )
    parser.add_argument(
        "--trunk_id",
        type=str,
        help="Trunk ID that the outbound agent will use (e.g. ST_xyz)",
        required=True
    )
    parser.add_argument(
        "--calls", 
        type=float, 
        default=3, 
        help="Number of calls to make (default: 3)"
    )
    parser.add_argument(
        "--interval", 
        type=float, 
        default=5, 
        help="Seconds between calls (default: 5)"
    )
    parser.add_argument(
        "--duration", 
        type=float, 
        default=10, 
        help="Duration of the call in seconds (default: 10)"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    load_test_id = random.randint(1000, 9999)
    calls = int(args.calls)
    interval = int(args.interval)
    duration = int(args.duration)
    phone_number = args.phone_number
    trunk_id = args.trunk_id
    outbound_trunk_details = await get_outbound_trunk_details(trunk_id)
    inbound_trunk_details = await get_inbound_trunk_details(phone_number)
    
    print(f"Starting Load Test at {datetime.now().isoformat()}...")
    print(f"\tID: {load_test_id} (search @room:load_test_{load_test_id}* in DataDog)")
    print("\tDispatching to:", os.getenv("LIVEKIT_URL"))
    print(f"\tOutbound Details")
    print(f"\t\tTrunk: {outbound_trunk_details.sip_trunk_id}")
    print(f"\t\tName: {outbound_trunk_details.name}")
    print(f"\t\tNumber: {outbound_trunk_details.numbers[0]}")
    print(f"\t\tAddress: {outbound_trunk_details.address}")
    print(f"\tInbound Details")
    print(f"\t\tTrunk: {inbound_trunk_details.sip_trunk_id}")
    print(f"\t\tName: {inbound_trunk_details.name}")
    print(f"\t\tNumber: {inbound_trunk_details.numbers[0]}")
    print("\tTest Details:")
    print(f"\t\tNumber of calls: {calls}")
    print(f"\t\tInterval between calls: {interval} seconds")
    print(f"\t\tDuration of each call: {duration} seconds")
    print("--------------------------------\n")

    for i in range(calls):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Call {i + 1}/{calls}")
        dispatch = await create_outbound_dispatch(load_test_id, i, phone_number, trunk_id, duration)
        print(f"\tCreated dispatch: {dispatch.id}")
        print(f"\t\tRoom: {dispatch.room}")
        if i < calls - 1:  # Don't sleep after the last call
            await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())
