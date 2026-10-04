# From Memory to Self-Improvement: My First Agent Learning Lab Prototype

If I correct an AI agent today, will it make the same mistake tomorrow?

I have prepared a small prototype to explore that question using Letta and the memory ideas introduced by MemGPT.

The project is called **Agent Learning Lab**. It asks whether an agent can convert feedback from an earlier task into a useful lesson for a new task, without retraining the underlying model.

MemGPT introduced an operating-system-inspired approach to managing information across memory tiers. Letta develops that foundation into persistent agents. My project adds a controlled experiment around experience, reflection, and evaluation.

The first version focuses on software incident diagnosis: asynchronous completion, duplicate effects from retries, and expired credentials.

The loop is straightforward:

1. Attempt a task.
2. Receive externally supplied feedback.
3. Propose a bounded lesson.
4. Validate it on a separate incident.
5. Apply promoted lessons to unseen variants.

I compare three configurations: fresh context, raw past incident history, and evaluated lessons. The underlying model stays the same.

A counterexample matters as much as a success. Learning to check completion signals should not make the agent reject a timeout adjustment when the deadline really is too short.

The repository includes a Python CLI, a live Letta adapter, versioned memory records in SQLite, tests, and an HTML audit report. There is also a credential-free scripted walkthrough for understanding the mechanics. Its behavior is hard-coded and is not evidence of AI improvement.

I have verified the local harness, but I have not yet run the authenticated Letta experiment or measured model improvement. This is a small diagnosis prototype, not yet an autonomous coding agent.

My next step is to expand the evaluation and test whether retained lessons help, hurt, or make no difference. I also want to explore autonomous memory management and background consolidation as separate experiments.

From my experience in distributed systems, useful knowledge needs context: what worked, why it worked, and when it should be reconsidered. I want to bring that discipline to agents that learn through experience.

If you are building agents with memory, how do you distinguish remembering an event from learning a reusable skill?

Repository: add the real GitHub URL after publishing.

References:
- https://arxiv.org/abs/2310.08560
- https://www.letta.com/blog/ai-agents-stack/

#MemGPT #Letta #AgentMemory #SelfImprovingAgents #SoftwareEngineering
