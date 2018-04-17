#!/usr/bin/env python

#--------Include modules---------------
from copy import copy
import rospy
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from std_msgs.msg import Int32
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PointStamped, Vector3, Point, Pose
from geometry_msgs.msg import Transform
import tf
from numpy import array,vstack,delete,setdiff1d, array_equal
from functions import gridValue,informationGain
from sklearn.cluster import MeanShift
from rrt_exploration.msg import PointArray
from rrt_exploration.msg import FrontierTF
from cartographer_ros_msgs.msg import SubmapList, SubmapEntry
import PyKDL
import numpy
from tf_conversions import posemath
import tf_conversions
import message_filters


# Subscribers' callbacks------------------------------
mapData=OccupancyGrid()
all_frontiers=[]
transformed_frontiers=[]
globalmaps=[]
current_frontier = []
current_submap_poses = {}

def transform (frontier_tf):
	global current_submap_poses

	while len(current_submap_poses)==0:
		pass

	for frontier in frontier_tf: #sada je svaki frontier oblik FrontierTF ima submapIndex, trajectory_id i transform
		if (frontier.trajectory_id, frontier.submapIndex) in current_submap_poses:
			pomocni=posemath.toMsg(
				current_submap_poses[frontier.trajectory_id, frontier.submapIndex] *
				PyKDL.Frame(PyKDL.Rotation.Identity(),
							PyKDL.Vector(frontier.transform.x,frontier.transform.y,0.0))
			)
			frontier.projected=pomocni.position


def transformCallBack (frontier_tf):
	global current_frontier

	current_frontier=[frontier_tf]

def submapCallBack (msg):
	global current_submap_poses

	for submap in msg.submap:
		current_submap_poses[
			submap.trajectory_id,
			submap.submap_index] = posemath.fromMsg(submap.pose)

def mapCallBack(data):
	global mapData
	mapData=data

def globalMap(data):
	global global1,globalmaps,litraIndx,namespace_init_count,n_robots
	global1=data
	if n_robots>1:
		indx=int(data._connection_header['topic'][litraIndx])-namespace_init_count
	elif n_robots==1:
		indx=0
	globalmaps[indx]=data


# Node----------------------------------------------
def node():
	print ('usao u glavni')
	global mapData,global1,global2,global3,globalmaps,current_frontier, all_frontiers, litraIndx,n_robots,namespace_init_count
	rospy.init_node('filter', anonymous=False)
	# fetching all parameters
	map_topic= rospy.get_param('~map_topic','/map')
	threshold= rospy.get_param('~costmap_clearing_threshold',50)
	info_radius= rospy.get_param('~info_radius',1)          #this can be smaller than the laser scanner range, >> smaller >>less computation time>> too small is not good, info gain won't be accurate
	goals_topic= rospy.get_param('~goals_topic','/detected_points')
	transform_topic=rospy.get_param ('~transform_topic', '/transformed_points')
	submap_topic=rospy.get_param ('~submap_topic', '/used_submaps')
	n_robots = rospy.get_param('~n_robots',1)
	namespace_list = rospy.get_param('~namespace_list',['alpha'])
	namespace_init_count = rospy.get_param('namespace_init_count',1)
	rateHz = rospy.get_param('~rate',100)
	litraIndx=len(namespace_list)
	rate = rospy.Rate(rateHz)
	#-------------------------------------------
	rospy.Subscriber(map_topic, OccupancyGrid, mapCallBack)

	#---------------------------------------------------------------------------------------------------------------

	for i in range(0,n_robots):
		globalmaps.append(OccupancyGrid())

	if len(namespace_list) > 0:
		for i in range(0,len(namespace_list)):
			print(namespace_list[i])
			rospy.Subscriber(namespace_list[i]+'/move_base/global_costmap/costmap', OccupancyGrid, globalMap)
	elif len(namespace_list)==0:
		rospy.Subscriber('/move_base/global_costmap/costmap', OccupancyGrid, globalMap)
	print ('usao u glavni2')
	#wait if map is not received yet
	while (len(mapData.data)<1):
		pass
	print ('usao u glavni3')
	#wait if any of robots' global costmap map is not received yet
	for i in range(0,n_robots):
		while (len(globalmaps[i].data)<1):
			pass
	global_frame="/"+mapData.header.frame_id

	print ('usao u glavni4')
	tfLisn=tf.TransformListener()
	rospy.sleep(2)
	if len(namespace_list) > 0:
		for i in range(0,len(namespace_list)):
			tfLisn.waitForTransform(global_frame[1:], namespace_list[i]+'/base_link', rospy.Time(0),rospy.Duration(10.0))
	elif len(namespace_list)==0:
		tfLisn.waitForTransform(global_frame[1:], '/base_link', rospy.Time(0),rospy.Duration(10.0))

	rospy.Subscriber(submap_topic,SubmapList, submapCallBack)
	rospy.Subscriber(transform_topic, FrontierTF, transformCallBack)
	#rospy.Subscriber(goals_topic, PointStamped, callback=callBack,callback_args=[tfLisn,global_frame[1:]])


	pub = rospy.Publisher('frontiers', Marker, queue_size=10)
	pub2 = rospy.Publisher('centroids', Marker, queue_size=10)
	filterpub = rospy.Publisher('filtered_points', PointArray, queue_size=10)
	filterpub2=rospy.Publisher('filtered_struct', FrontierTF, queue_size=10)

	rospy.loginfo("the map and global costmaps are received")


	# wait if no frontier is received yet
	while len(current_frontier)<1:
		pass


	points=Marker()
	points_clust=Marker()
	#Set the frame ID and timestamp.  See the TF tutorials for information on these.
	points.header.frame_id= mapData.header.frame_id
	points.header.stamp= rospy.Time.now()

	points.ns= "markers2"
	points.id = 0

	points.type = Marker.POINTS
	#Set the marker action for latched frontiers.  Options are ADD, DELETE, and new in ROS Indigo: 3 (DELETEALL)
	points.action = Marker.ADD;

	points.pose.orientation.w = 1.0

	points.scale.x=0.2
	points.scale.y=0.2

	points.color.r = 255.0/255.0
	points.color.g = 255.0/255.0
	points.color.b = 0.0/255.0

	points.color.a=1;
	points.lifetime = rospy.Duration();

	p=Point()

	p.z = 0;

	pp=[]
	pl=[]

	points_clust.header.frame_id= mapData.header.frame_id
	points_clust.header.stamp= rospy.Time.now()

	points_clust.ns= "markers3"
	points_clust.id = 4

	points_clust.type = Marker.POINTS

	#Set the marker action for centroids.  Options are ADD, DELETE, and new in ROS Indigo: 3 (DELETEALL)
	points_clust.action = Marker.ADD;

	points_clust.pose.orientation.w = 1.0;

	points_clust.scale.x=0.2;
	points_clust.scale.y=0.2;
	points_clust.color.r = 0.0/255.0
	points_clust.color.g = 255.0/255.0
	points_clust.color.b = 0.0/255.0
	points_clust.color.a=1;
	points_clust.lifetime = rospy.Duration();


	temppoint=PointStamped()
	temppoint.header.frame_id= mapData.header.frame_id
	temppoint.header.stamp=rospy.Time(0)
	temppoint.point.z=0.0

	arraypoints=PointArray()
	tempPoint=Point()
	tempPoint.z=0.0
	#-------------------------------------------------------------------------
	#---------------------     Main   Loop     -------------------------------
	#-------------------------------------------------------------------------
	while not rospy.is_shutdown():
		#-------------------------------------------------------------------------
		#SVE FRONTIERE PONOVNO TRANSFORMIRATI, U SVAKOM PROLAZU

		my_frontiers=copy(current_frontier)
		transform(my_frontiers)

		transform(all_frontiers)
		all_frontiers.extend(my_frontiers)

		#print ('koje dobivam', all_frontiers)
		all_centroids=copy(all_frontiers)
		#print('centroidi su:', all_centroids[0])
		#-------------------------------------------------------------------------
		#clearing old frontiers
		z=0
		#print ('duljina frontiera',len(all_frontiers))
		for centroid in all_centroids:
			cond=False
			temppoint.point.x=centroid.projected.x
			temppoint.point.y=centroid.projected.y

			for i in range(0,len(namespace_list)):
				transformedPoint=tfLisn.transformPoint(globalmaps[i].header.frame_id,temppoint)
				x=array([transformedPoint.point.x,transformedPoint.point.y])
				cond=(gridValue(globalmaps[i],x)>threshold) or cond
			if (cond or (informationGain(mapData,[centroid.projected.x,centroid.projected.y],info_radius*0.5))<0.3):
				all_centroids=list(delete(all_centroids, (z), axis=0))
				z=z-1
			#print ('deleted centroid')
			z+=1
		print("resize frontiers from %d to %d"%(len(all_frontiers),len(all_centroids)))
		#-------------------------------------------------------------------------

		#------------------------------------------------------------------------
		#publishing

		arraypoints.points=[]
		#arraystruct=[]
		cnt=0

		for centroid in all_centroids:

			tempPoint.x=centroid.projected.x
			tempPoint.y=centroid.projected.y
			arraypoints.points.append(copy(tempPoint))
			#arraystruct.append(copy(centroid))
			cnt+=1

		filterpub.publish(arraypoints)
		#filterpub2.publish(arraystruct)
		print("Published transformed centroids:"+str(cnt))
		#-------------------------------------------------------------------------
		pp=[]
		for q in all_centroids:
			p.x=q.projected.x
			p.y=q.projected.y
			pp.append(copy(p))
		points_clust.points=pp


		pub2.publish(points_clust)


		print("delete old frontiers")
		z=0
		for frontier in all_frontiers:
			cond=False
			temppoint.point.x=frontier.projected.x
			temppoint.point.y=frontier.projected.y

			for i in range(0,len(namespace_list)):
				transformedPoint=tfLisn.transformPoint(globalmaps[i].header.frame_id,temppoint)
				x=array([transformedPoint.point.x,transformedPoint.point.y])
				cond=(gridValue(globalmaps[i],x)>threshold) or cond
			if (cond or (informationGain(mapData,[frontier.projected.x,frontier.projected.y],info_radius*0.5))<0.2):
				all_frontiers=list(delete(all_frontiers, (z), axis=0))
				z=z-1
			z+=1
		pp=[]
		for q in all_frontiers:
			p.x=q.projected.x
			p.y=q.projected.y
			pp.append(copy(p))
		points.points=pp
		pub.publish(points)
		rate.sleep()

#-------------------------------------------------------------------------

if __name__ == '__main__':
	try:
		node()

	except rospy.ROSInterruptException:
		pass
