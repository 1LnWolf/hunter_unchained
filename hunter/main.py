#!/usr/bin/env python3
"""Hunter Unchained – Main entry point."""

import asyncio
import sys
import signal
from hunter.config_loader import load_config
from hunter.master_auth import authenticate
from hunter.agent_core import AgentCore
from hunter.ui import ConsoleUI
from hunter.permission_gate import MissionGate
from hunter.tool_orchestrator import ToolOrchestrator
from hunter.knowledge_base import KnowledgeBase
from hunter.memory import Memory
from hunter.learning_pipeline import LiveLearner
from hunter.models import create_model
from hunter.self_defense import SelfDefense
from hunter.topic_researcher import TopicResearcher
from hunter.fuzzing_engine import FuzzingEngine
from hunter.innovation_engine import InnovationEngine

async def shutdown(loop, sig_name):
    print(f"\n[!] Received {sig_name}, shutting down...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def main():
    config = load_config("hunter_unchained.yaml")

    if not authenticate(config):
        print("[X] Authentication failed. Exiting.")
        sys.exit(1)

    model = create_model(config)
    kb = KnowledgeBase(config)
    mem = Memory(config)
    gate = MissionGate(config)
    self_defense = SelfDefense(config)
    tools = ToolOrchestrator(config, gate, self_defense)
    researcher = TopicResearcher(config, kb)
    fuzzing = FuzzingEngine(config, gate) if config["fuzzing"]["enabled"] else None
    innovation = InnovationEngine(config, kb, model) if config["innovation"]["enabled"] else None
    learner = LiveLearner(config, kb)
    ui = ConsoleUI(config, gate, researcher, fuzzing, innovation, self_defense)

    if config["knowledge"]["live_feeds"]:
        asyncio.create_task(learner.start())

    agent = AgentCore(config, model, kb, mem, tools, gate, ui, researcher)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(loop, s.name)))

    try:
        await ui.run(agent)
    except Exception as e:
        print(f"[FATAL] {e}")
    finally:
        await mem.close()
        await kb.close()
        print("[*] Hunter out.")

if __name__ == "__main__":
    asyncio.run(main())