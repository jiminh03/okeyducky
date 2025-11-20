from setuptools import find_packages, setup

package_name = 'duck_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/duck_bringup.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='bmj426',
    maintainer_email='mooyoup1999@naver.com',
    description='Control nodes for AI Duck (robot state, follow controller)',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            # ros2 run duck_control robot_state_node
            'robot_state_node = duck_control.robot_state_node:main',
            # ros2 run duck_control follow_controller_node
            'follow_controller_node = duck_control.follow_controller_node:main',
        ],
    },
)
