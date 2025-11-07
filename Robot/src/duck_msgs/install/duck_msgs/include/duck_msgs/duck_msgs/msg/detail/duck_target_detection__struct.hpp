// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from duck_msgs:msg/DuckTargetDetection.idl
// generated code does not contain a copyright notice

#ifndef DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__STRUCT_HPP_
#define DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__duck_msgs__msg__DuckTargetDetection __attribute__((deprecated))
#else
# define DEPRECATED__duck_msgs__msg__DuckTargetDetection __declspec(deprecated)
#endif

namespace duck_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct DuckTargetDetection_
{
  using Type = DuckTargetDetection_<ContainerAllocator>;

  explicit DuckTargetDetection_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->type = "";
      this->distance_m = 0.0f;
      this->center_x = 0.0f;
      this->confidence = 0.0f;
    }
  }

  explicit DuckTargetDetection_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : type(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->type = "";
      this->distance_m = 0.0f;
      this->center_x = 0.0f;
      this->confidence = 0.0f;
    }
  }

  // field types and members
  using _type_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _type_type type;
  using _distance_m_type =
    float;
  _distance_m_type distance_m;
  using _center_x_type =
    float;
  _center_x_type center_x;
  using _confidence_type =
    float;
  _confidence_type confidence;

  // setters for named parameter idiom
  Type & set__type(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->type = _arg;
    return *this;
  }
  Type & set__distance_m(
    const float & _arg)
  {
    this->distance_m = _arg;
    return *this;
  }
  Type & set__center_x(
    const float & _arg)
  {
    this->center_x = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    duck_msgs::msg::DuckTargetDetection_<ContainerAllocator> *;
  using ConstRawPtr =
    const duck_msgs::msg::DuckTargetDetection_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<duck_msgs::msg::DuckTargetDetection_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<duck_msgs::msg::DuckTargetDetection_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      duck_msgs::msg::DuckTargetDetection_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<duck_msgs::msg::DuckTargetDetection_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      duck_msgs::msg::DuckTargetDetection_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<duck_msgs::msg::DuckTargetDetection_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<duck_msgs::msg::DuckTargetDetection_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<duck_msgs::msg::DuckTargetDetection_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__duck_msgs__msg__DuckTargetDetection
    std::shared_ptr<duck_msgs::msg::DuckTargetDetection_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__duck_msgs__msg__DuckTargetDetection
    std::shared_ptr<duck_msgs::msg::DuckTargetDetection_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DuckTargetDetection_ & other) const
  {
    if (this->type != other.type) {
      return false;
    }
    if (this->distance_m != other.distance_m) {
      return false;
    }
    if (this->center_x != other.center_x) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    return true;
  }
  bool operator!=(const DuckTargetDetection_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DuckTargetDetection_

// alias to use template instance with default allocator
using DuckTargetDetection =
  duck_msgs::msg::DuckTargetDetection_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace duck_msgs

#endif  // DUCK_MSGS__MSG__DETAIL__DUCK_TARGET_DETECTION__STRUCT_HPP_
