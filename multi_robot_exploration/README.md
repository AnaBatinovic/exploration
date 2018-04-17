# amacal-konzum-data-logging
Data logging for Konzum experiments. The `ROBOT_NAME` environment variable has to be set for all launch files, e.g. `export ROBOT_NAME=charlie`.

## Launch files

###`run_experiment.launch`
Runs all the driver nodes and optionally starts recording.

Arguments:
* `record`: whether to start recording to a bag (default value is `true`)
* `path`: path for saving the recorded bag file (default value is `~/bags`)
* `prefix`: prefix for the bag name (default value is `amacal`)

###`record.launch`
Runs bag recording. Arguments are the same as for `path`, `prefix` and `robot_name`.

Topics recorded:
* `$(ROBOT_NAME)/camera/image_raw`
* `$(ROBOT_NAME)/camera/camera_info`
* `$(ROBOT_NAME)/imu`
* `$(ROBOT_NAME)/laserscan`
* `$(ROBOT_NAME)/timestamp_synchronizer` debug topics

###`tf_*.launch`

These launch files start static transform publishers. They are robot-specific, because different robots will generally have sensors mounted in different configurations.

