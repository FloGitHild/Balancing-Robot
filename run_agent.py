#!/usr/bin/env python3
"""
Robot Agent - Main Entry Point
Task-based autonomous system for the balancing robot.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from robot_agent.core.agent import Agent
import robot_agent.config as config


def main():
    parser = argparse.ArgumentParser(description="Balancing Robot Agent")
    parser.add_argument("--model", default=config.LLM_MODEL, help="Ollama model name")
    parser.add_argument("--mode", default=config.DEFAULT_MODE, help="Initial mode (Idle, Play, Assist, Explore, Auto)")
    parser.add_argument("--robot-url", default=config.ROBOT_URL, help="Robot WebSocket URL")
    args = parser.parse_args()

    agent = Agent(mode=args.mode, robot_url=args.robot_url)
    agent.run_interactive()


if __name__ == "__main__":
    main()
