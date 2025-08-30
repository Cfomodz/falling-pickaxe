import subprocess
import time
import threading
import numpy as np
import cv2

class AutoStreamCreator:
    """Creates and manages automatic YouTube streams without needing existing stream ID"""
    
    def __init__(self, stream_key: str, stream_config: dict):
        self.stream_key = stream_key
        self.width = int(stream_config.get('width', 720))
        self.height = int(stream_config.get('height', 1280))
        self.fps = int(stream_config.get('fps', 30))
        self.bitrate = stream_config.get('bitrate', '2500k')
        
        self.streaming = False
        self.stream_process = None
        self.stream_thread = None
        
        # YouTube RTMP endpoint
        self.rtmp_url = "rtmp://a.rtmp.youtube.com/live2/"
        
        print(f"AutoStreamCreator initialized: {self.width}x{self.height} @ {self.fps}fps")
    
    def start_black_stream(self):
        """Start streaming a black screen to YouTube to initialize the stream"""
        if self.streaming:
            print("Stream already active")
            return True
            
        print("🎥 Starting black screen stream to YouTube...")
        
        # FFmpeg command to stream black video
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite outputs
            '-f', 'lavfi',
            '-i', f'color=c=black:size={self.width}x{self.height}:rate={self.fps}',  # Black video
            '-f', 'lavfi', 
            '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',  # Silent audio
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-b:v', self.bitrate,
            '-maxrate', self.bitrate,
            '-bufsize', '5000k',
            '-g', str(self.fps * 2),  # GOP size
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-f', 'flv',
            f'{self.rtmp_url}{self.stream_key}'
        ]
        
        try:
            print("📡 Connecting to YouTube RTMP...")
            self.stream_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            # Give it a moment to connect
            time.sleep(3)
            
            # Check if process is still running (successful connection)
            if self.stream_process.poll() is None:
                self.streaming = True
                print("✅ Black stream started successfully!")
                print("🔴 YouTube stream is now LIVE")
                print("💡 Stream will be visible on your YouTube channel")
                return True
            else:
                error_output = self.stream_process.stderr.read().decode()
                print(f"❌ Stream failed to start: {error_output}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start stream: {e}")
            return False
    
    def start_starting_soon_stream(self):
        """Start streaming a 'Starting Soon' screen"""
        if self.streaming:
            return True
            
        print("🎬 Starting 'Starting Soon' stream...")
        
        # Create starting soon image
        starting_soon_cmd = [
            'ffmpeg',
            '-y',
            '-f', 'lavfi',
            '-i', f'color=c=black:size={self.width}x{self.height}:rate={self.fps}',
            '-f', 'lavfi',
            '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-vf', f'drawtext=fontfile=/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf:text=\'Starting Soon...\':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2',
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-b:v', self.bitrate,
            '-maxrate', self.bitrate,
            '-bufsize', '5000k',
            '-g', str(self.fps * 2),
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-f', 'flv',
            f'{self.rtmp_url}{self.stream_key}'
        ]
        
        try:
            self.stream_process = subprocess.Popen(
                starting_soon_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(3)
            
            if self.stream_process.poll() is None:
                self.streaming = True
                print("✅ 'Starting Soon' stream active!")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Starting soon stream failed: {e}")
            return False
    
    def stop_stream(self):
        """Stop the current stream"""
        if not self.streaming:
            return
            
        print("🛑 Stopping auto-stream...")
        self.streaming = False
        
        if self.stream_process:
            try:
                self.stream_process.terminate()
                self.stream_process.wait(timeout=5)
            except:
                self.stream_process.kill()
            self.stream_process = None
        
        print("📴 Auto-stream stopped")
    
    def is_streaming(self):
        """Check if stream is active"""
        return self.streaming and self.stream_process and self.stream_process.poll() is None
    
    def get_stream_status(self):
        """Get current stream status"""
        if self.is_streaming():
            return {
                'status': 'live',
                'resolution': f'{self.width}x{self.height}',
                'fps': self.fps,
                'bitrate': self.bitrate,
                'rtmp_url': f'{self.rtmp_url}[key]'
            }
        else:
            return {'status': 'offline'}
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop_stream()


def create_and_start_stream(stream_key: str, stream_type: str = "black") -> AutoStreamCreator:
    """Create and start an automatic stream"""
    
    config = {
        'width': 720,
        'height': 1280, 
        'fps': 30,
        'bitrate': '2500k'
    }
    
    creator = AutoStreamCreator(stream_key, config)
    
    if stream_type == "black":
        success = creator.start_black_stream()
    elif stream_type == "starting_soon":
        success = creator.start_starting_soon_stream()
    else:
        print(f"Unknown stream type: {stream_type}")
        return None
    
    if success:
        print("🎯 Auto-stream created successfully!")
        print("💡 Your YouTube stream is now live and discoverable")
        print("🎮 Game can now detect and connect to this stream")
        return creator
    else:
        print("❌ Failed to create auto-stream")
        return None


# Usage example:
if __name__ == "__main__":
    stream_key = "your-youtube-stream-key-here"
    
    print("🚀 Creating automatic YouTube stream...")
    creator = create_and_start_stream(stream_key, "black")
    
    if creator:
        print("✅ Stream is live!")
        print("Status:", creator.get_stream_status())
        
        # Keep running for demonstration
        try:
            print("🔴 Stream running... Press Ctrl+C to stop")
            while creator.is_streaming():
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n🛑 Stopping stream...")
            creator.stop_stream()
    else:
        print("❌ Failed to start stream")