from branchlayerflow import AsyncBaseFlow, BaseMeta
from agents import Meta, AsnycFeatureAgent, AsyncRootAgent
from openai import AsyncOpenAI

def get_master_flow(store) -> AsyncBaseFlow:
    root_node = AsyncRootAgent(meta=BaseMeta(**{ "name": "root" }))
    feature_nodes = store["feature_nodes"]
    for node_name in feature_nodes:
        node_meta = Meta(**{
            **store["feature_nodes"][node_name],
            "llm": AsyncOpenAI(
                base_url=store["feature_nodes"][node_name]["llm_base_url"], 
                api_key=store["feature_nodes"][node_name]["llm_api_key"],
            )
        })
        node = AsnycFeatureAgent(meta=node_meta)
        node >> root_node # type: ignore
        root_node >> node # type: ignore
    master_flow = AsyncBaseFlow(meta=BaseMeta(**{ "name": "master_flow" }), branches=(root_node,))
    return master_flow
