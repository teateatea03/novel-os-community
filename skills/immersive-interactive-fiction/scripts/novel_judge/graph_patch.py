from __future__ import annotations

from typing import Any

from .canonical import deep_copy, now_iso, sha256_json


def _diff(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if type(before) is not type(after): return [{"path": path or "/", "before": before, "after": after}]
    if isinstance(before, dict):
        out=[]
        for k in sorted(set(before)|set(after)):
            p=(path+"/"+str(k)).replace("//","/")
            if k not in before: out.append({"path":p,"before":None,"after":after[k]})
            elif k not in after: out.append({"path":p,"before":before[k],"after":None})
            else: out.extend(_diff(before[k],after[k],p))
        return out
    if isinstance(before,list):
        out=[]
        for i in range(max(len(before),len(after))):
            p=f"{path}/{i}"
            if i>=len(before): out.append({"path":p,"before":None,"after":after[i]})
            elif i>=len(after): out.append({"path":p,"before":before[i],"after":None})
            else: out.extend(_diff(before[i],after[i],p))
        return out
    return [] if before==after else [{"path":path or "/","before":before,"after":after}]


def build_graph_patch(before: dict[str, Any], after: dict[str, Any], *, turn_id: str, event_id: str, branch_id: str) -> dict[str, Any]:
    changes = [x for x in _diff(before, after) if x["path"].startswith(("/world_truth/", "/actors/", "/relations/", "/knowledge/"))]
    return {"schema":"minis.graph-patch.v1","patch_id":sha256_json([branch_id,turn_id,event_id,changes]),"turn_id":turn_id,"event_id":event_id,"branch_id":branch_id,"before_state_hash":before.get("state_hash"),"after_state_hash":after.get("state_hash"),"status":"pending","created_at":now_iso(),"changes":changes,"requires_promotion":True}
