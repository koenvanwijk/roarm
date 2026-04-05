#!/usr/bin/env python3
"""Direct WebRTC test with verbose logging."""

import asyncio
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
import aiohttp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_direct_connection():
    """Test direct WebRTC connection without our wrapper classes."""
    
    # Create two peer connections
    pc1 = RTCPeerConnection()
    pc2 = RTCPeerConnection()
    
    # Create data channel on pc1
    channel1 = pc1.createDataChannel("test")
    
    @channel1.on("open")
    def on_open():
        logger.info("✅ Channel 1 opened!")
        channel1.send("Hello from sender!")
    
    # Handle data channel on pc2
    @pc2.on("datachannel")
    def on_datachannel(channel):
        logger.info(f"✅ Channel 2 received: {channel.label}")
        
        @channel.on("message")
        def on_message(message):
            logger.info(f"✅ Received message: {message}")
    
    # Create offer
    offer = await pc1.createOffer()
    await pc1.setLocalDescription(offer)
    logger.info("Created offer")
    
    # Set remote description on pc2
    await pc2.setRemoteDescription(pc1.localDescription)
    logger.info("Set remote description on pc2")
    
    # Create answer
    answer = await pc2.createAnswer()
    await pc2.setLocalDescription(answer)
    logger.info("Created answer")
    
    # Set remote description on pc1
    await pc1.setRemoteDescription(pc2.localDescription)
    logger.info("Set remote description on pc1")
    
    # Wait for channel to open
    await asyncio.sleep(2)
    
    logger.info("✓ Test complete")
    
    await pc1.close()
    await pc2.close()

if __name__ == "__main__":
    asyncio.run(test_direct_connection())
