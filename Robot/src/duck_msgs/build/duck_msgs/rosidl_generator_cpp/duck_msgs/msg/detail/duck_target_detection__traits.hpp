// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from duck_msgs:msg/DuckTargetDetection.idl
// generated code does not contain a copyright notice

#ifndef DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__TRAITS_HPP_
#define DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "duck_msgs/msg/detail/duck_target_detection__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace duck_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const DuckTargetDetection & msg,
  std::ostream & out)
{
  out << "{";
  // member: type
  {
    out << "type: ";
    rosidl_generator_traits::value_to_yaml(msg.type, out);
    out << ", ";
  }

  // member: distance_m
  {
    out << "distance_m: ";
    rosidl_generator_traits::value_to_yaml(msg.distance_m, out);
    out << ", ";
  }

  // member: center_x
  {
    out << "center_x: ";
    rosidl_generator_traits::value_to_yaml(msg.center_x, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DuckTargetDetection & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: type
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "type: ";
    rosidl_generator_traits::value_to_yaml(msg.type, out);
    out << "\n";
  }

  // member: distance_m
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "distance_m: ";
    rosidl_generator_traits::value_to_yaml(msg.distance_m, out);
    out << "\n";
  }

  // member: center_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "center_x: ";
    rosidl_generator_traits::value_to_yaml(msg.center_x, out);
    out << "\n";
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DuckTargetDetection & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace duck_msgs

namespace rosidl_generator_traits
{

[[deprecated("use duck_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const duck_msgs::msg::DuckTargetDetection & msg,
  std::ostream & out, size_t indentation = 0)
{
  duck_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use duck_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const duck_msgs::msg::DuckTargetDetection & msg)
{
  return duck_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<duck_msgs::msg::DuckTargetDetection>()
{
  return "duck_msgs::msg::DuckTargetDetection";
}

template<>
inline const char * name<duck_msgs::msg::DuckTargetDetection>()
{
  return "duck_msgs/msg/DuckTargetDetection";
}

template<>
struct has_fixed_size<duck_msgs::msg::DuckTargetDetection>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<duck_msgs::msg::DuckTargetDetection>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<duck_msgs::msg::DuckTargetDetection>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__TRAITS_HPP_
