# STELL Training Pipeline

1. Listener captures incoming event
2. Planner derives executable task graph
3. Executor performs tool calls
4. Reporter stores evidence references
5. Memory writer persists structured records
6. Retrieval evaluator scores hit quality
7. Solved-case writer stores reusable resolution

Pipeline invariant:
raw input -> structured memory -> retrieval index -> validated solved case
