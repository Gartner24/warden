> Every PR that adds a function used by 2+ modules MUST update this file.
> Every agent reading this plan MUST grep this file BEFORE writing a new helper.

## Python helpers

| name | location | purpose |
|------|----------|---------|
| `Dispatcher` | `src/detector/dispatcher.py` | Routes Scapy 802.11 packets to beacon/evil_twin/deauth callbacks |

## C++ helpers

| name | header | purpose |
|------|--------|---------|
