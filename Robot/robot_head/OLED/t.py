from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306, sh1106, ssd1327  # 사용하는 디스플레이 모델에 맞게 선택
from PIL import Image

# 1️⃣ I2C 연결 설정 (I2C 주소는 보드에 따라 다를 수 있음)
serial = i2c(port=1, address=0x3C)

# 2️⃣ 디바이스 초기화
device = ssd1306(serial)   # 또는 sh1106(serial), ssd1327(serial)

# 3️⃣ PNG 이미지 불러오기
# 이미지 크기를 OLED 해상도에 맞게 조정해야 함 (예: 128x64, 128x128 등)
image = Image.open("OLED_muki.png").convert("1")  # 흑백 모드 (1bit) 또는 .convert("L") 회색조
image = image.resize(device.size)  # 자동 리사이즈

# 4️⃣ 디스플레이에 출력
device.display(image)

