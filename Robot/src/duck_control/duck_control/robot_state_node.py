import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from duck_msgs.msg import DuckTargetDetection


class RobotStateNode(Node):
    """
    /duck/target_detection 을 보고
    로봇 상태(IDLE/FOLLOW)를 결정하는 노드
    """

    def __init__(self):
        super().__init__('robot_state_node')

        self.state_pub = self.create_publisher(
            String,
            '/duck/robot_state',
            10
        )

        self.sub = self.create_subscription(
            DuckTargetDetection,
            '/duck/target_detection',
            self.detection_callback,
            10
        )

        # 현재 상태 저장
        self.current_state = 'IDLE'

        # 주기적으로 상태 브로드캐스트 (백엔드, 로그용)
        self.timer = self.create_timer(0.5, self.timer_callback)

        self.get_logger().info('RobotStateNode started.')

    def detection_callback(self, msg: DuckTargetDetection):
        """
        사람 인식 결과를 보고 상태 전환
        """
        # 아주 단순한 로직 (나중에 히스테리시스/타임아웃 추가 가능)
        if msg.type == 'human' and msg.confidence > 0.5:
            new_state = 'FOLLOW'
        else:
            new_state = 'IDLE'

        if new_state != self.current_state:
            self.get_logger().info(
                f'State changed: {self.current_state} -> {new_state}'
            )
            self.current_state = new_state

    def timer_callback(self):
        msg = String()
        msg.data = self.current_state
        self.state_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RobotStateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

