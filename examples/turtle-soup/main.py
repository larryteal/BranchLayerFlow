import asyncio
import json

from flow import get_master_flow
from store import store

async def main():
    while True:
        from_name = "Loqua"
        to_name = "Stone"
        content = "Hi"
        content = input("Waiting for human input: ")
        msg_content = f"""```xml
<root>
<thinking>I'm Loqua, the boss. Stone is my chief assistant.</thinking>
<message>
<from>{from_name}</from>
<to>{to_name}</to>
<cc></cc>
<subject>From Boss</subject>
<content>{content}</content>
<attachments></attachments>
</message>
</root>
```
"""
        message = { "role": "user", "name": from_name, "content": msg_content }
        store["root"]["messages"].append(message)
        store["root"]["waiting"] = []
        master_flow = get_master_flow(store=store)
        async for layer in master_flow(store):
            print([agent.meta.name for agent in layer])
            if layer and layer[0].meta.name == "root" and store["root"]["messages"]:
                print(json.dumps(store["root"]["messages"][-1], indent=4, ensure_ascii=False))
            await asyncio.sleep(1)
    

if __name__ == "__main__":
    asyncio.run(main())
