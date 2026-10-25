"""Render the app's simple geometric arrow icon with no dependencies."""
import struct
import zlib
from pathlib import Path


def segment_distance(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy)))
    return ((x - a[0] - t * dx) ** 2 + (y - a[1] - t * dy) ** 2) ** 0.5


def chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))


def render(size):
    segments = [((.32, .68), (.68, .32)), ((.43, .32), (.68, .32)), ((.68, .32), (.68, .57))]
    data = bytearray()
    for y in range(size):
        data.append(0)
        for x in range(size):
            distance = min(segment_distance((x + .5) / size, (y + .5) / size, a, b) for a, b in segments)
            coverage = max(0, min(1, (.035 - distance) * size + .5))
            data.extend(round(bg + (fg - bg) * coverage) for bg, fg in zip((18, 59, 49), (228, 239, 166)))
    header = struct.pack('!IIBBBBB', size, size, 8, 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(data)) + chunk(b'IEND', b'')


if __name__ == '__main__':
    destination = Path(__file__).resolve().parents[1] / 'public' / 'icons'
    destination.mkdir(exist_ok=True)
    for name, size in [('apple-touch-icon', 180), ('icon-192', 192), ('icon-512', 512)]:
        (destination / f'{name}.png').write_bytes(render(size))
