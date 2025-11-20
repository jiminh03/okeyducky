from loguru import logger

import pyaudio

p = pyaudio.PyAudio()

logger.info("---------- 오디오 입력 장치 목록 ----------")

info = p.get_host_api_info_by_index(0)
num_devices = info.get('deviceCount')

for i in range(0, num_devices):
    device_info = p.get_device_info_by_host_api_device_index(0, i)
    # 입력 채널이 1개 이상인 장치만 (즉, 마이크만) 출력
    if device_info.get('maxInputChannels') > 0:
        logger.info(f"\n[Device ID: {i}] {device_info.get('name')}")
        logger.info(f"  기본 샘플 레이트: {device_info.get('defaultSampleRate')}")
        logger.info(f"  최대 입력 채널: {device_info.get('maxInputChannels')}")

logger.info("---------------------------------------")
p.terminate()