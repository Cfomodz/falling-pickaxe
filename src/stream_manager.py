import cv2
import numpy as np
import pygame
import threading
import subprocess
import os
import time
from queue import Queue

class StreamManager:
    def __init__(self, config):
        self.config = config
        self.streaming = False
        self.stream_process = None
        self.frame_queue = Queue(maxsize=30)  # Buffer frames
        self.stream_thread = None
        
        # Stream settings
        self.fps = 30
        self.width = 720   # 9:16 aspect ratio
        self.height = 1280
        self.bitrate = "2500k"  # 2.5 Mbps for good quality
        
        # YouTube RTMP settings
        self.rtmp_url = "rtmp://a.rtmp.youtube.com/live2/"
        self.stream_key = None
        
        print("StreamManager initialized")
    
    def set_stream_key(self, stream_key):
        """Set the YouTube stream key"""
        self.stream_key = stream_key
        print(f"Stream key set: {stream_key[:10]}...")
    
    def start_streaming(self):
        """Start the streaming process"""
        if self.streaming or not self.stream_key:
            print("Already streaming or no stream key set")
            return False
            
        print("Starting YouTube stream...")
        
        # FFmpeg command for YouTube RTMP streaming
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output files
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',  # Read from stdin
            '-c:v', 'libx264',
            '-preset', 'veryfast',  # Fast encoding for real-time
            '-tune', 'zerolatency',
            '-crf', '23',  # Good quality
            '-pix_fmt', 'yuv420p',
            '-b:v', self.bitrate,
            '-maxrate', self.bitrate,
            '-bufsize', '5000k',
            '-g', str(self.fps * 2),  # Keyframe interval
            '-f', 'flv',
            f'{self.rtmp_url}{self.stream_key}'
        ]
        
        try:
            self.stream_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            self.streaming = True
            
            # Start frame processing thread
            self.stream_thread = threading.Thread(target=self._stream_worker)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            print("✅ YouTube stream started successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start stream: {e}")
            return False
    
    def stop_streaming(self):
        """Stop the streaming process"""
        if not self.streaming:
            return
            
        print("Stopping YouTube stream...")
        self.streaming = False
        
        if self.stream_process:
            try:
                self.stream_process.stdin.close()
                self.stream_process.terminate()
                self.stream_process.wait(timeout=5)
            except:
                self.stream_process.kill()
            
            self.stream_process = None
        
        if self.stream_thread:
            self.stream_thread.join(timeout=2)
            self.stream_thread = None
        
        print("✅ Stream stopped")
    
    def _stream_worker(self):
        """Worker thread that sends frames to FFmpeg"""
        while self.streaming:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=0.1)
                    if self.stream_process and self.stream_process.stdin:
                        self.stream_process.stdin.write(frame.tobytes())
                        self.stream_process.stdin.flush()
                else:
                    time.sleep(0.01)  # Small delay if no frames
            except Exception as e:
                if self.streaming:  # Only log if we should still be streaming
                    print(f"Stream worker error: {e}")
                break
    
    def capture_frame(self, pygame_surface):
        """Capture a pygame surface and add to stream queue"""
        if not self.streaming:
            return
            
        try:
            # Convert pygame surface to numpy array
            frame_array = pygame.surfarray.array3d(pygame_surface)
            
            # Pygame uses (width, height, 3), OpenCV uses (height, width, 3)
            frame_array = np.transpose(frame_array, (1, 0, 2))
            
            # Convert RGB to BGR for OpenCV
            frame_array = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            
            # Resize to streaming resolution (9:16 aspect ratio)
            frame_resized = cv2.resize(frame_array, (self.width, self.height), 
                                     interpolation=cv2.INTER_LINEAR)
            
            # Convert back to RGB for FFmpeg
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Add to queue (drop frame if queue is full)
            if not self.frame_queue.full():
                self.frame_queue.put(frame_rgb, block=False)
            else:
                # Drop oldest frame and add new one
                try:
                    self.frame_queue.get(block=False)
                    self.frame_queue.put(frame_rgb, block=False)
                except:
                    pass
                    
        except Exception as e:
            print(f"Frame capture error: {e}")
    
    def is_streaming(self):
        """Check if currently streaming"""
        return self.streaming and self.stream_process is not None
    
    def get_stream_stats(self):
        """Get basic streaming statistics"""
        if not self.is_streaming():
            return {"status": "offline"}
            
        return {
            "status": "live",
            "fps": self.fps,
            "resolution": f"{self.width}x{self.height}",
            "bitrate": self.bitrate,
            "queue_size": self.frame_queue.qsize()
        }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_streaming()

# Utility functions for stream management
def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def install_ffmpeg_replit():
    """Install FFmpeg in Replit environment"""
    print("Installing FFmpeg for streaming...")
    try:
        # Install via nix-env in Replit
        subprocess.run(['nix-env', '-iA', 'nixpkgs.ffmpeg'], check=True)
        print("✅ FFmpeg installed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to install FFmpeg: {e}")
        print("Please add 'ffmpeg' to your .replit packages list")
        return False