## Archive Note

- Reason retired: This V6 constitution was superseded by the GitHub canonical V10 package.
- Replaced by: `docs/v10/00_V10_MASTER_CONSTITUTION.md`
- Historical value: Yes. It captures early locked state and product assumptions before V10 normalization.

# STELLCODEX V6 — Core Technical Constitution (Binding)

STELLCODEX = CAD Upload + Viewer + Orchestrator + DFM Pipeline + Share Engine + Admin/Audit.

MoldCodes ayrı ürün değildir.
Manufacturing Decision Engine modülüdür.

ID CONTRACT:
- UI yalnızca file_id kullanır.
- revision_id ve storage_key public response'ta bulunmaz.

ORCHESTRATOR STATES:
S0 Uploaded
S1 Converted
S2 AssemblyReady
S3 Analyzing
S4 DFMReady
S5 AwaitingApproval
S6 Approved
S7 ShareReady

decision_json zorunlu alanlar:
- rule_version
- rule_explanations[]
- mode (brep|mesh_approx|visual_only)
- confidence
