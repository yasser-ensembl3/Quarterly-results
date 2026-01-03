from __future__ import annotations
"""Modèles SQLAlchemy pour la base de données."""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles."""
    pass


class CompanyType(PyEnum):
    """Type de société."""
    CRYPTO = "crypto"
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"


class ProcessingStatus(PyEnum):
    """Statut du traitement des données."""
    PENDING = "pending"
    SYNCED = "synced"
    EXTRACTED = "extracted"
    NORMALIZED = "normalized"
    REVIEWED = "reviewed"
    ERROR = "error"


class FileType(PyEnum):
    """Type de fichier source."""
    MARKDOWN = "markdown"
    PDF = "pdf"
    IMAGE = "image"
    OTHER = "other"


class Company(Base):
    """Modèle pour les sociétés."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    ticker = Column(String(20), nullable=True)
    company_type = Column(Enum(CompanyType), nullable=False)
    sector = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    company_quarters = relationship("CompanyQuarter", back_populates="company")

    def __repr__(self) -> str:
        return f"<Company(name='{self.name}', ticker='{self.ticker}')>"


class Quarter(Base):
    """Modèle pour les trimestres."""
    __tablename__ = "quarters"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)  # 1, 2, 3, 4
    label = Column(String(20), nullable=False)  # Ex: "Q3 2024"
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("year", "quarter", name="uq_year_quarter"),
    )

    # Relations
    company_quarters = relationship("CompanyQuarter", back_populates="quarter")

    def __repr__(self) -> str:
        return f"<Quarter(label='{self.label}')>"


class CompanyQuarter(Base):
    """Association société-trimestre avec statut de traitement."""
    __tablename__ = "company_quarters"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    quarter_id = Column(Integer, ForeignKey("quarters.id"), nullable=False)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    needs_review = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("company_id", "quarter_id", name="uq_company_quarter"),
    )

    # Relations
    company = relationship("Company", back_populates="company_quarters")
    quarter = relationship("Quarter", back_populates="company_quarters")
    source_files = relationship("SourceFile", back_populates="company_quarter")
    core_financials = relationship("CoreFinancials", back_populates="company_quarter", uselist=False)
    crypto_metrics = relationship("CryptoMetrics", back_populates="company_quarter", uselist=False)
    ecommerce_metrics = relationship("EcommerceMetrics", back_populates="company_quarter", uselist=False)

    def __repr__(self) -> str:
        return f"<CompanyQuarter(company_id={self.company_id}, quarter_id={self.quarter_id})>"


class SourceFile(Base):
    """Fichiers sources téléchargés depuis Google Drive."""
    __tablename__ = "source_files"

    id = Column(Integer, primary_key=True)
    company_quarter_id = Column(Integer, ForeignKey("company_quarters.id"), nullable=False)
    gdrive_file_id = Column(String(255), nullable=False, unique=True)
    filename = Column(String(500), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    mime_type = Column(String(100), nullable=True)
    gdrive_modified = Column(DateTime, nullable=True)
    local_path = Column(String(1000), nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA256
    extraction_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    raw_extracted_text = Column(Text, nullable=True)
    extraction_confidence = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    company_quarter = relationship("CompanyQuarter", back_populates="source_files")

    def __repr__(self) -> str:
        return f"<SourceFile(filename='{self.filename}')>"


class CoreFinancials(Base):
    """Métriques financières universelles (toutes sociétés)."""
    __tablename__ = "core_financials"

    id = Column(Integer, primary_key=True)
    company_quarter_id = Column(Integer, ForeignKey("company_quarters.id"), nullable=False, unique=True)

    # Revenue & Profit (en millions USD)
    revenue = Column(Numeric(15, 2), nullable=True)
    gross_profit = Column(Numeric(15, 2), nullable=True)
    operating_income = Column(Numeric(15, 2), nullable=True)
    net_income = Column(Numeric(15, 2), nullable=True)

    # Marges (en pourcentage)
    gross_margin_pct = Column(Numeric(6, 2), nullable=True)
    operating_margin_pct = Column(Numeric(6, 2), nullable=True)
    net_margin_pct = Column(Numeric(6, 2), nullable=True)

    # Par action
    eps = Column(Numeric(10, 4), nullable=True)
    eps_diluted = Column(Numeric(10, 4), nullable=True)

    # Croissance (en pourcentage)
    revenue_yoy_pct = Column(Numeric(8, 2), nullable=True)
    revenue_qoq_pct = Column(Numeric(8, 2), nullable=True)

    # Guidance
    guidance_revenue_low = Column(Numeric(15, 2), nullable=True)
    guidance_revenue_high = Column(Numeric(15, 2), nullable=True)
    guidance_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    company_quarter = relationship("CompanyQuarter", back_populates="core_financials")

    def __repr__(self) -> str:
        return f"<CoreFinancials(revenue={self.revenue})>"


class CryptoMetrics(Base):
    """Métriques spécifiques aux sociétés crypto (Coinbase, Circle, etc.)."""
    __tablename__ = "crypto_metrics"

    id = Column(Integer, primary_key=True)
    company_quarter_id = Column(Integer, ForeignKey("company_quarters.id"), nullable=False, unique=True)

    # Volume & Revenue
    trading_volume = Column(Numeric(18, 2), nullable=True)  # En USD
    transaction_revenue = Column(Numeric(15, 2), nullable=True)
    subscription_revenue = Column(Numeric(15, 2), nullable=True)
    blockchain_rewards_revenue = Column(Numeric(15, 2), nullable=True)

    # Assets
    assets_on_platform = Column(Numeric(18, 2), nullable=True)  # AUC/AUM
    custody_assets = Column(Numeric(18, 2), nullable=True)
    stablecoin_market_cap = Column(Numeric(18, 2), nullable=True)  # Pour Circle: USDC

    # Users
    monthly_transacting_users = Column(Integer, nullable=True)
    verified_users = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    company_quarter = relationship("CompanyQuarter", back_populates="crypto_metrics")

    def __repr__(self) -> str:
        return f"<CryptoMetrics(trading_volume={self.trading_volume})>"


class EcommerceMetrics(Base):
    """Métriques spécifiques aux sociétés e-commerce (Amazon, etc.)."""
    __tablename__ = "ecommerce_metrics"

    id = Column(Integer, primary_key=True)
    company_quarter_id = Column(Integer, ForeignKey("company_quarters.id"), nullable=False, unique=True)

    # Volume & Orders
    gmv = Column(Numeric(18, 2), nullable=True)  # Gross Merchandise Volume
    orders = Column(Integer, nullable=True)
    average_order_value = Column(Numeric(10, 2), nullable=True)

    # Customers
    active_customers = Column(Integer, nullable=True)
    prime_members = Column(Integer, nullable=True)

    # Segments spécifiques (ex: Amazon)
    aws_revenue = Column(Numeric(15, 2), nullable=True)
    advertising_revenue = Column(Numeric(15, 2), nullable=True)
    third_party_seller_pct = Column(Numeric(6, 2), nullable=True)

    # Costs
    fulfillment_cost = Column(Numeric(15, 2), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    company_quarter = relationship("CompanyQuarter", back_populates="ecommerce_metrics")

    def __repr__(self) -> str:
        return f"<EcommerceMetrics(gmv={self.gmv})>"


def init_db(database_url: str) -> sessionmaker:
    """Initialise la base de données et retourne un sessionmaker."""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
