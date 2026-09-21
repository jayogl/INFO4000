import io
from PIL import Image

# Compress in memory
img = Image.open("Galaxy.jpg")
img.thumbnail((1024, 1024))  # Scale max dimensions
buf = io.BytesIO()
img.save(buf, format="JPEG", quality=70)
byte_array = buf.getvalue()

print(f"Compressed size: {len(byte_array)} bytes")
img.save("compressed_input.jpg", format="JPEG", quality=70)