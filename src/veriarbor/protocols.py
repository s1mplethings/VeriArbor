"""Host ports; implementations and durable truth stay in the caller."""
from typing import Protocol, Mapping


class Archive(Protocol):
    def read(self, ref: str) -> bytes: ...


class EvidenceStore(Protocol):
    def evidence(self, ref: str) -> Mapping: ...


class Acceptance(Protocol):
    def view(self) -> Mapping: ...


class Executor(Protocol):
    def execute(self, request: Mapping) -> Mapping: ...


class EventSink(Protocol):
    def append(self, event: Mapping) -> str: ...
