"""Decoder for Nintendo's 0x11 LZ format, used for GARC member inspection."""


class LZ11Error(ValueError):
    """Raised when a compressed member is truncated or invalid."""


def decompress(data: bytes, *, max_output: int = 64 * 1024 * 1024) -> bytes:
    if len(data) < 4 or data[0] != 0x11:
        raise LZ11Error("Missing LZ11 header")
    size = int.from_bytes(data[1:4], "little")
    pos = 4
    if size == 0:
        if len(data) < 8:
            raise LZ11Error("Truncated extended LZ11 header")
        size = int.from_bytes(data[4:8], "little")
        pos = 8
    if size > max_output:
        raise LZ11Error(f"Refusing oversized decompressed member ({size} bytes)")
    output = bytearray()
    while len(output) < size:
        if pos >= len(data):
            raise LZ11Error("Missing LZ11 flag byte")
        flags = data[pos]
        pos += 1
        for bit in range(7, -1, -1):
            if len(output) >= size:
                break
            if flags & (1 << bit) == 0:
                if pos >= len(data):
                    raise LZ11Error("Truncated LZ11 literal")
                output.append(data[pos])
                pos += 1
                continue
            if pos >= len(data):
                raise LZ11Error("Truncated LZ11 back-reference")
            first = data[pos]
            pos += 1
            prefix = first >> 4
            if prefix == 0:
                if pos + 1 >= len(data):
                    raise LZ11Error("Truncated long LZ11 back-reference")
                second, third = data[pos], data[pos + 1]
                pos += 2
                length = (((first & 0x0F) << 4) | (second >> 4)) + 0x11
                disp = (((second & 0x0F) << 8) | third) + 1
            elif prefix == 1:
                if pos + 2 >= len(data):
                    raise LZ11Error("Truncated extended LZ11 back-reference")
                second, third, fourth = data[pos], data[pos + 1], data[pos + 2]
                pos += 3
                length = (((first & 0x0F) << 12) | (second << 4) | (third >> 4)) + 0x111
                disp = (((third & 0x0F) << 8) | fourth) + 1
            else:
                if pos >= len(data):
                    raise LZ11Error("Truncated short LZ11 back-reference")
                second = data[pos]
                pos += 1
                length = prefix + 1
                disp = (((first & 0x0F) << 8) | second) + 1
            if disp > len(output):
                raise LZ11Error("LZ11 back-reference precedes output start")
            for _ in range(min(length, size - len(output))):
                output.append(output[-disp])
    return bytes(output)
