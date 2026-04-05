"""WebRTC Receiver - Teleoperator that receives actions via WebRTC.

This is used on the FOLLOWER computer as the --teleop.type.
It receives actions via WebRTC from the remote leader and provides them
to the local robot.

Usage on Follower Computer:
    lerobot-teleoperate \\
      --robot.type lerobot_robot_roarm \\
      --robot.port /dev/ttyUSB1 \\
      --teleop.type lerobot_teleoperator_webrtc_receiver \\
      --teleop.signaling_server "192.168.1.100:8080"
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
import numpy as np

from lerobot.processor import RobotAction, RobotObservation
from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.teleoperators.config import TeleoperatorConfig

logger = logging.getLogger(__name__)


@TeleoperatorConfig.register_subclass("lerobot_teleoperator_webrtc_receiver")
@dataclass
class WebRTCReceiverConfig(TeleoperatorConfig):
    """Configuration for WebRTC Receiver."""
    signaling_server: str = "localhost:8080"


class WebRTCReceiver(Teleoperator):
    """WebRTC Receiver - receives actions via WebRTC and provides to robot."""
    
    def __init__(self, config: WebRTCReceiverConfig):
        self.name = config.id or "lerobot_teleoperator_webrtc_receiver"
        super().__init__(config)
        self.config = config
        
        # WebRTC components
        self.signaling_url = config.signaling_server  # e.g. "localhost:8080"
        self.pc = None
        self.http_session = None
        
        # State
        self._connected = False
        self._webrtc_connected = False
        self.actions_received = 0
        self.last_action = None
        
        # Async loop in thread
        self.loop = None
        self.loop_thread = None
        
        logger.info("Initializing WebRTC Receiver")
    
    def connect(self) -> None:
        if self._connected:
            return
        
        logger.info("Connecting WebRTC Receiver...")
        
        self.loop = asyncio.new_event_loop()
        self.loop_thread = Thread(target=self._run_loop, daemon=True)
        self.loop_thread.start()
        
        # Wait for connection
        timeout = 30.0
        start = time.time()
        while not self._webrtc_connected and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        if not self._webrtc_connected:
            raise RuntimeError("WebRTC connection timeout")
        
        self._connected = True
        logger.info("✓ WebRTC Receiver connected")
    
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._setup_webrtc())
        except Exception as e:
            logger.error(f"WebRTC error: {e}")
    
    async def _setup_webrtc(self):
        try:
            # Create HTTP session
            self.http_session = aiohttp.ClientSession()
            
            # Create peer connection with ICE servers for NAT traversal
            configuration = RTCConfiguration(
                iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
            )
            self.pc = RTCPeerConnection(configuration=configuration)
            
            # Handle incoming data channel
            @self.pc.on("datachannel")
            def on_datachannel(channel):
                logger.info(f"DataChannel received: {channel.label}")
                self.channel = channel
                
                @channel.on("open")
                def on_open():
                    logger.info("✓ DataChannel opened")
                    self._webrtc_connected = True
                
                @channel.on("close")
                def on_close():
                    logger.info("DataChannel closed")
                    self._webrtc_connected = False
                
                @channel.on("message")
                def on_message(message):
                    self._handle_action(message)
            
            # Request offer from signaling server (blocking wait)
            logger.info(f"Requesting offer from signaling server: {self.signaling_url}")
            url = f"http://{self.signaling_url}/answer"
            
            # Post a request to get offer - server will wait for sender
            async with self.http_session.post(url, json={
                "peer_id": "receiver",
                "answer": {"type": "waiting", "sdp": ""}  # Placeholder
            }, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Received offer from signaling server")
                    
                    # Set remote description from offer
                    offer = RTCSessionDescription(sdp=data['offer']['sdp'], type='offer')
                    await self.pc.setRemoteDescription(offer)
                    
                    # Create answer
                    answer = await self.pc.createAnswer()
                    await self.pc.setLocalDescription(answer)
                    
                    # Send answer back to signaling server
                    async with self.http_session.post(url, json={
                        "peer_id": "receiver",
                        "answer": {
                            "type": "answer",
                            "sdp": self.pc.localDescription.sdp
                        }
                    }) as resp2:
                        logger.info(f"Sent answer to signaling server: {resp2.status}")
                else:
                    logger.error(f"Failed to get offer: {response.status}")
                    return
            
            # Keep alive
            while self._connected:
                await asyncio.sleep(0.1)
                
        finally:
            if self.http_session:
                await self.http_session.close()
            if self.pc:
                await self.pc.close()
            if self.ws_session:
                await self.ws_session.close()
    
    def _handle_action(self, message: str):
        """Handle incoming action from WebRTC."""
        try:
            data = json.loads(message)
            if data['type'] == 'action':
                self.actions_received += 1
                
                # Convert action list to dict
                action_list = data['action']
                action_dict = {
                    'shoulder_pan.pos': action_list[0],
                    'shoulder_lift.pos': action_list[1],
                    'elbow_flex.pos': action_list[2],
                    'wrist_flex.pos': action_list[3],
                    'wrist_roll.pos': action_list[4],
                    'gripper.pos': action_list[5],
                }
                
                self.last_action = action_dict
                
        except Exception as e:
            logger.error(f"Error handling action: {e}")
    
    def disconnect(self) -> None:
        self._connected = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.loop_thread:
            self.loop_thread.join(timeout=2.0)
        logger.info("✓ WebRTC Receiver disconnected")
    
    def get_observation(self) -> RobotObservation:
        """Return empty observation."""
        return RobotObservation(**{'observation.state': np.zeros(6, dtype=np.float32)})
    
    def get_action(self) -> RobotAction:
        """Get action received via WebRTC."""
        if not self._connected:
            raise RuntimeError("WebRTC receiver not connected")
        
        # Return last received action or zeros
        if self.last_action is None:
            action_dict = {
                'shoulder_pan.pos': 0.0,
                'shoulder_lift.pos': 0.0,
                'elbow_flex.pos': 0.0,
                'wrist_flex.pos': 0.0,
                'wrist_roll.pos': 0.0,
                'gripper.pos': 0.0,
            }
        else:
            action_dict = self.last_action.copy()
        
        return RobotAction(**action_dict)
    
    def calibrate(self, *args: Any, **kwargs: Any) -> None:
        pass
    
    def is_connected(self) -> bool:
        return self._connected and self._webrtc_connected
    
    def is_calibrated(self) -> bool:
        return True
    
    def configure(self) -> None:
        pass
    
    def send_feedback(self, feedback: Any) -> None:
        pass
    
    @property
    def action_features(self) -> dict[str, Any]:
        return {
            'action': {
                'dtype': 'float32',
                'shape': (6,),
                'names': ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper']
            }
        }
    
    @property
    def feedback_features(self) -> dict[str, Any]:
        return {}
