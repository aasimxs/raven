import json
import asyncio
from database import SessionLocal
import models
from collectors.username_collector import run_username_collection

def run_correlation(case_id: int):
    """
    Analyzes evidence in a case and extracts new indicators to pivot on.
    For example, if an email scan finds a GitHub username, it will automatically
    queue a username scan for that target.
    """
    db = SessionLocal()
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        db.close()
        return
        
    evidence_items = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()
    existing_targets = [t.seed_value for t in db.query(models.Target).filter(models.Target.case_id == case_id).all()]
    
    new_targets_to_run = []
    
    for ev in evidence_items:
        try:
            payload = json.loads(ev.raw_payload)
            # If we found a GitHub username from an email scan
            if ev.source == "GitHub (Commits)" and payload.get("exists") and payload.get("url"):
                # Extract username from URL (https://github.com/username)
                username = payload["url"].split("/")[-1]
                if username and username not in existing_targets:
                    new_targets_to_run.append(("username", username, "Extracted from GitHub Commit Email", ev.id))
                    existing_targets.append(username)
        except Exception as e:
            continue
            
    for t_type, t_val, reason, ev_id in new_targets_to_run:
        # Save the new derived target
        target = models.Target(case_id=case_id, seed_type=t_type, seed_value=t_val)
        db.add(target)
        db.commit()
        
        # Save the relationship to explain HOW we found this new target
        rel = models.Relationship(
            case_id=case_id,
            source_type="evidence",
            source_value=str(ev_id),
            target_type="target",
            target_value=t_val,
            relationship_type="PIVOT",
            confidence=0.9
        )
        db.add(rel)
        db.commit()
        
        if t_type == "username":
            print(f"[*] AUTO-PIVOT: Running username scan on {t_val} (Reason: {reason})")
            results = asyncio.run(run_username_collection(t_val))
            for res in results:
                new_ev = models.Evidence(
                    case_id=case_id,
                    source=f"[Auto-Pivot] {res.get('source')}",
                    retrieval_method="api",
                    data_hash=str(hash(json.dumps(res))),
                    confidence=res.get("confidence", 0.0),
                    raw_payload=json.dumps(res)
                )
                db.add(new_ev)
                db.commit()
                db.refresh(new_ev)
                
                if res.get("exists"):
                    new_rel = models.Relationship(
                        case_id=case_id,
                        source_type="target",
                        source_value=t_val,
                        target_type="evidence",
                        target_value=str(new_ev.id),
                        relationship_type="FOUND_IN",
                        confidence=res.get("confidence", 0.0)
                    )
                    db.add(new_rel)
                    db.commit()

    db.close()
