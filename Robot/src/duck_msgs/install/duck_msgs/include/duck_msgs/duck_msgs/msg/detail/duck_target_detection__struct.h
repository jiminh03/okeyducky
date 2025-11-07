// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from duck_msgs:msg/DuckTargetDetection.idl
// generated code does not contain a copyright notice

#ifndef DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__STRUCT_H_
#define DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'type'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/DuckTargetDetection in the package duck_msgs.
typedef struct duck_msgs__msg__DuckTargetDetection
{
  /// "human" 또는 "none"
  rosidl_runtime_c__String type;
  /// 추정 거리 (m)
  float distance_m;
  /// 화면 가로 비율 (0.0 ~ 1.0, 중앙=0.5)
  float center_x;
  /// 0.0 ~ 1.0
  float confidence;
} duck_msgs__msg__DuckTargetDetection;

// Struct for a sequence of duck_msgs__msg__DuckTargetDetection.
typedef struct duck_msgs__msg__DuckTargetDetection__Sequence
{
  duck_msgs__msg__DuckTargetDetection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} duck_msgs__msg__DuckTargetDetection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__STRUCT_H_
