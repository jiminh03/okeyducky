from setuptools import find_packages, setup

package_name = 'duck_perception'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='bmj426',
    maintainer_email='mooyoup1999@naver.com',
    description='Perception nodes for AI Duck (YOLO, target detection, etc.)',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'dummy_perception = duck_perception.dummy_perception:main',
            'yolo_perception = duck_perception.yolo_perception:main',
        ],
    },
)
