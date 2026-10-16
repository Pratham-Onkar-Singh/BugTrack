from fastapi import Depends, FastAPI, HTTPException, Response
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from . import models, schemas
from .db import get_db

app = FastAPI(title="BugTrack API")
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "database unavailable"}
    return {"status": "ready"}


@app.get("/api/bugs", response_model=list[schemas.BugOut])
def list_bugs(status: schemas.Status | None = None, db: Session = Depends(get_db)):
    query = select(models.Bug).order_by(models.Bug.id.desc())
    if status:
        query = query.where(models.Bug.status == status)
    return db.scalars(query).all()


@app.get("/api/bugs/stats", response_model=schemas.Stats)
def stats(db: Session = Depends(get_db)):
    rows = dict(db.execute(select(models.Bug.status, func.count()).group_by(models.Bug.status)).all())
    counts = {s: rows.get(s, 0) for s in schemas.STATUSES}
    return {"total": sum(counts.values()), **counts}


def get_or_404(db: Session, bug_id: int) -> models.Bug:
    bug = db.get(models.Bug, bug_id)
    if bug is None:
        raise HTTPException(status_code=404, detail="Bug not found")
    return bug


@app.get("/api/bugs/{bug_id}", response_model=schemas.BugOut)
def get_bug(bug_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, bug_id)


@app.post("/api/bugs", response_model=schemas.BugOut, status_code=201)
def create_bug(payload: schemas.BugIn, db: Session = Depends(get_db)):
    bug = models.Bug(**payload.model_dump())
    db.add(bug)
    db.commit()
    db.refresh(bug)
    return bug


@app.put("/api/bugs/{bug_id}", response_model=schemas.BugOut)
def update_bug(bug_id: int, payload: schemas.BugIn, db: Session = Depends(get_db)):
    bug = get_or_404(db, bug_id)
    for field, value in payload.model_dump().items():
        setattr(bug, field, value)
    db.commit()
    db.refresh(bug)
    return bug


@app.delete("/api/bugs/{bug_id}", status_code=204)
def delete_bug(bug_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, bug_id))
    db.commit()
