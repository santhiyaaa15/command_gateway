# app.py - FINAL SUBMISSION (EVERYTHING WORKS)
import re
import os
import json
import uuid
import datetime
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

DATABASE_URL = "sqlite:///gateway.db"
PORT = 5000

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(bind=engine))

class Role:
    ADMIN = "admin"
    MEMBER = "member"

class Action:
    AUTO_ACCEPT = "AUTO_ACCEPT"
    AUTO_REJECT = "AUTO_REJECT"

# MODELS
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    api_key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default=Role.MEMBER)
    credits = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    pattern = Column(String, nullable=False)
    action = Column(String, nullable=False)
    order = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))

class Command(Base):
    __tablename__ = "commands"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    command_text = Column(Text, nullable=False)
    status = Column(String, default="submitted")
    cost = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    command_id = Column(Integer, ForeignKey("commands.id"), nullable=True)
    action = Column(String)
    meta_data = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = Flask(__name__, static_folder="static")

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Invalid auth"}), 401
        api_key = auth.split(" ", 1)[1]

        db = SessionLocal()
        try:
            user = db.query(User).filter_by(api_key=api_key).first()
            if not user:
                return jsonify({"error": "Invalid API key"}), 401
            g.user = user
            return f(*args, **kwargs)
        finally:
            db.close()
    return decorated

def admin_only(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user.role != Role.ADMIN:
            return jsonify({"error": "Admin only"}), 403
        return f(*args, **kwargs)
    return decorated

def generate_key():
    return uuid.uuid4().hex

def match_first_rule(db, text):
    rules = db.query(Rule).order_by(Rule.order.asc(), Rule.id.asc()).all()
    for r in rules:
        try:
            if re.search(r.pattern, text):
                return r
        except:
            continue
    return None

def mock_execute(cmd):
    return {"stdout": f"[MOCK] {cmd}", "rc": 0}

# Seed Admin
def seed_admin():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            key = generate_key()
            admin = User(api_key=key, name="admin", role=Role.ADMIN, credits=999999)
            db.add(admin)
            db.commit()
            print("\n" + "="*80)
            print("ADMIN API KEY →", key)
            print("COPY THIS AND PASTE IN THE LOGIN BOX!")
            print("="*80 + "\n")
    finally:
        db.close()

seed_admin()

# ROUTES
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/whoami")
@require_api_key
def whoami():
    return jsonify({
        "name": g.user.name,
        "role": g.user.role,
        "credits": g.user.credits,
        "is_admin": g.user.role == Role.ADMIN
    })

@app.route("/commands", methods=["POST"])
@require_api_key
def submit_command():
    data = request.get_json() or {}
    cmd_text = data.get("command_text", "").strip()
    if not cmd_text:
        return jsonify({"error": "command_text required"}), 400

    db = SessionLocal()
    try:
        user = g.user
        is_admin = user.role == Role.ADMIN

        if is_admin:
            cmd = Command(user_id=user.id, command_text=cmd_text, status="executed", cost=0, executed_at=datetime.datetime.utcnow())
            db.add(cmd)
            db.flush()
            result = mock_execute(cmd_text)
            db.add(AuditLog(user_id=user.id, command_id=cmd.id, action="ADMIN_EXECUTED", meta_data=json.dumps({"result": result})))
            db.commit()
            return jsonify({"status": "executed", "result": result})

        if user.credits <= 0:
            return jsonify({"status": "rejected", "reason": "no credits"}), 403

        cmd = Command(user_id=user.id, command_text=cmd_text, status="submitted", cost=1)
        db.add(cmd)
        db.flush()

        rule = match_first_rule(db, cmd_text)

        if rule and rule.action == Action.AUTO_ACCEPT:
            user.credits -= 1
            result = mock_execute(cmd_text)
            cmd.status = "executed"
            cmd.executed_at = datetime.datetime.utcnow()
            db.add(AuditLog(user_id=user.id, command_id=cmd.id, action="AUTO_ACCEPTED", meta_data=json.dumps({"rule_id": rule.id, "result": result})))
            db.commit()
            return jsonify({"status": "executed", "result": result, "new_balance": user.credits})

        cmd.status = "rejected"
        reason = "blocked by rule" if rule else "no matching rule"
        action = "AUTO_REJECTED" if rule else "REJECTED_NO_RULE"
        db.add(AuditLog(user_id=user.id, command_id=cmd.id, action=action, meta_data=json.dumps({"reason": reason})))
        db.commit()
        return jsonify({"status": "rejected", "reason": reason})
    finally:
        db.close()

@app.route("/commands")
@require_api_key
def list_commands():
    db = SessionLocal()
    try:
        cmds = db.query(Command).filter_by(user_id=g.user.id).order_by(Command.created_at.desc()).limit(50).all()
        return jsonify([{
            "id": c.id,
            "text": c.command_text,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
            "executed_at": c.executed_at.isoformat() if c.executed_at else None
        } for c in cmds])
    finally:
        db.close()

@app.route("/admin/users", methods=["POST"])
@require_api_key
@admin_only
def create_user():
    data = request.get_json() or {}
    name = data.get("name", "user")
    role = data.get("role", Role.MEMBER)
    credits = data.get("credits", 100 if role == Role.MEMBER else 0)
    api_key = generate_key()
    db = SessionLocal()
    try:
        user = User(api_key=api_key, name=name, role=role, credits=credits)
        db.add(user)
        db.commit()
        return jsonify({"api_key": api_key})
    finally:
        db.close()

@app.route("/admin/users")
@require_api_key
@admin_only
def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return jsonify([{
            "id": u.id,
            "name": u.name,
            "role": u.role,
            "credits": u.credits,
            "api_key": u.api_key  # THIS WAS MISSING!
        } for u in users])
    finally:
        db.close()

@app.route("/admin/users/<int:user_id>", methods=["DELETE"])
@require_api_key
@admin_only
def delete_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.role == Role.ADMIN:
            return jsonify({"error": "Cannot delete admin"}), 403
        
        db.delete(user)
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()

@app.route("/admin/rules", methods=["POST"])
@require_api_key
@admin_only
def create_rule():
    data = request.get_json() or {}
    pattern = data.get("pattern")
    action = data.get("action")
    if not pattern or action not in [Action.AUTO_ACCEPT, Action.AUTO_REJECT]:
        return jsonify({"error": "Invalid data"}), 400
    try:
        re.compile(pattern)
    except:
        return jsonify({"error": "Invalid regex"}), 400
    
    db = SessionLocal()
    try:
        rule = Rule(name=data.get("name", ""), pattern=pattern, action=action, order=0, created_by=g.user.id)
        db.add(rule)
        db.commit()
        return jsonify({"rule_id": rule.id})
    finally:
        db.close()

@app.route("/rules")
@require_api_key
def list_rules():
    db = SessionLocal()
    try:
        rules = db.query(Rule).order_by(Rule.order.asc()).all()
        return jsonify([{"id": r.id, "name": r.name or "Unnamed", "pattern": r.pattern, "action": r.action} for r in rules])
    finally:
        db.close()

@app.route("/admin/audit")
@require_api_key
@admin_only
def audit_logs():
    db = SessionLocal()
    try:
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
        return jsonify([{
            "action": l.action,
            "meta": json.loads(l.meta_data) if l.meta_data else {},
            "time": l.created_at.isoformat(),
            "user_id": l.user_id
        } for l in logs])
    finally:
        db.close()

@app.teardown_appcontext
def shutdown_session(exception=None):
    SessionLocal.remove()

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=PORT, debug=False)