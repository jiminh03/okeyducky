import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import Twist
from duck_msgs.msg import DuckTargetDetection


class FollowControllerNode(Node):
    """
    /duck/target_detection + /duck/robot_state를 보고
    /duck/velocity_cmd (Twist) 퍼블리시
    """

    def __init__(self):
        super().__init__('follow_controller_node')

        self.state = 'IDLE'
        self.last_detection = None

        # 퍼블리셔
        self.cmd_pub = self.create_publisher(
            Twist,
            '/duck/velocity_cmd',
            10
        )

        # 구독: robot_state
        self.state_sub = self.create_subscription(
            String,
            '/duck/robot_state',
            self.state_callback,
            10
        )

        # 구독: target_detection
        self.detect_sub = self.create_subscription(
            DuckTargetDetection,
            '/duck/target_detection',
            self.detection_callback,
            10
        )

        # 제어 주기 (20Hz 근사)
        self.timer = self.create_timer(0.05, self.control_loop)

        # 간단한 P 제어 계수
        self.k_v = 0.5   # 거리 -> 속도
        self.k_w = 1.5   # center_x -> 회전

        # 목표 거리, 최대 속도
        self.target_dist = 1.2   # m
        self.max_linear = 0.4    # m/s
        self.max_angular = 1.0   # rad/s

        self.get_logger().info('FollowControllerNode started.')

    def state_callback(self, msg: String):
        self.state = msg.data

    def detection_callback(self, msg: DuckTargetDetection):
        self.last_detection = msg

    def control_loop(self):
        cmd = Twist()

        if self.state != 'FOLLOW':
            # IDLE / PARENT_MODE 등에서는 항상 정지
            self.cmd_pub.publish(cmd)
            return

        if self.last_detection is None:
            # 인식 정보가 없으면 안전하게 정지
            self.cmd_pub.publish(cmd)
            return

        det = self.last_detection
        if det.type != 'human' or det.confidence < 0.5 or det.distance_m < 0.0:
            # 유효하지 않은 타겟
            self.cmd_pub.publish(cmd)
            return

        # 1) 전진 속도 (거리 오차 기반)
        dist_error = det.distance_m - self.target_dist
        v = self.k_v * dist_error

        # 너무 가까우면 멈추거나 살짝 뒤로
        # (dist_error < 0이면 음수가 되어 뒤로 가려 함 → 클리핑)
        if v > self.max_linear:
            v = self.max_linear
        if v < -self.max_linear:
            v = -self.max_linear

        # 2) 회전 속도 (화면 중앙 기준 오프셋)
        # center_x: 0.0~1.0, 중앙은 0.5
        offset = det.center_x - 0.5
        w = -self.k_w * offset  # 사람이 오른쪽에 있으면 왼쪽으로 회전하도록 부호

        if w > self.max_angular:
            w = self.max_angular
        if w < -self.max_angular:
            w = -self.max_angular

        cmd.linear.x = float(v)
        cmd.angular.z = float(w)

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = FollowControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

