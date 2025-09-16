from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

ENGINE_URL = "sqlite:///netscan.db"
engine = create_engine(ENGINE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Scan(Base):
    __tablename__ = "scans"
    id = Column(String, primary_key=True)
    started = Column(DateTime, default=datetime.utcnow)
    finished = Column(DateTime, nullable=True)
    target = Column(String)
    safe_mode = Column(Boolean, default=True)
    summary_high = Column(Integer, default=0)
    summary_medium = Column(Integer, default=0)
    summary_low = Column(Integer, default=0)
    summary_info = Column(Integer, default=0)
    hosts = relationship("Host", back_populates="scan", cascade="all, delete-orphan")

class Host(Base):
    __tablename__ = "hosts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey("scans.id"))
    ip = Column(String, index=True)
    rdns = Column(String, nullable=True)
    whois_json = Column(Text, nullable=True)
    tls_json = Column(Text, nullable=True)
    scan = relationship("Scan", back_populates="hosts")
    ports = relationship("Port", back_populates="host", cascade="all, delete-orphan")
    webs = relationship("WebTarget", back_populates="host", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="host", cascade="all, delete-orphan")

class Port(Base):
    __tablename__ = "ports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    port = Column(Integer)
    proto = Column(String)
    state = Column(String, nullable=True)
    service = Column(String, nullable=True)
    product = Column(String, nullable=True)
    version = Column(String, nullable=True)
    host = relationship("Host", back_populates="ports")

class WebTarget(Base):
    __tablename__ = "webtargets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    url = Column(String)
    fp_json = Column(Text, nullable=True)  # whatweb fingerprint
    zap_json = Column(Text, nullable=True) # optional imported
    host = relationship("Host", back_populates="webs")

class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    source = Column(String)        # nuclei, nessus, zap
    name = Column(String)
    severity = Column(String)      # critical/high/medium/low/info
    cvss = Column(Float, nullable=True)
    evidence = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    host = relationship("Host", back_populates="findings")

def init_db():
    Base.metadata.create_all(bind=engine)
