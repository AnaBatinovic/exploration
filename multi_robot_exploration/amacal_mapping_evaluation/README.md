# amacal_mapping_evaluation

Launch and configuration files for evaluating different map-building approaches with AMaCal datasets. Dataset bags are available on [laricscloud](http://larics.rasip.fer.hr/laricscloud/index.php/s/eklqs4x71M2ReWO). The ROBOT_NAME environment variable should be set to `pioneer`, `pioneer_rig` or `t20`.

## Launch files

#### `cartographer.launch` / `gmapping.launch`
Runs the mapping. Also included are versions which launch Rviz, and a special version of Rviz suited for video recording of the mapping process (the launch file beginning with `demo`)

#### `play_bag.launch`

Plays a bag. The following parameters are supported:

* `bag` name of the bag
* `rate` rate of playing the bag (optional, default = 1.0)

#### `rovio.launch`
Runs Rovio visual odometry.


The supporting launch files are prefixed with the robot they are related to, i.e. the launch file for Cartographer on t20 is called `t20_cartographer.launch`.


#### Useful shell aliases

Here are some useful shell aliases (put them in your shell RC file)

```
# run view_frames and view the resulting pdf with "tf"
alias tf='( function cleanup { rm frames.pdf; rm frames.gv; }; trap cleanup EXIT; trap : INT; cd /var/tmp; rosrun tf2_tools view_frames.py && evince frames.pdf )'
# switch ROBOT_NAME quickly by typing only the robot name
alias t20='export ROBOT_NAME=t20'
alias rig='export ROBOT_NAME=pioneer_rig'
alias pioneer='export ROBOT_NAME=pioneer'

# run bags with amabag <bag_name>
function amabag () {
  roslaunch amacal_mapping_evaluation play_bag.launch bag:="$1"
}
```
