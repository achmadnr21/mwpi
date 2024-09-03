import numpy as np
import cv2
from picamera2 import Picamera2
from datetime import datetime
import subprocess

IMSIZE = (640, 480)
FPS = 15  # Adjust to your desired frame rate

# Initialize the PiCamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": IMSIZE}))
picam2.start()

stream_ip = '192.168.18.130'
stream_id = 'mwc1'

# Command to pipe video to ffmpeg for RTMP streaming
command = [
    'ffmpeg',
    '-y',  # overwrite output files
    '-f', 'rawvideo',
    '-pix_fmt', 'rgb24',  # Changed to rgb24 to match XRGB8888 format
    '-s', f'{IMSIZE[0]}x{IMSIZE[1]}',  # size of the input video
    '-r', str(FPS),  # frames per second
    '-i', '-',  # input comes from a pipe
    '-c:v', 'libx264',  # video codec
    '-preset', 'ultrafast',
    '-b:v', '500k',  # Adjust bitrate as needed for better quality
    '-maxrate', '500k',
    '-bufsize', '1000k',
    '-f', 'flv',  # format for RTMP
    f'rtmp://{stream_ip}:1935/markaswalet-live/{stream_id}'  # RTMP server URL
]

# Start ffmpeg subprocess
ffmpeg = subprocess.Popen(command, stdin=subprocess.PIPE)

try:
    while True:
        # Capture video frame
        frame = picam2.capture_array()
        if frame is None:
            break

        frame_rgb = frame[:, :, 0:3]  # Extract RGB channels from XRGB8888

        # Convert from numpy array to OpenCV image format
        frame_rgb = np.asarray(frame_rgb, dtype=np.uint8)

        # Get the current time
        current_time = datetime.now().strftime("%H:%M:%S")
        # Write it
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        frame_bgr = cv2.flip(frame_bgr, -1)
        cv2.putText(frame_bgr, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        
        # Write the frame to ffmpeg's stdin
        ffmpeg.stdin.write(frame_bgr.tobytes())

except KeyboardInterrupt:
    print("Streaming stopped by user")

finally:
    # Clean up
    ffmpeg.stdin.close()
    ffmpeg.wait()
    picam2.stop()
