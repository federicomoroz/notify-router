from sqlalchemy.orm import Session

from app.models.orm import Rule


def _matches(rule: Rule, source: str, event_type: str, payload: dict) -> bool:
    if rule.source_filter != "*" and rule.source_filter != source:
        return False
    if rule.event_type_filter != "*" and rule.event_type_filter != event_type:
        return False
    if rule.condition_key:
        return str(payload.get(rule.condition_key, "")) == rule.condition_value
    return True


class RuleRepository:
    @staticmethod
    def match_all(db: Session, source: str, event_type: str, payload: dict) -> list[Rule]:
        rules = (
            db.query(Rule)
            .filter(Rule.enabled == True)
            .order_by(Rule.priority.desc())
            .all()
        )
        return [r for r in rules if _matches(r, source, event_type, payload)]

    @staticmethod
    def list_all(db: Session) -> list[Rule]:
        return db.query(Rule).order_by(Rule.priority.desc()).all()

    @staticmethod
    def get(db: Session, rule_id: int) -> Rule | None:
        return db.query(Rule).filter(Rule.id == rule_id).first()

    @staticmethod
    def create(db: Session, rule: Rule) -> Rule:
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def update(db: Session, rule: Rule, data: dict) -> Rule:
        for key, value in data.items():
            setattr(rule, key, value)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def delete(db: Session, rule: Rule) -> None:
        db.delete(rule)
        db.commit()
