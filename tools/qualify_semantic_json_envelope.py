"""Use the gateway's supported structured envelope, retaining open semantic fields."""
from migrate_next import edit

def transform(source):
    old='''            if schema_name == "cgkn_semantic_v1":
                if self.api_method == "chat_completions":
                    payload["response_format"] = {"type": "json_object"}
                else:
                    payload["text"] = {"format": {"type": "json_object"}}
'''
    new='''            if schema_name == "cgkn_semantic_v1":
                # The installed gateway admits JSON Schema envelopes. Only
                # the existing object container is constrained here; semantic
                # fields and table identities remain owned by the protocol.
                envelope = {"name": schema_name, "strict": False,
                            "schema": {"type": "object"}}
                if self.api_method == "chat_completions":
                    payload["response_format"] = {"type": "json_schema", "json_schema": envelope}
                else:
                    payload["text"] = {"format": {"type": "json_schema", **envelope}}
'''
    assert source.count(old)==1
    return source.replace(old,new,1)

edit('cgkn/providers/gateway_client.py',transform,
     'Qualify semantic object envelope against installed gateway admission; open fields, strict semantic parser and no-replay remain authoritative')
