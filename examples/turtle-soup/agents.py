from __future__ import annotations

import json
import re
from typing import Any, Tuple, Optional
from bs4 import BeautifulSoup
from branchlayerflow import BaseMeta, AsyncBaseAgent
from openai import AsyncOpenAI
import xmltodict
from collections import deque
import dicttoxml
from xml.dom.minidom import parseString

class Meta(BaseMeta):
    prompt: str
    llm: AsyncOpenAI
    llm_model: str
    llm_temperature: float

class AsnycFeatureAgent(AsyncBaseAgent):
    meta: Meta
    async def takeover(self, store: Any) -> None:
        from_name = self.meta.name
        agent = store["feature_nodes"][from_name]
        if agent["role"] == "Human":
            store["root"]["waiting"].append(from_name)
            print("Notify :: ", from_name)
            return None
        
        system_msg = { "role": "system", "content": self.meta.prompt }
        messages = store["feature_nodes"][from_name]["messages"]
        messages = [system_msg, *messages]
        llm_res = await self.meta.llm.chat.completions.create(model=self.meta.llm_model, messages=messages, temperature=self.meta.llm_temperature)
        message = {
            "content": llm_res.choices[0].message.content, 
            "role": llm_res.choices[0].message.role
        }
        store["root"]["messages"].append(message)

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return self.successors["root"],

class AsyncRootAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        shared_record = f"shared_record.txt"
        with open(shared_record, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=4)
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        if not store["root"]["messages"] or store["root"]["waiting"]:
            return None
        msg_list = deque(store["root"]["messages"])
        store["root"]["messages"] = []
        successor_names = set()
        while msg_list:
            msg_raw = msg_list.popleft()
            msg_content = msg_raw["content"].strip().strip('```xml').strip('```').strip()
            msg_content = str(BeautifulSoup(msg_content, 'lxml-xml'))
            msg_content = xmltodict.parse(msg_content)
            # print(json.dumps(msg_content, indent=4, ensure_ascii=False))
            msg_content = msg_content["root"]["message"]
            msgs = [msg_content] if not isinstance(msg_content, list) else msg_content
            
            for i,msg in enumerate(msgs):
                msg_from = msg["from"]
                msg_cc = [] if msg["cc"] is None else msg["cc"].strip().strip(";").split(";")
                msg_to = [] if msg["to"] is None else msg["to"].strip().strip(";").split(";")
                if i == 0:
                    store["feature_nodes"][msg_from]["messages"].append({ **msg_raw, "name": msg_from })
                    msg_raw["content"] = re.sub(r"<thinking>.*?</thinking>", "", msg_raw["content"], flags=re.DOTALL)
                xml_msg = dicttoxml.dicttoxml({ "message": msg }, custom_root='root', attr_type=False, xml_declaration=False, encoding="UTF-8", return_bytes=False)
                xml_msg = parseString(xml_msg).documentElement.toprettyxml(indent="", newl="\n") # type: ignore
                for to_name in msg_to:
                    store["feature_nodes"][to_name]["messages"].append({ "content": xml_msg, "role": "user", "name": msg_from })
                    successor_names.add(to_name)
                for cc_name in msg_cc:
                    store["feature_nodes"][cc_name]["messages"].append({ "content": xml_msg, "role": "user", "name": msg_from })

        # print("successor_names:: ", successor_names)
        successors = tuple([self.successors[successor_name] for successor_name in successor_names])
        return successors
