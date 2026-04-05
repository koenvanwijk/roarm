#!/usr/bin/env python3
"""WebRTC Signaling Server - Coordinates peer connections between sender and receiver."""

import argparse
import asyncio
import json
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store waiting peers
peers = {}


async def handle_offer(request):
    """Handle offer from sender and wait for answer from receiver."""
    data = await request.json()
    peer_id = data.get("peer_id", "sender")
    
    logger.info(f"Received offer from {peer_id}")
    
    # Store the offer
    peers[peer_id] = {
        "type": "offer",
        "offer": data["offer"],
        "ice_candidates": data.get("ice_candidates", [])
    }
    
    # Wait for answer (with timeout)
    for _ in range(300):  # 30 second timeout
        await asyncio.sleep(0.1)
        if "receiver" in peers and peers["receiver"]["type"] == "answer":
            answer_data = peers["receiver"]
            logger.info(f"Sending answer to {peer_id}")
            del peers["receiver"]  # Clean up
            return web.json_response(answer_data)
    
    return web.json_response({"error": "Timeout waiting for answer"}, status=408)


async def handle_answer(request):
    """Handle answer from receiver and return offer from sender."""
    data = await request.json()
    peer_id = data.get("peer_id", "receiver")
    
    logger.info(f"Received answer from {peer_id}")
    
    # Store the answer
    peers[peer_id] = {
        "type": "answer",
        "answer": data["answer"],
        "ice_candidates": data.get("ice_candidates", [])
    }
    
    # Wait for offer
    for _ in range(300):  # 30 second timeout
        await asyncio.sleep(0.1)
        if "sender" in peers and peers["sender"]["type"] == "offer":
            offer_data = peers["sender"]
            logger.info(f"Sending offer to {peer_id}")
            del peers["sender"]  # Clean up
            return web.json_response(offer_data)
    
    return web.json_response({"error": "Timeout waiting for offer"}, status=408)


async def handle_ice_candidate(request):
    """Handle ICE candidates."""
    data = await request.json()
    peer_id = data.get("peer_id")
    candidate = data.get("candidate")
    
    logger.info(f"Received ICE candidate from {peer_id}")
    
    if peer_id in peers:
        if "ice_candidates" not in peers[peer_id]:
            peers[peer_id]["ice_candidates"] = []
        peers[peer_id]["ice_candidates"].append(candidate)
    
    return web.json_response({"status": "ok"})


async def handle_status(request):
    """Return server status."""
    return web.json_response({
        "status": "running",
        "peers": list(peers.keys())
    })


def main():
    parser = argparse.ArgumentParser(description="WebRTC Signaling Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    args = parser.parse_args()
    
    app = web.Application()
    app.router.add_post("/offer", handle_offer)
    app.router.add_post("/answer", handle_answer)
    app.router.add_post("/ice", handle_ice_candidate)
    app.router.add_get("/status", handle_status)
    
    logger.info(f"Starting signaling server on {args.host}:{args.port}")
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
