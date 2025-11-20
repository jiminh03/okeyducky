from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306, sh1106, ssd1327
from PIL import Image
from time import sleep

IMAGE_NAME = "line.png"

serial = i2c(port=1, address=0x3C)

device = sh1106(serial)

# 128x64
image = Image.open(IMAGE_NAME).convert("1")
image = image.resize(device.size) 

device.display(image)

sleep(100)
