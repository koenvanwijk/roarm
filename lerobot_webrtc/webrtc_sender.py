"""WebRTC Sender - Robot that forwards actions via WebRTC.

This is used on the LEADER computer as the --robot.type.
It receives actions from the local teleoperator and sends them via WebRTC
to the remote follower.

Usage on Leader Computer:
    lerobot-teleoperate \\
      --robot.type lerobot_robot_webrtc_sender \\
      --robot.signaling_server "192.168.1.100:8080" \\
      --teleop.type lerobot_robot_roarm \\
      --teleop.port /dev/ttyUSB0
"""

import asyncio
import json
import logging
import time
from threading import Thread
from typing import Any
from dataclasses import dataclass

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
import aiohttp

from lerobot.robots import Robot, RobotConfig

logger = logging.getLogger(__name__)


@RobotConfig.register_subclass("lerobot_robot_webrtc_sender")
@dataclass
class WebRTCSenderConfig(RobotConfig):
    """Configuration for WebRTC Sender."""
    signaling_server: str = "localhost:8080"


class WebRTCSender(Robot):
    """WebRTC Sender - receives actions from leader and forwards via WebRTC."""
    
    config_class = WebRTCSenderConfig
    name = "lerobot_robot_webrtc_sender"
    
    def __init__(self, config: WebRTCSenderConfig):
        super().__init__(config)
        self.config = config
        
        # WebRTC components  
        self.signaling_url = config.signaling_server  # e.g. "localhost:8080"
        self.pc = None
        self.data_channel = None
        self.http_session = None
        
        # State
        self._is_connected = False
        self._webrtc_connected = False
        self.actions_sent = 0
        
        # Async loop in thread
        self.loop = None
        self.loop_thread = None
        
        logger.info("Initializing WebRTC Sender")
    
    @property
    def observation_features(self) -> dict:
        return {}
    
    @property
    def action_features(self) -> dict:
        return {}
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected and self._webrtc_connected
    
    @property
    def is_calibrated(self) -> bool:
        return True
    
    def connect(self, calibrate: bool = True) -> None:
        if self._is_connected:
            return
        
        logger.info("🔌 Connecting WebRTC Sender...")
        
        self.loop = asyncio.new_event_loop()
        self.loop_thread = Thread(target=self._run_loop, daemon=True)
        self.loop_thread.start()
        
        logger.info("⏳ Waiting for WebRTC connection...")
        # Wait for connection
        timeout = 30.0
        start = time.time()
        while not self._webrtc_connected and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        if not self._webrtc_connected:
            logger.error("❌ WebRTC connection timeout")
            raise RuntimeError("WebRTC connection timeout")
        
        self._is_connected = True
        logger.info("✅ WebRTC Sender connected")
    
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            logger.info("🚀 Starting WebRTC sender async loop...")
            self.loop.run_until_complete(self._setup_webrtc())
        except Exception as e:
            logger.error(f"❌ WebRTC error: {e}", exc_info=True)
    
    async def _setup_webrtc(self):
        try:
            # Create HTTP session
            self.http_session = aiohttp.ClientSession()
            
            # Create peer connection with ICE servers for NAT traversal
            configuration = RTCConfiguration(
                iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
            )
            self.pc = RTCPeerConnection(configuration=configuration)
            self.data_channel = self.pc.createDataChannel("robot_actions")
            
            @self.data_channel.on("open")
            def on_open():
                logger.info("✓ DataChannel opened")
                self._webrtc_connected = True
            
            @self.data_channel.on("close")
            def on_close():
                logger.info("DataChannel closed")
                self._webrtc_connected = False
            
            # Create offer
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            # Send offer to signaling server
            logger.info(f"Sending offer to signaling server: {self.signaling_url}")
            url = f"http://{self.signaling_url}/offer"
            
            async with self.http_session.post(url, json={
                "peer_id": "sender",
                "offer": {
                    "type": "offer",
                    "sdp": self.pc.localDescription.sdp
                }
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Received answer from signaling server")
                    
                    # Set remote description from answer
                    answer = RTCSessionDescription(sdp=data['answer']['sdp'], type='answer')
                    await self.pc.setRemoteDescription(answer)
                    logger.info("✓ WebRTC connection established")
                else:
                    logger.error(f"Failed to send offer: {response.status}")
                    return
            
            # Keep alive
            while self._is_connected:
                await asyncio.sleep(0.1)
                
        finally:
            if self.http_session:
                await self.http_session.close()
            if self.pc:
                await self.pc.close()
    
    def disconnect(self) -> None:
        self._is_connected = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.loop_thread:
            self.loop_thread.join(timeout=2.0)
        logger.info("✓ WebRTC Sender disconnected")
    
    def calibrate(self) -> None:
        pass
    
    def configure(self) -> None:
        pass
    
    def get_observation(self) -> dict:
        return {}
    
    def send_action(self, action: dict) -> None:
        """Receive action from teleoperator and send via WebRTC."""
        if not self._webrtc_connected:
            return
        
        # Convert action dict to list
        action_list = [
            action.get('shoulder_pan.pos', 0.0),
            action.get('shoulder_lift.pos', 0.0),
            action.get('elbow_flex.pos', 0.0),
            action.get('wrist_flex.pos', 0.0),
            action.get('wrist_roll.pos', 0.0),
            action.get('gripper.pos', 0.0),
        ]
        
        message = json.dumps({
            'type': 'action',
            'action': action_list,
            'timestamp': time.time(),
            'sequence': self.actions_sent
        })
        
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._send(message), self.loop)
        
        self.actions_sent += 1
    
    async def _send(self, message: str):
        try:
            if self.data_channel and self.data_channel.readyState == "open":
                self.data_channel.send(message)
        except Exception as e:
            logger.error(f"Send error: {e}")
