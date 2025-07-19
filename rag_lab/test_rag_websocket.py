#!/usr/bin/env python3
"""
Test script for RAG WebSocket functionality
"""

import requests
import json
import asyncio
import websockets
from time import sleep

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat"

def test_rag_config():
    """Test RAG configuration endpoint"""
    print("=== Testing RAG Configuration ===")
    
    # Test GET config
    response = requests.get(f"{BASE_URL}/api/rag/config")
    print(f"GET /api/rag/config: {response.status_code}")
    print(f"Current config: {response.json()}")
    
    # Test SET config
    config_data = {
        "model": "gpt-4o-mini",
        "temperature": 0.1,
        "search_type": "similarity",
        "k": 5,
        "search_kwargs": {}
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/set", json=config_data)
    print(f"POST /api/rag/set: {response.status_code}")
    print(f"Set config response: {response.json()}")
    
    return response.status_code == 200

def test_document_sync():
    """Test document synchronization"""
    print("\n=== Testing Document Sync ===")
    
    # Check if documents exist
    response = requests.get(f"{BASE_URL}/api/documents/status")
    print(f"Document status: {response.json()}")
    
    # If no documents, try to sync
    if not response.json().get("db_exists", False):
        print("No documents found, attempting sync...")
        sync_response = requests.post(f"{BASE_URL}/api/documents/sync", json={
            "chunk_size": 500,
            "chunk_overlap": 100
        })
        print(f"Sync response: {sync_response.json()}")
        return sync_response.status_code == 200
    
    return True

async def test_websocket_rag():
    """Test WebSocket RAG functionality"""
    print("\n=== Testing WebSocket RAG ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("WebSocket connected successfully")
            
            # Test question
            test_question = "What is tax law?"
            message = {"message": test_question}
            
            print(f"Sending question: {test_question}")
            await websocket.send(json.dumps(message))
            
            # Receive streaming response
            response_chunks = []
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    data = json.loads(response)
                    
                    if data["type"] == "start":
                        print(f"Stream started: {data['message']}")
                    elif data["type"] == "chunk":
                        content = data["content"]
                        response_chunks.append(content)
                        print(content, end="", flush=True)
                    elif data["type"] == "done":
                        print("\nStream completed")
                        break
                    elif data["type"] == "error":
                        print(f"Error: {data['message']}")
                        return False
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    return False
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    return False
            
            full_response = "".join(response_chunks)
            print(f"\nFull response length: {len(full_response)} characters")
            return len(full_response) > 0
            
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== RAG WebSocket Test Suite ===\n")
    
    # Test REST API first
    config_success = test_rag_config()
    doc_success = test_document_sync()
    
    if config_success and doc_success:
        print("\nREST API tests passed, testing WebSocket...")
        
        # Test WebSocket
        ws_success = asyncio.run(test_websocket_rag())
        
        print(f"\n=== Test Results ===")
        print(f"RAG Config: {'✅ PASS' if config_success else '❌ FAIL'}")
        print(f"Document Sync: {'✅ PASS' if doc_success else '❌ FAIL'}")
        print(f"WebSocket RAG: {'✅ PASS' if ws_success else '❌ FAIL'}")
        
        if config_success and doc_success and ws_success:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed")
    else:
        print("\n❌ REST API tests failed, skipping WebSocket test")

if __name__ == "__main__":
    main()