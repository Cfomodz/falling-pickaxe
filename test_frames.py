#!/usr/bin/env python3
"""
Test script to generate frames in the exact format the game would use
and stream them directly to YouTube via FFmpeg
"""
import subprocess
import numpy as np
import time
import cv2

# Game frame settings (from stream_manager.py)
width = 720
height = 1280
fps = 30

# YouTube stream key (from config.json - known working)
stream_key = "vjh3-u5sj-pyew-w6s4-c0e1"
rtmp_url = "rtmp://a.rtmp.youtube.com/live2"

def create_test_frame(frame_num):
    """Create a test frame with game-like content"""
    # Create a simple animated frame
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Background gradient
    for y in range(height):
        intensity = int((y / height) * 100 + 50)
        frame[y, :] = [intensity, intensity//2, intensity//3]
    
    # Moving element (simulates falling pickaxe)
    center_x = width // 2
    center_y = (frame_num * 5) % height
    
    # Draw a simple rectangle that moves down
    cv2.rectangle(frame, 
                 (center_x - 20, center_y - 10),
                 (center_x + 20, center_y + 10),
                 (255, 255, 0), -1)
    
    # Frame counter text
    cv2.putText(frame, f"Frame #{frame_num}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return frame

def test_streaming():
    """Test streaming with game-format frames"""
    
    print(f"🎬 Starting test stream to YouTube...")
    print(f"🔴 RTMP URL: {rtmp_url}")
    print(f"🔑 Stream key: {stream_key[:8]}...")
    
    # FFmpeg command (identical to stream_manager.py)
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Overwrite output files
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'rgb24',
        '-s', f'{width}x{height}',
        '-r', str(fps),
        '-i', '-',  # Read from stdin
        '-c:v', 'libx264',
        '-preset', 'veryfast',  # Fast encoding for real-time
        '-tune', 'zerolatency',
        '-crf', '23',  # Good quality
        '-pix_fmt', 'yuv420p',
        '-b:v', '2500k',
        '-maxrate', '2500k',
        '-bufsize', '5000k',
        '-g', str(fps * 2),  # Keyframe interval
        '-f', 'flv',
        f'{rtmp_url}/{stream_key}'
    ]
    
    try:
        print(f"🚀 Starting FFmpeg process...")
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )
        
        print(f"📤 Sending test frames...")
        
        # Send 900 frames (30 seconds at 30fps)
        for frame_num in range(900):
            # Create frame in RGB format (like game does)
            frame_rgb = create_test_frame(frame_num)
            
            # Send frame to FFmpeg
            try:
                process.stdin.write(frame_rgb.tobytes())
                process.stdin.flush()
                
                if frame_num % 30 == 0:  # Every second
                    print(f"📤 Sent frame {frame_num}/900 ({frame_num//30}s)")
                
            except BrokenPipeError:
                print("❌ FFmpeg process died!")
                break
            
            # Maintain 30 FPS timing
            time.sleep(1/fps)
        
        # Close stdin and check for errors
        process.stdin.close()
        stdout, stderr = process.communicate()
        
        print("✅ Test streaming completed!")
        if stderr:
            print("📋 FFmpeg stderr output:")
            print(stderr.decode())
        print(f"📺 Check: https://youtube.com/watch?v=jeUiHXdHWAg")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_streaming()