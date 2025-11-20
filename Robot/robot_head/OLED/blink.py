from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306, sh1106, ssd1327
from PIL import Image
from time import sleep

serial = i2c(port=1, address=0x3C)

device = ssd1306(serial)

# 128x64
while True:
    image = Image.open("open.png").convert("1")
    device.display(image)
    sleep(1.5)

    image = Image.open("close.png").convert("1")
    device.display(image)
    sleep(0.3)
