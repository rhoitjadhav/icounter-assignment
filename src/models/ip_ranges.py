from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, \
    Index, func
from sqlalchemy.dialects.sqlite import insert
from common.helper import to_dict
from database import Base, SessionLocal


class IPRangesModel(Base):
    __tablename__ = 'ip_ranges'

    id = Column(Integer, primary_key=True)
    cidr = Column(String)
    provider = Column(String)
    source = Column(String)
    ip_version = Column(Integer)
    network_int = Column(Integer)
    broadcast_int = Column(Integer)
    region = Column(String)
    service = Column(String)
    fetched_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("cidr", "provider", name="uq_cidr_provider"),
        Index("idx_range", "network_int", "broadcast_int"),
    )

    def __repr__(self) -> str:
        return (
            f"<IPRange(id={self.id}, cidr={self.cidr!r}, "
            f"provider={self.provider!r}, region={self.region!r})>"
        )

    @classmethod
    def create(cls, **kwargs) -> dict:
        model_obj = cls(**kwargs)
        with SessionLocal() as session:
            session.add(model_obj)
            session.commit()
            session.refresh(model_obj)
            return to_dict(model_obj)

    @classmethod
    def find_by_ip(cls, ip_int: int) -> list[dict]:
        with SessionLocal() as session:
            rows = (
                session.query(cls)
                .filter(cls.network_int <= ip_int, cls.broadcast_int >= ip_int)
                .all()
            )
            return [to_dict(r) for r in rows]

    @classmethod
    def get_provider_counts(cls) -> list[dict]:
        with SessionLocal() as session:
            rows = (
                session.query(cls.provider, func.count().label("ranges"))
                .group_by(cls.provider)
                .all()
            )
            return [{"name": r.provider, "ranges": r.ranges} for r in rows]

    @classmethod
    def get_health_stats(cls) -> dict:
        with SessionLocal() as session:
            total = session.query(func.count(cls.id)).scalar()
            last_refreshed = session.query(func.max(cls.fetched_at)).scalar()
            providers = [
                r[0] for r in session.query(cls.provider).distinct().all()
            ]
            return {
                "status": "ok",
                "total_ranges": total,
                "last_refreshed": last_refreshed,
                "providers": providers,
            }

    @classmethod
    def upsert_many(cls, records: list[dict]) -> None:
        if not records:
            return
        with SessionLocal() as session:
            stmt = insert(cls).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["cidr", "provider"],
                set_={"fetched_at": stmt.excluded.fetched_at},
            )
            session.execute(stmt)
            session.commit()
