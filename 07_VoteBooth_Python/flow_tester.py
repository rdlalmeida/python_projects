import flow_py_sdk
import configparser
import asyncio

network="emulator"

async def getLatestBlock():
    config = configparser.ConfigParser()
    config.read("config.ini")
    
    async with flow_py_sdk.flow_client(
        host=config.get(network, "host"), port=config.get(network, "port")
    ) as client:
        block = await client.get_latest_block(is_sealed=False)
        print(f"Block ID: {block.id.hex()}")
        print(f"Block height: {block.height}")
        print(f"Block timestamp: [{block.timestamp}]")


if __name__ == "__main__":
    asyncio.run(getLatestBlock())