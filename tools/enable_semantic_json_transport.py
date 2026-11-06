"""Bind the existing single-object semantic protocol to JSON transport mode."""
from migrate_next import edit

def transform(source):
    old = '''        if schema_doc is None:
            payload.pop("response_format",None);payload.pop("text",None)
'''
    new = '''        if schema_doc is None:
            payload.pop("response_format",None);payload.pop("text",None)
            # Semantic decisions already require exactly one JSON object.
            # Request that wire format without inventing a field schema or
            # changing the protocol's authoritative validation/repair path.
            if schema_name == "cgkn_semantic_v1":
                if self.api_method == "chat_completions":
                    payload["response_format"] = {"type": "json_object"}
                else:
                    payload["text"] = {"format": {"type": "json_object"}}
'''
    assert source.count(old) == 1
    return source.replace(old,new,1)

edit('cgkn/providers/gateway_client.py',transform,
     'Request JSON-object wire format for the existing semantic protocol; retain strict parser, original executor and unknown/no-replay behavior')
