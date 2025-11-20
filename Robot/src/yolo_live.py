import argparse, cv2
from ultralytics import YOLO

def main(cam, conf, classes):
    cap = cv2.VideoCapture(cam, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
    cap.set(cv2.CAP_PROP_FPS,30)

    model = YOLO("yolov8n.pt")

    if not cap.isOpened():
        raise RuntimeError("Camera open failed")

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        res = model(frame, classes=classes, conf=conf, device=0)
        vis = res[0].plot()
        cv2.imshow("YOLOv8 Live (ESC to quit)", vis)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
   ap = argparse.ArgumentParser()
   ap.add_argument("--cam", type=int, default=2)
   ap.add_argument("--conf", type=float, default=0.40)
   ap.add_argument("--classes", nargs="*", type=int, default=[0])
   args = ap.parse_args()
   main(args.cam, args.conf, args.classes)
