import rclpy
from rclpy.node import Node
from duck_msgs.msg import DuckTargetDetection
import cv2
from ultralytics import YOLO


class YoloPerceptionNode(Node):
    def __init__(self):
        super().__init__('yolo_perception')
        self.publisher_ = self.create_publisher(DuckTargetDetection, '/duck/target_detection', 10)

        # 카메라 연결
        cam_id = 4  # 필요시 1, 2로 변경
        self.cap = cv2.VideoCapture(cam_id)
        if not self.cap.isOpened():
            self.get_logger().error(f"❌ Failed to open camera {cam_id}")
        else:
            self.get_logger().info(f"📷 Camera {cam_id} opened successfully")

        # YOLO 모델 로드
        self.get_logger().info("🔄 Loading YOLOv8n model...")
        self.model = YOLO('yolov8n.pt')  # 자동 다운로드
        self.get_logger().info("✅ YOLOv8n model loaded")

        # 주기적 추론 (10Hz)
        self.timer = self.create_timer(0.1, self.timer_callback)

    def timer_callback(self):
        msg = DuckTargetDetection()
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warning("⚠️ Failed to read frame")
            return

        h, w, _ = frame.shape
        results = self.model(frame, verbose=False)
        result = results[0]
        human_boxes = [b for b in result.boxes if int(b.cls[0]) == 0]  # class 0 = person

        if not human_boxes:
            msg.type = 'none'
            msg.distance_m = -1.0
            msg.center_x = -1.0
            msg.confidence = 0.0
        else:
            # 가장 큰 사람 선택
            box = max(human_boxes, key=lambda b: (b.xyxy[0][2] - b.xyxy[0][0]) * (b.xyxy[0][3] - b.xyxy[0][1]))
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cx = (x1 + x2) / 2.0
            bbox_h = y2 - y1
            cx_norm = cx / w
            k = 1.7  # 사람 키(m) 기준 보정
            distance_m = (k * h) / bbox_h if bbox_h > 0 else -1.0

            msg.type = 'human'
            msg.distance_m = float(distance_m)
            msg.center_x = float(cx_norm)
            msg.confidence = float(conf)

        self.publisher_.publish(msg)
        self.get_logger().info(
            f"👀 Detected: {msg.type}, dist={msg.distance_m:.2f}m, "
            f"cx={msg.center_x:.2f}, conf={msg.confidence:.2f}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = YoloPerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cap.release()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

