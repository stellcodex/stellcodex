# decision_json Schema (V7)

Required shape:

{
  "rule_version": "vX.Y",
  "mode": "brep|mesh_approx|visual_only",
  "confidence": 0.0,
  "manufacturing_method": "injection_molding|3d_printing|cnc|unknown",
  "rule_explanations": [
    {
      "rule_id": "R01_SOMETHING",
      "triggered": true,
      "severity": "INFO|LOW|MEDIUM|HIGH",
      "reference": "rule_configs:R01",
      "reasoning": "deterministic explanation"
    }
  ],
  "conflict_flags": []
}

Notes:
- rule_explanations must be non-empty.
- confidence is required even for visual_only.
