"""The unit the whole lab moves around: a market-data tick.

Kept deliberately tiny — a symbol, a monotonic sequence, a send timestamp in
nanoseconds, and a price. The send timestamp is the anchor for tick-to-response
latency later: response_time - tick.sent_ns = how long WE took to react.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

# A fixed-width binary wire format. Fixed width matters for latency work: no
# JSON parsing on the hot path, no variable-length surprises. 4 fields, packed.
#   symbol_id: uint16   seq: uint32   sent_ns: uint64   price_e4: uint32
_WIRE = struct.Struct("<HIQI")


@dataclass
class Tick:
    symbol_id: int
    seq: int
    sent_ns: int          # time.perf_counter_ns() at send
    price_e4: int         # price * 10_000, integer to avoid float on hot path

    def pack(self) -> bytes:
        return _WIRE.pack(self.symbol_id, self.seq, self.sent_ns, self.price_e4)

    @staticmethod
    def unpack(buf: bytes) -> "Tick":
        symbol_id, seq, sent_ns, price_e4 = _WIRE.unpack(buf)
        return Tick(symbol_id, seq, sent_ns, price_e4)

    @staticmethod
    def size() -> int:
        return _WIRE.size
