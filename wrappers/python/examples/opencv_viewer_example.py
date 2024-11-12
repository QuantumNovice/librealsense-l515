## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2015-2017 Intel Corporation. All Rights Reserved.

###############################################
##      Open CV and Numpy integration        ##
###############################################

import pyrealsense2 as rs
import numpy as np
import cv2


## Find out resolution first
import pyrealsense2 as rs

def get_camera_stream_resolutions():
    # Initialize the pipeline and start streaming
    pipeline = rs.pipeline()
    config = rs.config()
    pipeline_profile = pipeline.start(config)
    
    # Dictionary to store resolutions
    resolutions = {}

    # Get the active streams and their resolutions
    for sensor in pipeline_profile.get_device().sensors:
        for stream_profile in sensor.profiles:
            video_profile = stream_profile.as_video_stream_profile()
            if video_profile:
                stream_type = str(stream_profile.stream_type())
                width = video_profile.width()
                height = video_profile.height()
                fps = video_profile.fps()
                
                # Store resolution details in the dictionary
                resolutions[stream_type] = {
                    'width': width,
                    'height': height,
                    'fps': fps
                }

    # Stop the pipeline when done
    pipeline.stop()
    
    return resolutions

# Example usage
# {'stream.confidence': {'width': 320, 'height': 240, 'fps': 30}, 'stream.infrared': {'width': 320, 'height': 240, 'fps': 30}, 'stream.depth': {'width': 320, 'height': 240, 'fps': 30}, 'stream.color': {'width': 640, 'height': 360, 'fps': 6}}
resolutions = get_camera_stream_resolutions()
print(resolutions)



# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()
device_product_line = str(device.get_info(rs.camera_info.product_line))

found_rgb = False
for s in device.sensors:
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The demo requires Depth camera with Color sensor")
    exit(0)

config.enable_stream(rs.stream.depth, resolutions['stream.depth']['width'], resolutions['stream.depth']['height'], rs.format.z16, 30)
config.enable_stream(rs.stream.color, resolutions['stream.color']['width'], resolutions['stream.color']['height'], rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

try:
    while True:

        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        depth_colormap_dim = depth_colormap.shape
        color_colormap_dim = color_image.shape

        # If depth and color resolutions are different, resize color image to match depth image for display
        if depth_colormap_dim != color_colormap_dim:
            resized_color_image = cv2.resize(color_image, dsize=(depth_colormap_dim[1], depth_colormap_dim[0]), interpolation=cv2.INTER_AREA)
            images = np.hstack((resized_color_image, depth_colormap))
        else:
            images = np.hstack((color_image, depth_colormap))

        # Show images
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)
        cv2.waitKey(1)

finally:

    # Stop streaming
    pipeline.stop()
