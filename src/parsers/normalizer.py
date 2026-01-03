from __future__ import annotations
"""Normaliseur de données financières."""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Optional

from ..database.models import CompanyType
from ..extractors.base import ExtractionResult
from ..models.financials import (
    CoreFinancialsSchema,
    CryptoMetricsSchema,
    EcommerceMetricsSchema,
)
from .metric_patterns import extract_all_metrics, extract_metric


@dataclass
class NormalizationResult:
    """Résultat de la normalisation des données."""
    core: CoreFinancialsSchema
    crypto: Optional[CryptoMetricsSchema] = None
    ecommerce: Optional[EcommerceMetricsSchema] = None
    confidence: float = 0.0
    needs_review: bool = False
    warnings: list[str] = field(default_factory=list)
    extracted_metrics: dict = field(default_factory=dict)


class FinancialsNormalizer:
    """Normalise les données extraites en schémas financiers uniformes."""

    # Seuil de confiance en dessous duquel on flag pour review
    REVIEW_THRESHOLD = 0.7

    def normalize(
        self,
        extraction: ExtractionResult,
        company_name: str,
        company_type: CompanyType,
    ) -> NormalizationResult:
        """
        Normalise les données extraites.

        Args:
            extraction: Résultat de l'extraction
            company_name: Nom de la société
            company_type: Type de société (crypto, ecommerce, etc.)

        Returns:
            NormalizationResult avec les schémas validés
        """
        warnings = list(extraction.warnings)

        # Extraire toutes les métriques du texte
        metrics = extract_all_metrics(extraction.raw_text)

        # Essayer d'extraire aussi des tableaux
        table_metrics = self._extract_from_tables(extraction.tables)
        metrics.update(table_metrics)

        # Construire le schéma core (toutes les sociétés)
        core = self._build_core_financials(metrics)

        # Construire les schémas spécifiques selon le type
        crypto = None
        ecommerce = None

        if company_type == CompanyType.CRYPTO:
            crypto = self._build_crypto_metrics(metrics)
        elif company_type == CompanyType.ECOMMERCE:
            ecommerce = self._build_ecommerce_metrics(metrics)

        # Calculer la confiance globale
        confidence = self._calculate_confidence(
            extraction.confidence_score,
            core,
            crypto,
            ecommerce,
        )

        # Déterminer si une review est nécessaire
        needs_review = confidence < self.REVIEW_THRESHOLD

        if needs_review:
            warnings.append(
                f"Confiance faible ({confidence:.0%}), review manuelle recommandée."
            )

        return NormalizationResult(
            core=core,
            crypto=crypto,
            ecommerce=ecommerce,
            confidence=confidence,
            needs_review=needs_review,
            warnings=warnings,
            extracted_metrics=metrics,
        )

    def _build_core_financials(self, metrics: dict) -> CoreFinancialsSchema:
        """Construit le schéma CoreFinancials depuis les métriques extraites."""
        return CoreFinancialsSchema(
            revenue=metrics.get("revenue"),
            gross_profit=metrics.get("gross_profit"),
            operating_income=metrics.get("operating_income"),
            net_income=metrics.get("net_income"),
            gross_margin_pct=metrics.get("gross_margin_pct"),
            operating_margin_pct=metrics.get("operating_margin_pct"),
            net_margin_pct=metrics.get("net_margin_pct"),
            eps=metrics.get("eps"),
            eps_diluted=metrics.get("eps_diluted"),
            revenue_yoy_pct=metrics.get("revenue_yoy_pct"),
            revenue_qoq_pct=metrics.get("revenue_qoq_pct"),
            guidance_revenue_low=metrics.get("guidance_revenue_low"),
            guidance_revenue_high=metrics.get("guidance_revenue_high"),
        )

    def _build_crypto_metrics(self, metrics: dict) -> CryptoMetricsSchema:
        """Construit le schéma CryptoMetrics depuis les métriques extraites."""
        return CryptoMetricsSchema(
            trading_volume=metrics.get("trading_volume"),
            transaction_revenue=metrics.get("transaction_revenue"),
            subscription_revenue=metrics.get("subscription_revenue"),
            blockchain_rewards_revenue=metrics.get("blockchain_rewards_revenue"),
            assets_on_platform=metrics.get("assets_on_platform"),
            custody_assets=metrics.get("custody_assets"),
            stablecoin_market_cap=metrics.get("stablecoin_market_cap"),
            monthly_transacting_users=self._to_int(metrics.get("monthly_transacting_users")),
            verified_users=self._to_int(metrics.get("verified_users")),
        )

    def _build_ecommerce_metrics(self, metrics: dict) -> EcommerceMetricsSchema:
        """Construit le schéma EcommerceMetrics depuis les métriques extraites."""
        return EcommerceMetricsSchema(
            gmv=metrics.get("gmv"),
            orders=self._to_int(metrics.get("orders")),
            average_order_value=metrics.get("average_order_value"),
            active_customers=self._to_int(metrics.get("active_customers")),
            prime_members=self._to_int(metrics.get("prime_members")),
            aws_revenue=metrics.get("aws_revenue"),
            advertising_revenue=metrics.get("advertising_revenue"),
            third_party_seller_pct=metrics.get("third_party_seller_pct"),
            fulfillment_cost=metrics.get("fulfillment_cost"),
        )

    def _extract_from_tables(self, tables: list[dict]) -> dict:
        """Extrait des métriques depuis les tableaux."""
        metrics = {}

        for table in tables:
            rows = table.get("rows", [])
            for row in rows:
                # Chercher des patterns dans les valeurs du tableau
                for key, value in row.items():
                    if not isinstance(value, str):
                        continue

                    key_lower = key.lower()
                    value_clean = value.strip()

                    # Mapper les clés de tableau vers les métriques
                    if "revenue" in key_lower and value_clean:
                        extracted = extract_metric(f"revenue: {value_clean}", "revenue")
                        if extracted:
                            metrics["revenue"] = extracted

                    elif "net income" in key_lower and value_clean:
                        extracted = extract_metric(f"net income: {value_clean}", "net_income")
                        if extracted:
                            metrics["net_income"] = extracted

                    # Ajouter d'autres mappings au besoin...

        return metrics

    def _calculate_confidence(
        self,
        extraction_confidence: float,
        core: CoreFinancialsSchema,
        crypto: Optional[CryptoMetricsSchema],
        ecommerce: Optional[EcommerceMetricsSchema],
    ) -> float:
        """Calcule le score de confiance global."""
        score = extraction_confidence * 0.5  # 50% basé sur l'extraction

        # Bonus si des métriques core ont été trouvées
        core_dict = core.model_dump(exclude_none=True)
        if core_dict:
            # Plus on a de métriques, plus on est confiant
            metrics_found = len(core_dict)
            score += min(0.3, metrics_found * 0.05)

        # Revenue est critique - bonus si trouvé
        if core.revenue is not None:
            score += 0.1

        # Bonus pour les métriques spécifiques au type
        if crypto:
            crypto_dict = crypto.model_dump(exclude_none=True)
            if crypto_dict:
                score += min(0.1, len(crypto_dict) * 0.02)

        if ecommerce:
            ecom_dict = ecommerce.model_dump(exclude_none=True)
            if ecom_dict:
                score += min(0.1, len(ecom_dict) * 0.02)

        return min(score, 1.0)

    @staticmethod
    def _to_int(value: Optional[Decimal]) -> Optional[int]:
        """Convertit une Decimal en int si possible."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None


def normalize_extraction(
    extraction: ExtractionResult,
    company_name: str,
    company_type: CompanyType,
) -> NormalizationResult:
    """
    Fonction utilitaire pour normaliser une extraction.

    Args:
        extraction: Résultat d'extraction
        company_name: Nom de la société
        company_type: Type de société

    Returns:
        NormalizationResult
    """
    normalizer = FinancialsNormalizer()
    return normalizer.normalize(extraction, company_name, company_type)
