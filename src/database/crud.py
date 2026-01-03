from __future__ import annotations
"""Opérations CRUD pour la base de données."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from .models import (
    Company,
    CompanyType,
    Quarter,
    CompanyQuarter,
    SourceFile,
    CoreFinancials,
    CryptoMetrics,
    EcommerceMetrics,
    ProcessingStatus,
    FileType,
)


# ============== Companies ==============

def get_or_create_company(
    session: Session,
    name: str,
    company_type: CompanyType,
    ticker: Optional[str] = None,
    sector: Optional[str] = None,
) -> Company:
    """Récupère ou crée une société."""
    company = session.query(Company).filter(Company.name == name).first()
    if not company:
        company = Company(
            name=name,
            ticker=ticker,
            company_type=company_type,
            sector=sector,
        )
        session.add(company)
        session.commit()
    return company


def get_company_by_name(session: Session, name: str) -> Optional[Company]:
    """Récupère une société par son nom."""
    return session.query(Company).filter(Company.name == name).first()


def get_all_companies(session: Session) -> list[Company]:
    """Récupère toutes les sociétés."""
    return session.query(Company).all()


# ============== Quarters ==============

def get_or_create_quarter(
    session: Session,
    year: int,
    quarter: int,
) -> Quarter:
    """Récupère ou crée un trimestre."""
    q = session.query(Quarter).filter(
        Quarter.year == year,
        Quarter.quarter == quarter,
    ).first()
    if not q:
        label = f"Q{quarter} {year}"
        q = Quarter(year=year, quarter=quarter, label=label)
        session.add(q)
        session.commit()
    return q


def get_all_quarters(session: Session) -> list[Quarter]:
    """Récupère tous les trimestres."""
    return session.query(Quarter).order_by(Quarter.year.desc(), Quarter.quarter.desc()).all()


# ============== CompanyQuarters ==============

def get_or_create_company_quarter(
    session: Session,
    company: Company,
    quarter: Quarter,
) -> CompanyQuarter:
    """Récupère ou crée une association société-trimestre."""
    cq = session.query(CompanyQuarter).filter(
        CompanyQuarter.company_id == company.id,
        CompanyQuarter.quarter_id == quarter.id,
    ).first()
    if not cq:
        cq = CompanyQuarter(
            company_id=company.id,
            quarter_id=quarter.id,
        )
        session.add(cq)
        session.commit()
    return cq


def update_company_quarter_status(
    session: Session,
    company_quarter: CompanyQuarter,
    status: ProcessingStatus,
    needs_review: bool = False,
) -> CompanyQuarter:
    """Met à jour le statut d'un company_quarter."""
    company_quarter.status = status
    company_quarter.needs_review = needs_review
    company_quarter.updated_at = datetime.utcnow()
    if status == ProcessingStatus.NORMALIZED:
        company_quarter.processed_at = datetime.utcnow()
    session.commit()
    return company_quarter


def get_pending_company_quarters(session: Session) -> list[CompanyQuarter]:
    """Récupère les company_quarters en attente de traitement."""
    return session.query(CompanyQuarter).filter(
        CompanyQuarter.status.in_([ProcessingStatus.PENDING, ProcessingStatus.SYNCED])
    ).all()


def get_company_quarters_for_review(session: Session) -> list[CompanyQuarter]:
    """Récupère les company_quarters nécessitant une review."""
    return session.query(CompanyQuarter).filter(
        CompanyQuarter.needs_review == True
    ).all()


# ============== SourceFiles ==============

def create_source_file(
    session: Session,
    company_quarter: CompanyQuarter,
    gdrive_file_id: str,
    filename: str,
    file_type: FileType,
    mime_type: Optional[str] = None,
    gdrive_modified: Optional[datetime] = None,
) -> SourceFile:
    """Crée un nouveau fichier source."""
    source_file = SourceFile(
        company_quarter_id=company_quarter.id,
        gdrive_file_id=gdrive_file_id,
        filename=filename,
        file_type=file_type,
        mime_type=mime_type,
        gdrive_modified=gdrive_modified,
    )
    session.add(source_file)
    session.commit()
    return source_file


def get_source_file_by_gdrive_id(session: Session, gdrive_file_id: str) -> Optional[SourceFile]:
    """Récupère un fichier source par son ID Google Drive."""
    return session.query(SourceFile).filter(SourceFile.gdrive_file_id == gdrive_file_id).first()


def update_source_file_extraction(
    session: Session,
    source_file: SourceFile,
    raw_text: str,
    confidence: float,
    local_path: Optional[str] = None,
) -> SourceFile:
    """Met à jour les données d'extraction d'un fichier source."""
    source_file.raw_extracted_text = raw_text
    source_file.extraction_confidence = confidence
    source_file.extraction_status = ProcessingStatus.EXTRACTED
    if local_path:
        source_file.local_path = local_path
    source_file.updated_at = datetime.utcnow()
    session.commit()
    return source_file


# ============== Financials ==============

def upsert_core_financials(
    session: Session,
    company_quarter: CompanyQuarter,
    **kwargs,
) -> CoreFinancials:
    """Crée ou met à jour les métriques financières core."""
    financials = session.query(CoreFinancials).filter(
        CoreFinancials.company_quarter_id == company_quarter.id
    ).first()

    if not financials:
        financials = CoreFinancials(company_quarter_id=company_quarter.id)
        session.add(financials)

    for key, value in kwargs.items():
        if hasattr(financials, key) and value is not None:
            setattr(financials, key, value)

    financials.updated_at = datetime.utcnow()
    session.commit()
    return financials


def upsert_crypto_metrics(
    session: Session,
    company_quarter: CompanyQuarter,
    **kwargs,
) -> CryptoMetrics:
    """Crée ou met à jour les métriques crypto."""
    metrics = session.query(CryptoMetrics).filter(
        CryptoMetrics.company_quarter_id == company_quarter.id
    ).first()

    if not metrics:
        metrics = CryptoMetrics(company_quarter_id=company_quarter.id)
        session.add(metrics)

    for key, value in kwargs.items():
        if hasattr(metrics, key) and value is not None:
            setattr(metrics, key, value)

    metrics.updated_at = datetime.utcnow()
    session.commit()
    return metrics


def upsert_ecommerce_metrics(
    session: Session,
    company_quarter: CompanyQuarter,
    **kwargs,
) -> EcommerceMetrics:
    """Crée ou met à jour les métriques e-commerce."""
    metrics = session.query(EcommerceMetrics).filter(
        EcommerceMetrics.company_quarter_id == company_quarter.id
    ).first()

    if not metrics:
        metrics = EcommerceMetrics(company_quarter_id=company_quarter.id)
        session.add(metrics)

    for key, value in kwargs.items():
        if hasattr(metrics, key) and value is not None:
            setattr(metrics, key, value)

    metrics.updated_at = datetime.utcnow()
    session.commit()
    return metrics


# ============== Queries ==============

def get_financials_comparison(
    session: Session,
    company_names: list[str],
    year: Optional[int] = None,
    quarter: Optional[int] = None,
) -> list[dict]:
    """Récupère les données financières pour comparaison."""
    query = (
        session.query(Company, Quarter, CoreFinancials, CryptoMetrics, EcommerceMetrics)
        .join(CompanyQuarter, Company.id == CompanyQuarter.company_id)
        .join(Quarter, Quarter.id == CompanyQuarter.quarter_id)
        .outerjoin(CoreFinancials, CoreFinancials.company_quarter_id == CompanyQuarter.id)
        .outerjoin(CryptoMetrics, CryptoMetrics.company_quarter_id == CompanyQuarter.id)
        .outerjoin(EcommerceMetrics, EcommerceMetrics.company_quarter_id == CompanyQuarter.id)
        .filter(Company.name.in_(company_names))
    )

    if year:
        query = query.filter(Quarter.year == year)
    if quarter:
        query = query.filter(Quarter.quarter == quarter)

    results = []
    for company, qtr, core, crypto, ecom in query.all():
        results.append({
            "company": company.name,
            "ticker": company.ticker,
            "company_type": company.company_type.value,
            "quarter": qtr.label,
            "year": qtr.year,
            "quarter_num": qtr.quarter,
            "core_financials": core,
            "crypto_metrics": crypto,
            "ecommerce_metrics": ecom,
        })

    return results
