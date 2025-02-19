#!/user/bin/env python
import rospy
import mavros
from geometry_msgs.msg import PoseStamped,Twist,Point
from mavros_msgs.srv import SetMode
from mavros_msgs.msg import State
from mavros_msgs.srv import *
import time
current_state = State()
previous_state = State()
current_posestamped=PoseStamped()
def takeoff():
	rospy.wait_for_service('mavros/cmd/takeoff')
	try:
		takeoff_handler = rospy.ServiceProxy('mavros/cmd/takeoff', CommandTOL)
		takeoff_handler()
	except rospy.ServiceException, e:
		print "Service takeoff call failed: %s"%e


def state_cb(msg):
	global current_state
	current_state = msg
def posestamped_cb(data):
	global current_posestamped
	current_posestamped=data	

if __name__ == '__main__':
	rospy.init_node('offboard_node',anonymous=True)
	rate = rospy.Rate(20)
	state_sub = rospy.Subscriber("mavros/state",State,state_cb)
	posestamped_sub=rospy.Subscriber("mavros/local_position/pose",PoseStamped,posestamped_cb)
	pub = rospy.Publisher("mavros/setpoint_position/local",PoseStamped,queue_size=10)
	arming_handler = rospy.ServiceProxy("mavros/cmd/arming",CommandBool)
	set_mode_handler = rospy.ServiceProxy("mavros/set_mode",SetMode)	

	circle = PoseStamped()

	while not current_state.connected:
		rate.sleep()
	arming_handler(True)
	takeoff()
	pose = PoseStamped()	

	current_posestamped.pose.position.x = 0	
	current_posestamped.pose.position.y = 0
	current_posestamped.pose.position.z = 1
	
	if current_posestamped.pose.position.z>0:
	 circle.pose.position.x = 0
	 circle.pose.position.y = 0
	 circle.pose.position.z = 2
	 time.sleep(60)
	elif current_posestamped.pose.position.z>1:
		circle.pose.position.x = 0
		circle.pose.position.y = 0
		circle.pose.position.z = 0



	for i in range(100):
		pub.publish(pose)
		rate.sleep()

	last_request = rospy.Time.now()

	try:
		while not rospy.is_shutdown():
			if (current_state.mode != "OFFBOARD") and (rospy.Time.now() - last_request > rospy.Duration(0.05)):
				set_mode_handler(base_mode=0, custom_mode="OFFBOARD") 
				last_request = rospy.Time.now()

			else:
				if not current_state.armed and (rospy.Time.now() - last_request > rospy.Duration(0.05)):
					arming_handler(True) 
					last_request = rospy.Time.now()

			if previous_state.armed != current_state.armed:
				rospy.loginfo("%r" % current_state.armed) 

			if previous_state.mode != current_state.mode:
				rospy.loginfo("%r"%current_state.mode)

			previous_state = current_state
			pose.header.stamp = rospy.Time.now()
			pub.publish(pose)
			rate.sleep()

	except KeyboardInterrupt:
		print "Changing to Stabilized"
		set_mode_handler(base_mode=0, custom_mode="STABILIZED")
