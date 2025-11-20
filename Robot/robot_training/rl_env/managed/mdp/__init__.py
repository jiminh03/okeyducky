# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MDP 함수 모듈: 표준 함수 + 커스텀 함수"""

# 1. Isaac Lab의 모든 표준 MDP 함수를 임포트
from isaaclab.envs.mdp import * # noqa: F401, F403

# 2. 이 폴더의 커스텀 함수들을 임포트
from .observations import (
    duck_foot_contact,
    reset_duck_foot_contact_hysteresis
)
from .events import randomize_foot_friction
from .terminations import terminate_if_stuck_while_commanded
# from .rewards import ... (커스텀 보상 함수가 있다면 추가)

# 3. __all__ 리스트에 커스텀 함수들을 추가하여 모듈 외부로 노출
_CUSTOM_FUNCTIONS = [
    "duck_foot_contact",
    "reset_duck_foot_contact_hysteresis",
    #"randomize_foot_friction",
    "terminate_if_stuck_while_commanded",
]

# 표준 함수 목록과 커스텀 함수 목록을 결합
__all__ = globals().get("__all__", []) + _CUSTOM_FUNCTIONS