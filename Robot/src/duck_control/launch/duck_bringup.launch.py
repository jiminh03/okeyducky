from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # YOLO Perception Node
        Node(
            package='duck_perception',
            executable='yolo_perception',
            name='yolo_perception',
            output='screen'
        ),

        # Robot State Node
        Node(
            package='duck_control',
            executable='robot_state_node',
            name='robot_state_node',
            output='screen'
        ),

        # Follow Controller Node
        Node(
            package='duck_control',
            executable='follow_controller_node',
            name='follow_controller_node',
            output='screen'
        ),
    ])

