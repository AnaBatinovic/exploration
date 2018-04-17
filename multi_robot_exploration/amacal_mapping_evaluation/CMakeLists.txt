cmake_minimum_required(VERSION 2.8.3)

project(amacal_mapping_evaluation)

find_package(catkin REQUIRED)

catkin_package()

# robot names for various robot types
set(pioneer_ROBOT_NAMES alpha pioneer)
set(pioneer_rig_ROBOT_NAMES pioneer_rig)
set(t20_ROBOT_NAMES t20)

set(PARSE_ROBOT_NAME_TOOL "${CMAKE_CURRENT_SOURCE_DIR}/parse_robot_name.sh")
set(TEMPLATE_OUT_FILES)

# glob all template files
file(GLOB_RECURSE TEMPLATE_FILES RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/templates"
    "${CMAKE_CURRENT_SOURCE_DIR}/templates/*")

# Add a hook that reruns CMake when source files are added or removed. Taken from cartographer/cmake/functions.cmake
set(LIST_TEMPLATE_FILES_CMD "find ${CMAKE_CURRENT_SOURCE_DIR}/templates/ | sort | sed 's/^/#/'")
set(TEMPLATE_FILES_LIST_PATH "${PROJECT_BINARY_DIR}/TemplateFiles.cmake")
set(TEMPLATE_DETECT_CHANGES_CMD "bash" "-c" "${LIST_TEMPLATE_FILES_CMD} | diff -N -q ${TEMPLATE_FILES_LIST_PATH} - || ${LIST_TEMPLATE_FILES_CMD} > ${TEMPLATE_FILES_LIST_PATH}")
add_custom_target(${PROJECT_NAME}_template_detect_changes ALL
    COMMAND ${TEMPLATE_DETECT_CHANGES_CMD}
    VERBATIM
)
if(NOT EXISTS ${TEMPLATE_FILES_LIST_PATH})
execute_process(COMMAND ${TEMPLATE_DETECT_CHANGES_CMD})
endif()
include(${TEMPLATE_FILES_LIST_PATH})

foreach(TEMPLATE ${TEMPLATE_FILES})
   # split template into path, robot name and the second part of the filename
   string(REGEX REPLACE "^((.+/)*)([^.-]+)(.*)$" "\\1;\\3;\\4" TEMPLATE_FILENAME_PARTS ${TEMPLATE})
   list(GET TEMPLATE_FILENAME_PARTS 1 ROBOT_TYPE)
   set(FULL_IN_FILENAME "${CMAKE_CURRENT_SOURCE_DIR}/templates/${TEMPLATE}")
   foreach(ROBOT_NAME ${${ROBOT_TYPE}_ROBOT_NAMES})
     set(OUT_FILENAME_PARTS ${TEMPLATE_FILENAME_PARTS})
     # insert robot name after robot type
     list(INSERT OUT_FILENAME_PARTS 2 "-${ROBOT_NAME}")
     # glue list into string
     string(REPLACE ";" "" OUT_FILENAME "${OUT_FILENAME_PARTS}")
     set(FULL_OUT_FILENAME "${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_SHARE_DESTINATION}/${OUT_FILENAME}")
     #message(STATUS "Process template file: ${TEMPLATE}, src ${FULL_IN_FILENAME}, dest: ${FULL_OUT_FILENAME}, robot type: ${ROBOT_TYPE}")	
     add_custom_command(
       COMMAND ${PARSE_ROBOT_NAME_TOOL} "${ROBOT_NAME}" "${FULL_IN_FILENAME}" "${FULL_OUT_FILENAME}"
       DEPENDS ${PARSE_ROBOT_NAME_TOOL} ${FULL_IN_FILENAME}
       OUTPUT ${FULL_OUT_FILENAME}
       COMMENT "Generating from template: ${OUT_FILENAME}"
     )
     # TODO
     #install()
     SET(TEMPLATE_OUT_FILES ${TEMPLATE_OUT_FILES} ${FULL_OUT_FILENAME})
    endforeach()
endforeach()

add_custom_target(processed_templates ALL DEPENDS ${TEMPLATE_OUT_FILES})

# Install launch files
install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
