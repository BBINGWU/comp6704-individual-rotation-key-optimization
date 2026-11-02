# Report notes V2

This is a workload-aware optimization study and makes no claim of cryptographic novelty.

Under the fixed CKKS parameter set, every measured singleton rotation key has the same serialized size (5,507,945 bytes). Therefore the memory constraint in this experiment is equivalent to a cardinality/key-count constraint. The general formulation still allows heterogeneous key sizes.

Individual singleton-key serialization repeats some container metadata, so summed bytes are a consistent experimental proxy rather than the exact serialized size of one combined key map.

`DIRECT_ALL` is preserved in the old raw CSV for compatibility and is called `DIRECT_IN_POOL` in V2 report-facing outputs. `ALL_REQUIRED` directly provisions every workload target and is an unconstrained reference, not a candidate-pool budget point.

Composed measurements restart from the same original ciphertext for every timed repetition. `measured_model_latency_us` is the workload-weighted sum of complete-path median measurements; it is not full application end-to-end runtime. See `report_notes.md` for the complexity analysis, which remains unchanged.
