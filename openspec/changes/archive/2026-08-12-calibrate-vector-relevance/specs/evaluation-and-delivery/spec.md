## ADDED Requirements

### Requirement: Refusal calibration reporting
The retrieval evaluation SHALL record the effective vector score threshold for vector-capable profiles and SHALL report refusal calibration metrics for questions marked as requiring refusal, including refusal count, false-positive answer count, and false-positive rate. Metrics MUST be computed from the current run rather than hard-coded.

#### Scenario: Report calibrated refusal outcomes
- **WHEN** an evaluation run contains refusal questions
- **THEN** its output includes the configured vector threshold, refusal count, false-positive answer count, and calculated false-positive rate

#### Scenario: Evaluate a threshold without vector retrieval
- **WHEN** the default BM25 evaluation profile is run
- **THEN** the output preserves BM25 metrics and records that no vector threshold is active

#### Scenario: Sweep thresholds for local calibration
- **WHEN** a user reruns a vector or hybrid evaluation with different vector threshold values
- **THEN** each output records its own threshold and measured refusal calibration metrics so the runs can be compared

#### Scenario: Handle an evaluation set without refusal questions
- **WHEN** an evaluation run contains no refusal questions
- **THEN** the refusal calibration count is zero and the false-positive rate is reported as unavailable rather than fabricated
