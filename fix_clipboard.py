from PIL import Image

try:
    img = Image.open(r"C:\Users\murug\AppData\Local\Temp\pi-clipboard-7510b796-fca4-43da-a629-d1053309b2bb.png")
    print(f"Image successfully opened: format={img.format}, size={img.size}, mode={img.mode}")
except Exception as e:
    print(f"Failed to open image: {e}")
