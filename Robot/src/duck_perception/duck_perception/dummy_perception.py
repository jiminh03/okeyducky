import rclpy
from rclpy.node import Node

from duck_msgs.msg import DuckTargetDetection


class DummyPerceptionNode(Node):
    """
    /duck/target_detection 토픽으로
    가짜 사람 인식 결과를 주기적으로 퍼블리시하는 노드
    (나중에 여기 YOLO 추론 코드로 바꿀 예정)
    """

    def __init__(self):
        super().__init__('dummy_perception')

        # 퍼블리셔: 우리가 아까 만든 msg 타입 사용
        self.pub = self.create_publisher(
            DuckTargetDetection,
            '/duck/target_detection',
            10
        )

        # 10Hz로 타이머 실행
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info('DummyPerceptionNode started.')

        # 테스트용으로 거리/위치를 조금씩 바꿔보자
        self.t = 0.0

    def timer_callback(self):
        msg = DuckTargetDetection()
        msg.type = 'human'
        msg.distance_m = 1.0 + 0.5  # 대충 1.5m라고 가정
        msg.center_x = 0.5          # 화면 정중앙
        msg.confidence = 0.9

        self.pub.publish(msg)
        self.get_logger().info(
            f'Publish: type={msg.type}, dist={msg.distance_m:.2f}m, '
            f'center_x={msg.center_x:.2f}, conf={msg.confidence:.2f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = DummyPerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

