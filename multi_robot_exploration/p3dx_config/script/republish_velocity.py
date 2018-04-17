#!/usr/bin/env python
import rospy
import time
from geometry_msgs.msg import Twist


storeVel=Twist()
def velocity_callback(msg):
    global storeVel
    global pub
    storeVel.linear=msg.linear
    storeVel.angular=msg.angular
    pub.publish(msg)


if __name__=='__main__':
    rospy.init_node('republish_velocity')

    pub=rospy.Publisher("cmd_vel", Twist, queue_size=1)
    sub=rospy.Subscriber("cmd_vel_orig",Twist,velocity_callback)

    while not rospy.is_shutdown():
        if storeVel:
            pub.publish(storeVel)
            time.sleep(1/10.)
