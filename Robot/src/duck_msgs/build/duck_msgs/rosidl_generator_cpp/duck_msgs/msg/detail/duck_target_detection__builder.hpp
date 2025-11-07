// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from duck_msgs:msg/DuckTargetDetection.idl
// generated code does not contain a copyright notice

#ifndef DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__BUILDER_HPP_
#define DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "duck_msgs/msg/detail/duck_target_detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace duck_msgs
{

namespace msg
{

namespace builder
{

class Init_DuckTargetDetection_confidence
{
public:
  explicit Init_DuckTargetDetection_confidence(::duck_msgs::msg::DuckTargetDetection & msg)
  : msg_(msg)
  {}
  ::duck_msgs::msg::DuckTargetDetection confidence(::duck_msgs::msg::DuckTargetDetection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return std::move(msg_);
  }

private:
  ::duck_msgs::msg::DuckTargetDetection msg_;
};

class Init_DuckTargetDetection_center_x
{
public:
  explicit Init_DuckTargetDetection_center_x(::duck_msgs::msg::DuckTargetDetection & msg)
  : msg_(msg)
  {}
  Init_DuckTargetDetection_confidence center_x(::duck_msgs::msg::DuckTargetDetection::_center_x_type arg)
  {
    msg_.center_x = std::move(arg);
    return Init_DuckTargetDetection_confidence(msg_);
  }

private:
  ::duck_msgs::msg::DuckTargetDetection msg_;
};

class Init_DuckTargetDetection_distance_m
{
public:
  explicit Init_DuckTargetDetection_distance_m(::duck_msgs::msg::DuckTargetDetection & msg)
  : msg_(msg)
  {}
  Init_DuckTargetDetection_center_x distance_m(::duck_msgs::msg::DuckTargetDetection::_distance_m_type arg)
  {
    msg_.distance_m = std::move(arg);
    return Init_DuckTargetDetection_center_x(msg_);
  }

private:
  ::duck_msgs::msg::DuckTargetDetection msg_;
};

class Init_DuckTargetDetection_type
{
public:
  Init_DuckTargetDetection_type()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DuckTargetDetection_distance_m type(::duck_msgs::msg::DuckTargetDetection::_type_type arg)
  {
    msg_.type = std::move(arg);
    return Init_DuckTargetDetection_distance_m(msg_);
  }

private:
  ::duck_msgs::msg::DuckTargetDetection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::duck_msgs::msg::DuckTargetDetection>()
{
  return duck_msgs::msg::builder::Init_DuckTargetDetection_type();
}

}  // namespace duck_msgs

#endif  // DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__BUILDER_HPP_
