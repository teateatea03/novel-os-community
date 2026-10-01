# Research sources and limits

## Purpose
This skill converts research findings into engineering constraints for realistic long-form and interactive fiction. Sources are methodological references, not clinical or behavioural truth tables.

## Sources

1. **Park et al., Generative Agents: Interactive Simulacra of Human Behavior**
   - URL: https://arxiv.org/abs/2304.03442
   - Extracted lesson: persistent memories, retrieval, reflection and planning improve long-horizon behaviour.
   - Limit: memory retrieval alone does not calculate physiological load or reduce cognitive capacity.

2. **Simulating Human Behavior with the Psychological-mechanism Agent: Integrating Feeling, Thought, and Action**
   - URL: https://arxiv.org/abs/2507.19495
   - Extracted lesson: behaviour should pass through feeling, thought and action rather than event-to-text shortcutting.
   - Limit: a computational mechanism is not a clinical model; use conditional hypotheses and observable predictions.

3. **IVIE: A Neuro-symbolic Approach to Incremental and Validated Generation of Interactive Fiction Worlds**
   - URL: https://arxiv.org/abs/2606.13348
   - Extracted lesson: combine neural generation with symbolic world state, incremental updates and validation gates.
   - Limit: world-state validation does not by itself make a character psychologically realistic.

4. **Role-Playing Agents Driven by Large Language Models: Current Status, Challenges, and Future Trends**
   - URL: https://arxiv.org/abs/2601.10122
   - Extracted lesson: persona fidelity, memory, emotional consistency, goals, agency and controllability are separate evaluation axes.
   - Limit: a role-playing benchmark is not evidence about a particular person's private psychology.

5. **DynamicMem: A Long-Horizon Memory Benchmark in Real-World Settings**
   - URL: https://arxiv.org/abs/2606.22877
   - Extracted lesson: long-term memory requires updates, temporal validity and conflict handling, not only retrieval.
   - Limit: benchmark memory tasks do not replace domain-specific state reducers.

6. **ChronoMem: Version Control and Semantic Rollback for Large Language Model Agent Memory**
   - URL: https://arxiv.org/abs/2607.27773
   - Extracted lesson: memory must be versioned, branch-aware and rollbackable when later events supersede earlier state.
   - Limit: version control preserves provenance; it does not decide which human reaction is ethically or psychologically correct.

## Cross-source synthesis

- Store immutable events and derive current state; do not let prose be the only state store.
- Separate stable persona from transient capacity.
- Use a symbolic validator around neural generation.
- Keep event time, knowledge time, and validity time separate where needed.
- Evaluate local prose coherence and global state consistency separately.
- Treat physiological and psychological variables as writing constraints, not diagnoses.
