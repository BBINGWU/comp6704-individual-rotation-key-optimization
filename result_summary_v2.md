# Result summary V2

## Status

All 731 unique paths were measured end-to-end from the same original ciphertext per repetition; all passed the `1e-6` correctness tolerance. These measurements form a workload-weighted **measured path model**, not a full application runtime.

- Median measured/predicted path ratio: **0.9985**
- Mean measured/predicted path ratio: **1.0090**
- 95th percentile absolute relative error: **12.60%**
- Original GREEDY exact-feasible failures: **16**
- COVERAGE_GREEDY exact-feasible failures: **1**
- COVERAGE_GREEDY_SWAP exact-feasible failures: **0**
- Maximum composed-path error: **9.459e-12**

The correct audit interpretation is: among the 13 old cases where both the heuristic and exact search returned finite solutions, the observed gap was 0%; however, the original heuristic failed to find a feasible solution in many tight-budget cases where exact search was feasible.

## Correctness by hop count

|Hops|Paths|Maximum error|Median error|
|---:|---:|---:|---:|
|1|24|9.459e-12|7.284e-12|
|2|191|9.450e-12|7.142e-12|
|3|243|9.320e-12|7.126e-12|
|4|134|8.759e-12|7.007e-12|
|5|87|9.033e-12|7.287e-12|
|6|33|9.269e-12|7.107e-12|
|7|14|7.598e-12|7.049e-12|
|8|5|7.774e-12|6.814e-12|

## ALL_REQUIRED reference

|Workload|Keys|Serialized-byte proxy|Measured weighted direct latency (us)|
|---|---:|---:|---:|
|UNIFORM|64|352,508,480|8410.71|
|ZIPF|64|352,508,480|8361.64|
|CONV3|8|44,063,560|8358.07|
|CONV7|48|264,381,360|8286.40|
|BSGS64|14|77,111,230|8376.00|
