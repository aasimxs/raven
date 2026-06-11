from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
import json
import asyncio
import logging

# Suppress noisy asyncio exceptions for DNS lookup failures on dead domains
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

import models
from database import engine, SessionLocal
from collectors.username_collector import run_username_collection
from collectors.email_collector import run_email_collection
from collectors.phone_collector import run_phone_collection
from correlator import run_correlation
from dossier_generator import generate_dossier

models.Base.metadata.create_all(bind=engine)

app = Flask(__name__)
CORS(app)

@app.route("/api/status", methods=["GET"])
def read_root():
    return jsonify({"status": "ok", "message": "Raven OSINT API is running"})

@app.route("/cases/", methods=["POST"])
def create_case():
    name = request.args.get("name")
    description = request.args.get("description", "")
    
    db = SessionLocal()
    case = models.Case(name=name, description=description)
    db.add(case)
    db.commit()
    db.refresh(case)
    case_dict = {"id": case.id, "name": case.name, "description": case.description}
    db.close()
    return jsonify(case_dict)

@app.route("/cases/", methods=["GET"])
def list_cases():
    db = SessionLocal()
    cases = db.query(models.Case).order_by(models.Case.id.desc()).all()
    result = []
    for c in cases:
        targets = [{"type": t.seed_type, "value": t.seed_value} for t in c.targets]
        result.append({
            "id": c.id, 
            "name": c.name, 
            "description": c.description,
            "targets": targets
        })
    db.close()
    return jsonify(result)

@app.route("/cases/<int:case_id>", methods=["GET"])
def get_case(case_id):
    db = SessionLocal()
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        db.close()
        return jsonify({"detail": "Case not found."}), 404
        
    targets = [{"type": t.seed_type, "value": t.seed_value} for t in case.targets]
    result = {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "targets": targets
    }
    db.close()
    return jsonify(result)

@app.route("/cases/<int:case_id>", methods=["DELETE"])
def delete_case(case_id):
    db = SessionLocal()
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        db.close()
        return jsonify({"detail": "Case not found."}), 404
        
    # Delete associated records manually since cascade wasn't set on models
    db.query(models.Target).filter(models.Target.case_id == case_id).delete()
    db.query(models.Evidence).filter(models.Evidence.case_id == case_id).delete()
    db.query(models.Relationship).filter(models.Relationship.case_id == case_id).delete()
    
    # Delete the case
    db.delete(case)
    db.commit()
    db.close()
    
    return jsonify({"status": "deleted"})

@app.route("/cases/<int:case_id>/evidence", methods=["GET"])
def get_evidence(case_id):
    db = SessionLocal()
    evidence = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()
    result = [{
        "id": e.id, "case_id": e.case_id, "source": e.source, 
        "retrieval_method": e.retrieval_method, "data_hash": e.data_hash, 
        "confidence": e.confidence, "raw_payload": e.raw_payload
    } for e in evidence]
    db.close()
    return jsonify(result)

@app.route("/search/", methods=["POST"])
def run_search():
    req = request.json
    target_type = req.get("target_type")
    target_value = req.get("target_value")
    case_id = req.get("case_id")
    
    if target_type not in ["username", "email", "phone"]:
        return jsonify({"detail": "Invalid target_type. Use 'username', 'email', or 'phone'."}), 400
        
    db = SessionLocal()
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        db.close()
        return jsonify({"detail": "Case not found."}), 404
        
    target = models.Target(case_id=case_id, seed_type=target_type, seed_value=target_value)
    db.add(target)
    db.commit()
    
    results = []
    if target_type == "username":
        results = asyncio.run(run_username_collection(target_value))
    elif target_type == "email":
        results = asyncio.run(run_email_collection(target_value))
    elif target_type == "phone":
        results = asyncio.run(run_phone_collection(target_value))
        
    for res in results:
        res["target"] = target_value
        evidence = models.Evidence(
            case_id=case_id,
            source=res.get("source"),
            retrieval_method="api",
            data_hash=str(hash(json.dumps(res))),
            confidence=res.get("confidence", 0.0),
            raw_payload=json.dumps(res)
        )
        db.add(evidence)
        db.commit() # Commit to get evidence.id
        db.refresh(evidence)
        
        if res.get("exists"):
            rel = models.Relationship(
                case_id=case_id,
                source_type="target",
                source_value=target_value,
                target_type="evidence",
                target_value=str(evidence.id),
                relationship_type="FOUND_IN",
                confidence=res.get("confidence", 0.0)
            )
            db.add(rel)
        
    db.commit()
    run_correlation(case_id)
    db.close()
    
    return jsonify({"status": "completed", "results": len(results)})

FRONTEND_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "out"))

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if not os.path.exists(FRONTEND_OUT):
        return "Frontend build not found. Run 'npm run build' in frontend.", 404
        
    if path != "" and os.path.exists(os.path.join(FRONTEND_OUT, path)):
        return send_from_directory(FRONTEND_OUT, path)
    elif path != "" and os.path.exists(os.path.join(FRONTEND_OUT, path + ".html")):
        return send_from_directory(FRONTEND_OUT, path + ".html")
    else:
        return send_from_directory(FRONTEND_OUT, "index.html")

@app.route('/cases/<int:case_id>/graph', methods=['GET'])
def get_case_graph(case_id):
    db = SessionLocal()
    targets = db.query(models.Target).filter(models.Target.case_id == case_id).all()
    evidence_list = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()
    relationships = db.query(models.Relationship).filter(models.Relationship.case_id == case_id).all()

    nodes = []
    links = []

    for t in targets:
        nodes.append({"id": f"target_{t.seed_value}", "name": t.seed_value, "group": "Target", "type": t.seed_type})

    for e in evidence_list:
        try:
            payload = json.loads(e.raw_payload)
            name = payload.get("url") or payload.get("note") or e.source
            # Only add to graph if it actually exists/was found
            if payload.get("exists"):
                nodes.append({"id": f"evidence_{e.id}", "name": name, "group": "Evidence", "source": e.source})
        except:
            nodes.append({"id": f"evidence_{e.id}", "name": e.source, "group": "Evidence"})

    for r in relationships:
        source_id = f"{r.source_type}_{r.source_value}"
        target_id = f"{r.target_type}_{r.target_value}"
        links.append({"source": source_id, "target": target_id, "label": r.relationship_type})

    # Filter out links pointing to missing nodes to prevent frontend crash
    valid_node_ids = {n["id"] for n in nodes}
    valid_links = [l for l in links if l["source"] in valid_node_ids and l["target"] in valid_node_ids]

    db.close()
    return jsonify({"nodes": nodes, "links": valid_links})

@app.route('/cases/<int:case_id>/dossier', methods=['GET'])
def get_case_dossier(case_id):
    pdf_bytes = generate_dossier(case_id)
    if not pdf_bytes:
        return jsonify({"detail": "Case not found"}), 404
        
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=raven_osint_case_{case_id}.pdf'
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
