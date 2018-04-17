cmake_minimum_required(VERSION 2.8.3)

project(multi_robot_exploration)

find_package(catkin REQUIRED)

catkin_package()

# Install launch files
install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
