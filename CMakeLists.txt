cmake_minimum_required(VERSION 2.8.3)
project(rrt_exploration)
SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  nav_msgs
  roscpp
  rospy
  std_msgs
  tf
  visualization_msgs
  message_generation
  cartographer_ros
)


add_message_files(
  FILES
  PointArray.msg
  FrontierTF.msg

)

generate_messages(
  DEPENDENCIES
  std_msgs
  geometry_msgs
  cartographer_ros_msgs
)


catkin_package( 

CATKIN_DEPENDS message_runtime
)

include_directories(include ${catkin_INCLUDE_DIRS})

list(APPEND catkin_LIBRARIES cartographer_ros)

add_executable(global_rrt_detector src/global_rrt_detector.cpp src/functions.cpp src/mtrand.cpp)
target_link_libraries(global_rrt_detector ${catkin_LIBRARIES})

add_executable(local_rrt_detector src/local_rrt_detector.cpp src/functions.cpp src/mtrand.cpp)
target_link_libraries(local_rrt_detector ${catkin_LIBRARIES})
add_dependencies(global_rrt_detector ${${PROJECT_NAME}_EXPORTED_TARGETS})
add_dependencies(local_rrt_detector ${${PROJECT_NAME}_EXPORTED_TARGETS})