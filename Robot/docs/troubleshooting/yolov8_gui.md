# 🧠 Jetson YOLOv8 GUI Troubleshooting Log

**작성자:** 강무엽  
**작성일:** 2025-10-23  
**환경:** Jetson Orin Nano / Docker / Ultralytics YOLOv8 / Intel RealSense D435  
**목표:** Docker 환경에서 실시간 YOLOv8 사람 인식 + OpenCV GUI 출력  

---

## ✅ 1. 컨테이너 환경 유지 설정

- [x] `--rm` 제거 후 영구 컨테이너 실행  
- [x] 실행 후 이미지로 커밋  

```bash
docker run -it --name yolov8-dev ...
docker commit yolov8-dev yolov8-gui:jetson
```
 /workspace를 호스트 폴더($HOME/ai-duck/duck_tracking)와 연결

## ✅ 2. RealSense 카메라 인식
 컨테이너 실행 시 장치 권한 부여
```bash
--privileged --device /dev/video2
```
 장치 노드 확인
```bash
v4l2-ctl --list-devices
```
 /dev/video2가 RGB 스트림임 확인

## ✅ 3. GUI 라이브러리 설치
 GTK 및 OpenCV 설치
```bash
apt-get update
apt-get install -y libgtk-3-0 
python3-opencv
cv2.imshow() 
 ```
 테스트 (간단한 이미지 출력 확인)

## ✅ 4. NumPy 버전 고정
 NumPy 2.x 제거

 1.x 버전 설치
```bash
pip uninstall -y numpy
pip install "numpy<2"
import numpy 
```
실행 확인

## ✅ 5. GStreamer 플러그인 설치
 appsink 오류 해결용 플러그인 설치
```bash
apt-get install -y \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-{base,good,bad,ugly} \
  gstreamer1.0-libav
gst-inspect-1.0 appsink
 appsink: GStreamer sink 
 ```
 출력 확인

## ✅ 6. 카메라 포맷 에러 해결
 MJPG/YUYV 포맷 자동 감지 스크립트 작성

 BGR 변환 코드 추가
```bash
if mode == "YUYV":
    frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUY2)
elif frame.ndim == 2:
    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
```
 실시간 프레임 정상 출력 확인

## ✅ 7. X11 GUI 디스플레이 연결
 호스트에서 X11 허용
```bash
xhost +local:
```
 컨테이너에 X11 소켓 공유
```bash
volumes:
  - /tmp/.X11-unix:/tmp/.X11-unix
environment:
  - DISPLAY=:1
  - QT_X11_NO_MITSHM=1
 Jetson 모니터 DISPLAY 확인

echo $DISPLAY  # → :1
```
 컨테이너 내에서도 동일하게 설정
```bash
export DISPLAY=:1
```
 GUI 창(YOLOv8 Live) 정상 표시 🎉

## ✅ 8. 환경 영구화
 설정 완료 후 이미지로 커밋
```bash
docker commit yolov8-dev yolov8-gui:jetson
```
 다음 실행 시 동일 환경 재사용
```bash
docker run -it --name yolov8-dev \
  --gpus all --network host --privileged \
  --device /dev/video2 \
  -e DISPLAY=:1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $HOME/ai-duck/duck_tracking:/workspace \
  yolov8-gui:jetson bash
 /workspace/yolo_live.py 
 ```
 영구 보관 확인

## ✅ 최종 결과
 ✅YOLOv8n 모델 실시간 사람 감지 성공

 ✅RealSense RGB 입력 정상 작동

 ✅GUI(OpenCV GTK) 출력 정상

 ✅모든 설정 Docker 이미지에 고정 완료

## 🧩 요약
Jetson Orin Nano에서 YOLOv8 실시간 사람 인식 + GUI 출력 성공
NumPy, GStreamer, GTK, DISPLAY 이슈 모두 해결
환경 고정(docker commit) 및 코드 영구 마운트로 재설치 불필요 🎯
