from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


class ResponseError(Exception):
    pass


class PendingEntry:
    def __init__(self, message_id: str, consumer: str, timestamp: float):
        self.message_id = message_id
        self.consumer = consumer
        self.timestamp = timestamp

    @property
    def idle(self) -> int:
        return int((time.time() - self.timestamp) * 1000)


@dataclass
class StreamEntry:
    message_id: str
    data: Dict[str, str]


class _GroupState:
    def __init__(self) -> None:
        self.next_index = 0
        self.pending: Dict[str, PendingEntry] = {}


class Redis:
    def __init__(self, decode_responses: bool = True, *args: Any, **kwargs: Any) -> None:
        self.decode_responses = decode_responses
        self.streams: Dict[str, List[StreamEntry]] = {}
        self.groups: Dict[Tuple[str, str], _GroupState] = {}
        self.kv: Dict[str, str] = {}

    def set(self, key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        if nx and key in self.kv:
            return False
        self.kv[key] = value
        return True

    def get(self, key: str) -> Optional[str]:
        return self.kv.get(key)

    def delete(self, key: str) -> None:
        self.kv.pop(key, None)

    def xgroup_create(self, name: str, groupname: str, id: str = "$", mkstream: bool = False) -> None:
        if (name, groupname) in self.groups:
            raise ResponseError("BUSYGROUP Consumer Group name already exists")
        if mkstream and name not in self.streams:
            self.streams[name] = []
        self.groups[(name, groupname)] = _GroupState()

    def xadd(self, name: str, fields: Dict[str, str]) -> str:
        stream = self.streams.setdefault(name, [])
        message_id = f"{len(stream) + 1}-0"
        stream.append(StreamEntry(message_id, fields))
        return message_id

    def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        streams: Dict[str, str],
        count: int = 1,
        block: Optional[int] = None,
    ) -> List[Tuple[str, List[Tuple[str, Dict[str, str]]]]]:
        results: List[Tuple[str, List[Tuple[str, Dict[str, str]]]]] = []
        for stream_name, start in streams.items():
            group_state = self.groups.setdefault((stream_name, groupname), _GroupState())
            stream = self.streams.get(stream_name, [])
            entries: List[Tuple[str, Dict[str, str]]] = []
            idx = group_state.next_index if start == ">" else 0
            for i in range(idx, min(len(stream), idx + count)):
                entry = stream[i]
                entries.append((entry.message_id, entry.data))
                group_state.pending[entry.message_id] = PendingEntry(entry.message_id, consumername, time.time())
                group_state.next_index = i + 1
            if entries:
                results.append((stream_name, entries))
        return results

    def xack(self, name: str, group: str, *message_ids: str) -> int:
        group_state = self.groups.get((name, group))
        if not group_state:
            return 0
        acked = 0
        for msg in message_ids:
            if msg in group_state.pending:
                group_state.pending.pop(msg, None)
                acked += 1
        return acked

    def xpending_range(
        self, name: str, groupname: str, min: str, max: str, count: int, consumername: Optional[str] = None
    ) -> List[PendingEntry]:
        group_state = self.groups.get((name, groupname))
        if not group_state:
            return []
        entries = list(group_state.pending.values())
        if consumername:
            entries = [e for e in entries if e.consumer == consumername]
        return entries[:count]

    def xclaim(
        self,
        name: str,
        group: str,
        consumername: str,
        min_idle_time: int,
        message_ids: List[str],
    ) -> List[Tuple[str, Dict[str, str]]]:
        group_state = self.groups.get((name, group))
        if not group_state:
            return []
        reclaimed = []
        stream = self.streams.get(name, [])
        for msg_id in message_ids:
            entry = next((e for e in stream if e.message_id == msg_id), None)
            if entry and msg_id in group_state.pending:
                group_state.pending[msg_id] = PendingEntry(msg_id, consumername, time.time())
                reclaimed.append((msg_id, entry.data))
        return reclaimed

    def xread(self, streams: Dict[str, str], count: Optional[int] = None) -> List[Tuple[str, List[Tuple[str, Dict[str, str]]]]]:
        results: List[Tuple[str, List[Tuple[str, Dict[str, str]]]]] = []
        for stream_name, start in streams.items():
            stream = self.streams.get(stream_name, [])
            entries: List[Tuple[str, Dict[str, str]]] = []
            start_index = 0 if start == "0" else len(stream)
            target = stream[start_index: start_index + count if count else None]
            for entry in target:
                entries.append((entry.message_id, entry.data))
            results.append((stream_name, entries))
        return results


class exceptions:
    ResponseError = ResponseError
