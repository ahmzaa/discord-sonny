import os
from dotenv import load_dotenv
from ampapi import Bridge
from ampapi.dataclass import APIParams
from ampapi.instance import AMPControllerInstance

# --- Configuration ---

load_dotenv()


# --- Logic ---


class AMPManager:
    def __init__(self):
        self.params = APIParams(
            url=os.getenv("AMP_URL"),
            user=os.getenv("AMP_USER"),
            password=os.getenv("AMP_PASS"),
        )
        self.bridge = Bridge(api_params=self.params)
        self.ads = AMPControllerInstance()
        self.initialized = False

    async def connect(self):
        # initialize the connection and fetch instances
        if not self.initialized:
            await self.ads.get_instances()
            self.initialized = True
            print("AMP Connection Established")

    async def get_server_info(self, name: str):
        # Find a server and return current metrics
        await self.connect()

        instance = next(
            (i for i in self.ads.instances if i.friendly_name == name), None
        )

        if instance:
            await instance.get_status()
            return {
                "name": instance.friendly_name,
                "state": instance.status.state,
                "cpu": instance.status.metrics.get("CPU Usage").Percent,
                "ram": instance.status.metrics.get("Memory Usage").Percent,
            }
        return None

    async def change_power_state(self, name: str, action: str):
        # change the power state of a specific instance
        # Actions: start, stop, restart, kill
        await self.connect()

        instance = next(
            (i for i in self.ads.instances if i.friendly_name == name), None
        )

        if not instance:
            return False, "Instance not found"

        try:
            if action == "start":
                await instance.start_instance()
            elif action == "stop":
                await instance.stop_instance()
            elif action == "restart":
                await instance.restart_instance()
            elif action == "kill":
                # use with caution
                await instance.kill_instance()
            else:
                return False, "Invalid action"

            return True, f"Successfully send `{action}` command to `{name}`"
        except Exception as e:
            return False, f"Failed to `{action}` instance: `{str(e)}`"
