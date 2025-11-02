import flow_py_sdk
import configparser
import asyncio
from common.account_config import Config
from pathlib import Path

async def getLatestBlock():
    config = configparser.ConfigParser()
    config.read("./common/config.ini")
    network=config.get("network", "current")
    print("Current Flow network selected: ", network)

    async with flow_py_sdk.flow_client(
        host=config.get(network, "host"), port=config.get(network, "port")
    ) as client:
        block = await client.get_latest_block(is_sealed=False)
        print(f"Block ID: {block.id.hex()}")
        print(f"Block height: {block.height}")
        print(f"Block timestamp: [{block.timestamp}]")

if __name__ == "__main__":
    flow_json_location = "./flow.json"
    flow_json_path = Path(flow_json_location)
    
    ctx = Config(flow_json_path)

    index = 0
    for account in ctx.accounts:
        print("Account {index} = ", account["name"], " => ", account["address"])
        index+=1