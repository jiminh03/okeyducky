// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from duck_msgs:msg/DuckTargetDetection.idl
// generated code does not contain a copyright notice
#include "duck_msgs/msg/detail/duck_target_detection__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `type`
#include "rosidl_runtime_c/string_functions.h"

bool
duck_msgs__msg__DuckTargetDetection__init(duck_msgs__msg__DuckTargetDetection * msg)
{
  if (!msg) {
    return false;
  }
  // type
  if (!rosidl_runtime_c__String__init(&msg->type)) {
    duck_msgs__msg__DuckTargetDetection__fini(msg);
    return false;
  }
  // distance_m
  // center_x
  // confidence
  return true;
}

void
duck_msgs__msg__DuckTargetDetection__fini(duck_msgs__msg__DuckTargetDetection * msg)
{
  if (!msg) {
    return;
  }
  // type
  rosidl_runtime_c__String__fini(&msg->type);
  // distance_m
  // center_x
  // confidence
}

bool
duck_msgs__msg__DuckTargetDetection__are_equal(const duck_msgs__msg__DuckTargetDetection * lhs, const duck_msgs__msg__DuckTargetDetection * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // type
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->type), &(rhs->type)))
  {
    return false;
  }
  // distance_m
  if (lhs->distance_m != rhs->distance_m) {
    return false;
  }
  // center_x
  if (lhs->center_x != rhs->center_x) {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  return true;
}

bool
duck_msgs__msg__DuckTargetDetection__copy(
  const duck_msgs__msg__DuckTargetDetection * input,
  duck_msgs__msg__DuckTargetDetection * output)
{
  if (!input || !output) {
    return false;
  }
  // type
  if (!rosidl_runtime_c__String__copy(
      &(input->type), &(output->type)))
  {
    return false;
  }
  // distance_m
  output->distance_m = input->distance_m;
  // center_x
  output->center_x = input->center_x;
  // confidence
  output->confidence = input->confidence;
  return true;
}

duck_msgs__msg__DuckTargetDetection *
duck_msgs__msg__DuckTargetDetection__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  duck_msgs__msg__DuckTargetDetection * msg = (duck_msgs__msg__DuckTargetDetection *)allocator.allocate(sizeof(duck_msgs__msg__DuckTargetDetection), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(duck_msgs__msg__DuckTargetDetection));
  bool success = duck_msgs__msg__DuckTargetDetection__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
duck_msgs__msg__DuckTargetDetection__destroy(duck_msgs__msg__DuckTargetDetection * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    duck_msgs__msg__DuckTargetDetection__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
duck_msgs__msg__DuckTargetDetection__Sequence__init(duck_msgs__msg__DuckTargetDetection__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  duck_msgs__msg__DuckTargetDetection * data = NULL;

  if (size) {
    data = (duck_msgs__msg__DuckTargetDetection *)allocator.zero_allocate(size, sizeof(duck_msgs__msg__DuckTargetDetection), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = duck_msgs__msg__DuckTargetDetection__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        duck_msgs__msg__DuckTargetDetection__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
duck_msgs__msg__DuckTargetDetection__Sequence__fini(duck_msgs__msg__DuckTargetDetection__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      duck_msgs__msg__DuckTargetDetection__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

duck_msgs__msg__DuckTargetDetection__Sequence *
duck_msgs__msg__DuckTargetDetection__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  duck_msgs__msg__DuckTargetDetection__Sequence * array = (duck_msgs__msg__DuckTargetDetection__Sequence *)allocator.allocate(sizeof(duck_msgs__msg__DuckTargetDetection__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = duck_msgs__msg__DuckTargetDetection__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
duck_msgs__msg__DuckTargetDetection__Sequence__destroy(duck_msgs__msg__DuckTargetDetection__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    duck_msgs__msg__DuckTargetDetection__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
duck_msgs__msg__DuckTargetDetection__Sequence__are_equal(const duck_msgs__msg__DuckTargetDetection__Sequence * lhs, const duck_msgs__msg__DuckTargetDetection__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!duck_msgs__msg__DuckTargetDetection__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
duck_msgs__msg__DuckTargetDetection__Sequence__copy(
  const duck_msgs__msg__DuckTargetDetection__Sequence * input,
  duck_msgs__msg__DuckTargetDetection__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(duck_msgs__msg__DuckTargetDetection);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    duck_msgs__msg__DuckTargetDetection * data =
      (duck_msgs__msg__DuckTargetDetection *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!duck_msgs__msg__DuckTargetDetection__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          duck_msgs__msg__DuckTargetDetection__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!duck_msgs__msg__DuckTargetDetection__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
