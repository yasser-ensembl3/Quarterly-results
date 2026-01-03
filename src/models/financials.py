from __future__ import annotations
"""Schémas Pydantic pour la validation des données financières."""

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class CompanyType(str, Enum):
    """Type de société."""
    CRYPTO = "crypto"
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"


class CoreFinancialsSchema(BaseModel):
    """Schéma pour les métriques financières universelles."""

    # Revenue & Profit (en millions USD)
    revenue: Optional[Decimal] = Field(None, description="Chiffre d'affaires total en millions USD")
    gross_profit: Optional[Decimal] = Field(None, description="Bénéfice brut en millions USD")
    operating_income: Optional[Decimal] = Field(None, description="Résultat opérationnel en millions USD")
    net_income: Optional[Decimal] = Field(None, description="Résultat net en millions USD")

    # Marges (en pourcentage)
    gross_margin_pct: Optional[Decimal] = Field(None, ge=0, le=100, description="Marge brute en %")
    operating_margin_pct: Optional[Decimal] = Field(None, description="Marge opérationnelle en %")
    net_margin_pct: Optional[Decimal] = Field(None, description="Marge nette en %")

    # Par action
    eps: Optional[Decimal] = Field(None, description="Bénéfice par action")
    eps_diluted: Optional[Decimal] = Field(None, description="BPA dilué")

    # Croissance (en pourcentage)
    revenue_yoy_pct: Optional[Decimal] = Field(None, description="Croissance revenue YoY en %")
    revenue_qoq_pct: Optional[Decimal] = Field(None, description="Croissance revenue QoQ en %")

    # Guidance
    guidance_revenue_low: Optional[Decimal] = Field(None, description="Guidance revenue basse")
    guidance_revenue_high: Optional[Decimal] = Field(None, description="Guidance revenue haute")
    guidance_notes: Optional[str] = Field(None, description="Notes sur la guidance")

    @model_validator(mode="after")
    def calculate_margins(self):
        """Calcule les marges si non fournies."""
        if self.revenue and self.revenue > 0:
            if self.gross_profit and not self.gross_margin_pct:
                self.gross_margin_pct = (self.gross_profit / self.revenue) * 100
            if self.operating_income and not self.operating_margin_pct:
                self.operating_margin_pct = (self.operating_income / self.revenue) * 100
            if self.net_income and not self.net_margin_pct:
                self.net_margin_pct = (self.net_income / self.revenue) * 100
        return self

    class Config:
        from_attributes = True


class CryptoMetricsSchema(BaseModel):
    """Schéma pour les métriques crypto (Coinbase, Circle, etc.)."""

    # Volume & Revenue
    trading_volume: Optional[Decimal] = Field(None, description="Volume de trading total en USD")
    transaction_revenue: Optional[Decimal] = Field(None, description="Revenus de transaction")
    subscription_revenue: Optional[Decimal] = Field(None, description="Revenus d'abonnement")
    blockchain_rewards_revenue: Optional[Decimal] = Field(None, description="Revenus de staking/rewards")

    # Assets
    assets_on_platform: Optional[Decimal] = Field(None, description="Assets sous gestion (AUC/AUM)")
    custody_assets: Optional[Decimal] = Field(None, description="Assets en custody")
    stablecoin_market_cap: Optional[Decimal] = Field(None, description="Market cap stablecoin (USDC)")

    # Users
    monthly_transacting_users: Optional[int] = Field(None, ge=0, description="MTU")
    verified_users: Optional[int] = Field(None, ge=0, description="Utilisateurs vérifiés")

    class Config:
        from_attributes = True


class EcommerceMetricsSchema(BaseModel):
    """Schéma pour les métriques e-commerce (Amazon, etc.)."""

    # Volume & Orders
    gmv: Optional[Decimal] = Field(None, description="Gross Merchandise Volume")
    orders: Optional[int] = Field(None, ge=0, description="Nombre de commandes")
    average_order_value: Optional[Decimal] = Field(None, description="Panier moyen")

    # Customers
    active_customers: Optional[int] = Field(None, ge=0, description="Clients actifs")
    prime_members: Optional[int] = Field(None, ge=0, description="Membres Prime (Amazon)")

    # Segments
    aws_revenue: Optional[Decimal] = Field(None, description="Revenue AWS (Amazon)")
    advertising_revenue: Optional[Decimal] = Field(None, description="Revenue publicitaire")
    third_party_seller_pct: Optional[Decimal] = Field(None, ge=0, le=100, description="% vendeurs tiers")

    # Costs
    fulfillment_cost: Optional[Decimal] = Field(None, description="Coût de fulfillment")

    class Config:
        from_attributes = True


class CompanySchema(BaseModel):
    """Schéma pour une société."""
    name: str = Field(..., min_length=1, description="Nom de la société")
    ticker: Optional[str] = Field(None, max_length=20, description="Symbole boursier")
    company_type: CompanyType = Field(..., description="Type de société")
    sector: Optional[str] = Field(None, description="Secteur d'activité")

    class Config:
        from_attributes = True


class QuarterSchema(BaseModel):
    """Schéma pour un trimestre."""
    year: int = Field(..., ge=2000, le=2100, description="Année")
    quarter: int = Field(..., ge=1, le=4, description="Trimestre (1-4)")

    @property
    def label(self) -> str:
        return f"Q{self.quarter} {self.year}"

    class Config:
        from_attributes = True


class FullFinancialsSchema(BaseModel):
    """Schéma complet avec toutes les données financières."""
    company: CompanySchema
    quarter: QuarterSchema
    core: CoreFinancialsSchema
    crypto: Optional[CryptoMetricsSchema] = None
    ecommerce: Optional[EcommerceMetricsSchema] = None

    class Config:
        from_attributes = True


class ExtractionResultSchema(BaseModel):
    """Résultat d'extraction de fichier."""
    raw_text: str = Field(..., description="Texte brut extrait")
    tables: list[dict] = Field(default_factory=list, description="Tableaux extraits")
    extraction_method: str = Field(..., description="Méthode d'extraction utilisée")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Score de confiance")
    warnings: list[str] = Field(default_factory=list, description="Avertissements")
