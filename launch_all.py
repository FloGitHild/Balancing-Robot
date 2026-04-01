#!/usr/bin/env python3
"""
Robot Agent Launcher
Starts all three programs - outputs to console
"""

import subprocess
import time
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def print_banner():
    print("=" * 60)
    print("🤖 ROBOT AGENT LAUNCHER")
    print("=" * 60)
    print()

def main():
    print_banner()
    
    processes = []
    
    # 1. Start ESP32P4 Simulator
    print("🚀 Starting ESP32P4 Simulator...")
    proc = subprocess.Popen(
        ["python3", "ESP32P4 Simulator.py"],
        cwd=os.path.join(PROJECT_ROOT, "ESP32P4")
    )
    processes.append(("ESP32P4", proc))
    time.sleep(3)
    
    # 2. Start Vision
    print("🚀 Starting Vision...")
    proc = subprocess.Popen(
        ["python3", "vision_for_agent.py"],
        cwd=os.path.join(PROJECT_ROOT, "Agent")
    )
    processes.append(("Vision", proc))
    time.sleep(2)
    
    # 3. Start Agent (runs in foreground so you can interact)
    print("🚀 Starting Agent (main program)...")
    proc = subprocess.Popen(
        ["python3", "agent.py"],
        cwd=os.path.join(PROJECT_ROOT, "Agent")
    )
    processes.append(("Agent", proc))
    
    print()
    print("=" * 60)
    print("✅ All programs started!")
    print("=" * 60)
    print("\nPrograms running:")
    for name, p in processes:
        print(f"  - {name} (PID: {p.pid})")
    print("\n⚠️ Note: Agent is now in foreground.")
    print("   ESP32P4 and Vision are running in background.")
    print()
    
    # Wait for agent (foreground)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all programs...")
        for name, p in processes:
            p.terminate()
            p.wait()
        print("✅ All stopped")

if __name__ == "__main__":
    main()