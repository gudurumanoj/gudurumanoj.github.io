"""A teaching model for 4 KiB pages and a two-entry LRU TLB.

It is not a hardware benchmark or a model of every possible page fault.
Run with python3 translation_model.py.
"""

from collections import OrderedDict

PAGE_BITS = 12
PAGE_SIZE = 1 << PAGE_BITS
INDEX_MASK = (1 << 9) - 1

example = 0x0000123456789ABC
indices = tuple((example >> shift) & INDEX_MASK for shift in (39, 30, 21, 12))
print("48-bit address indices:", indices, "offset:", hex(example & (PAGE_SIZE - 1)))

page_table = {1: 0xA, 2: 0xC}  # VPN -> resident physical frame number
tlb = OrderedDict()
capacity = 2


def access(virtual_address):
    vpn, offset = divmod(virtual_address, PAGE_SIZE)
    if vpn in tlb:
        frame = tlb.pop(vpn)
        event = "TLB hit"
    else:
        if vpn not in page_table:
            if vpn != 3:
                raise MemoryError(f"VPN {vpn} has no permitted mapping")
            page_table[vpn] = 0xD  # Simulated demand-zero fault and mapping.
            event = "page fault: demand-zero"
        else:
            event = "TLB miss: resident mapping"
        frame = page_table[vpn]
    tlb[vpn] = frame  # Most recently used.
    if len(tlb) > capacity:
        tlb.popitem(last=False)
    physical_address = frame * PAGE_SIZE + offset
    print(f"VA {virtual_address:#06x} -> PA {physical_address:#06x} ({event})")


for address in (0x1234, 0x1ABC, 0x2ABC, 0x3ABC, 0x1234, 0x3ABC):
    access(address)
