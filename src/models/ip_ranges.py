from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, \
    Index
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
