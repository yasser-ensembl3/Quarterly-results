from __future__ import annotations
"""Patterns regex pour l'extraction des métriques financières."""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional


# ============== Patterns pour les métriques ==============

METRIC_PATTERNS = {
    # ==================== CORE FINANCIALS ====================

    # Revenue
    "revenue": [
        r"(?:total\s+)?(?:net\s+)?revenue[:\s]+\$?([\d,\.]+)\s*(B|M|billion|million)?",
        r"net\s+revenue[:\s]+([\d,\.]+)\s*(B|M)?",
        r"Total\s+Revenue\s+.*?([\d,\.]+)\s*$",
        r"net\s+sales[:\s]+\$?([\d,\.]+)\s*(B|M)?",
    ],

    # Net Income
    "net_income": [
        r"net\s+income\s+(?:was\s+)?\$?([\d,\.]+)\s*(B|M|billion|million)?",
        r"net\s+income[:\s]+\$?([\d,\.]+)\s*(B|M)?",
        r"Net\s+Income\s+.*?([\d,\.]+)\s*$",
    ],

    # Adjusted Net Income
    "adjusted_net_income": [
        r"adjusted\s+net\s+income\s+(?:was\s+)?\$?([\d,\.]+)\s*(B|M|billion|million)?",
        r"Adjusted\s+Net\s+Income[:\s]+\$?([\d,\.]+)\s*(B|M)?",
    ],

    # EBITDA
    "adjusted_ebitda": [
        r"adjusted\s+EBITDA\s+(?:was\s+)?\$?([\d,\.]+)\s*(B|M|billion|million)?",
        r"Adjusted\s+EBITDA[:\s]+\$?([\d,\.]+)\s*(B|M)?",
        r"Adjusted\s+EBITDA\s+.*?([\d,\.]+)\s*$",
    ],

    # Operating Expenses
    "operating_expenses": [
        r"(?:total\s+)?operating\s+expenses?[:\s]+\$?([\d,\.]+)\s*(B|M|billion|million)?",
        r"operating\s+expenses?\s+(?:was|were|of)\s+\$?([\d,\.]+)\s*(B|M)?",
        r"Total\s+operating\s+expenses\s+.*?([\d,\.]+)",
    ],

    # Gross Profit
    "gross_profit": [
        r"gross\s+profit[:\s]+\$?([\d,\.]+)\s*(B|M)?",
    ],

    # Operating Income
    "operating_income": [
        r"operating\s+income[:\s]+\$?([\d,\.]+)\s*(B|M)?",
        r"income\s+from\s+operations[:\s]+\$?([\d,\.]+)",
    ],

    # ==================== MARGINS ====================

    "gross_margin_pct": [
        r"gross\s+margin[:\s]+([\d\.]+)\s*%",
        r"gross\s+profit\s+margin[:\s]+([\d\.]+)\s*%",
    ],
    "operating_margin_pct": [
        r"operating\s+margin[:\s]+([\d\.]+)\s*%",
    ],
    "net_margin_pct": [
        r"net\s+(?:profit\s+)?margin[:\s]+([\d\.]+)\s*%",
    ],

    # ==================== EPS ====================

    "eps": [
        r"(?:basic\s+)?(?:earnings|EPS)\s+per\s+share[:\s]+\$?([\d\.]+)",
        r"EPS[:\s]+\$?([\d\.]+)",
        r"earnings\s+per\s+share[:\s]+\$?([\d\.]+)",
    ],
    "eps_diluted": [
        r"diluted\s+(?:earnings|EPS)(?:\s+per\s+share)?[:\s]+\$?([\d\.]+)",
        r"diluted\s+EPS[:\s]+\$?([\d\.]+)",
    ],

    # ==================== GROWTH METRICS ====================

    "revenue_yoy_pct": [
        r"revenue\s+(?:growth|increased|up)\s+([\d\.]+)\s*%\s*(?:YoY|year.over.year|Y/Y)?",
        r"(?:YoY|year.over.year|Y/Y)\s+(?:revenue\s+)?growth[:\s]+([\d\.]+)\s*%",
        r"revenue.*?up\s+([\d\.]+)\s*%\s*(?:YoY|year.over.year|Y/Y)",
    ],
    "revenue_qoq_pct": [
        r"revenue.*?up\s+([\d\.]+)\s*%\s*(?:QoQ|Q/Q|quarter.over.quarter)",
        r"(?:QoQ|Q/Q)\s+(?:revenue\s+)?growth[:\s]+([\d\.]+)\s*%",
        r"revenue.*?(?:up|increased)\s+([\d\.]+)\s*%\s*Q/Q",
    ],

    # ==================== EMPLOYEES ====================

    "employees": [
        r"(?:full.time\s+)?employees?\s+(?:increased\s+)?(?:to\s+)?([\d,]+)",
        r"([\d,]+)\s+(?:full.time\s+)?employees",
        r"headcount[:\s]+([\d,]+)",
    ],

    # ==================== CRYPTO METRICS ====================

    # Trading Volume
    "trading_volume": [
        r"trading\s+volume[:\s]+\$?([\d,\.]+)\s*(B|T|billion|trillion)?",
        r"total\s+trading\s+volume[:\s]+\$?([\d,\.]+)\s*(B|T)?",
        r"Trading\s+Volume\s+.*?([\d,\.]+)\s*(B|T)?",
    ],

    # Transaction Revenue
    "transaction_revenue": [
        r"transaction\s+revenue\s+(?:was\s+)?\$?([\d,\.]+)\s*(B|M|billion|million)?",
        r"Total\s+Transaction\s+Revenue\s+.*?([\d,\.]+)",
        r"transaction\s+revenue[:\s]+\$?([\d,\.]+)\s*(B|M)?",
    ],

    # Consumer Transaction Revenue
    "consumer_transaction_revenue": [
        r"Consumer,?\s+net\s+.*?([\d,\.]+)",
        r"consumer\s+transaction\s+revenue[:\s]+\$?([\d,\.]+)\s*(M)?",
    ],

    # Institutional Transaction Revenue
    "institutional_transaction_revenue": [
        r"Institutional,?\s+net\s+.*?([\d,\.]+)",
        r"institutional\s+transaction\s+revenue[:\s]+\$?([\d,\.]+)\s*(M)?",
    ],

    # Subscription & Services Revenue
    "subscription_revenue": [
        r"subscription\s+and\s+services\s+revenue\s+(?:was\s+)?\$?([\d,\.]+)\s*(B|M|million)?",
        r"Total\s+Subscription\s+and\s+Services\s+Revenue\s+.*?([\d,\.]+)",
        r"subscription\s+(?:and\s+services\s+)?revenue[:\s]+\$?([\d,\.]+)\s*(M)?",
    ],

    # Stablecoin Revenue
    "stablecoin_revenue": [
        r"stablecoin\s+revenue[:\s]+\$?([\d,\.]+)\s*(M)?",
        r"Stablecoin\s+revenue\s+.*?([\d,\.]+)",
    ],

    # Blockchain Rewards
    "blockchain_rewards_revenue": [
        r"blockchain\s+rewards?[:\s]+\$?([\d,\.]+)\s*(M)?",
        r"Blockchain\s+rewards\s+.*?([\d,\.]+)",
        r"staking\s+revenue[:\s]+\$?([\d,\.]+)\s*(M)?",
    ],

    # Interest Income
    "interest_income": [
        r"interest\s+(?:and\s+finance\s+fee\s+)?income[:\s]+\$?([\d,\.]+)\s*(M)?",
        r"Interest\s+and\s+finance\s+fee\s+income\s+.*?([\d,\.]+)",
        r"interest\s+income[:\s]+\$?([\d,\.]+)",
    ],

    # Assets on Platform
    "assets_on_platform": [
        r"assets?\s+on\s+platform[:\s]+\$?([\d,\.]+)\s*(B|T|billion|trillion)?",
        r"AoP[:\s]+\$?([\d,\.]+)\s*(B|T)?",
    ],

    # Assets Under Custody
    "assets_under_custody": [
        r"assets?\s+under\s+custody[:\s]+\$?([\d,\.]+)\s*(B|T|billion|trillion)?",
        r"AUC[:\s]+\$?([\d,\.]+)\s*(B|T)?",
        r"custody\s+assets?[:\s]+\$?([\d,\.]+)\s*(B|T)?",
    ],

    # USDC Market Cap
    "usdc_market_cap": [
        r"USDC\s+(?:reached\s+)?(?:an\s+)?(?:all.time\s+high\s+)?(?:of\s+)?\$?([\d,\.]+)\s*(B|billion)\s+(?:in\s+)?market\s+cap",
        r"USDC\s+market\s+cap(?:italization)?[:\s]+\$?([\d,\.]+)\s*(B|billion)?",
    ],

    # Average USDC on Platform
    "usdc_on_platform": [
        r"(?:average\s+)?USDC\s+(?:held\s+)?(?:in\s+)?(?:Coinbase\s+)?(?:products?\s+)?(?:reached\s+)?(?:an\s+)?(?:all.time\s+high\s+)?(?:of\s+)?(?:over\s+)?\$?([\d,\.]+)\s*(B|billion)",
    ],

    # Verified Users
    "verified_users": [
        r"verified\s+users?[:\s]+([\d,\.]+)\s*(M|million)?",
        r"([\d,\.]+)\s*(M|million)?\s+verified\s+users?",
    ],

    # Monthly Transacting Users
    "monthly_transacting_users": [
        r"(?:monthly\s+transacting\s+users?|MTU)[:\s]+([\d,\.]+)\s*(M|million)?",
        r"([\d,\.]+)\s*(M|million)?\s+(?:monthly\s+)?transacting\s+users?",
    ],

    # ==================== E-COMMERCE METRICS ====================

    # GMV
    "gmv": [
        r"(?:gross\s+merchandise\s+(?:value|volume)|GMV)[:\s]+\$?([\d,\.]+)\s*(B|T|billion|trillion)?",
    ],

    # AWS Revenue
    "aws_revenue": [
        r"AWS\s+(?:revenue|sales|segment)[:\s]+\$?([\d,\.]+)\s*(B|M|billion|million)?",
        r"Amazon\s+Web\s+Services[:\s]+\$?([\d,\.]+)\s*(B|M)?",
    ],

    # Advertising Revenue
    "advertising_revenue": [
        r"advertising\s+(?:revenue|sales)[:\s]+\$?([\d,\.]+)\s*(B|M|billion|million)?",
        r"ad\s+revenue[:\s]+\$?([\d,\.]+)\s*(B|M)?",
    ],

    # Active Customers
    "active_customers": [
        r"active\s+(?:customer|buyer|user)s?[:\s]+([\d,\.]+)\s*(M|million)?",
        r"([\d,\.]+)\s*(M|million)?\s+active\s+(?:customer|buyer|user)s?",
    ],

    # Prime Members
    "prime_members": [
        r"prime\s+members?[:\s]+([\d,\.]+)\s*(M|million)?",
        r"([\d,\.]+)\s*(M|million)?\s+prime\s+members?",
    ],

    # Orders
    "orders": [
        r"(?:total\s+)?orders?[:\s]+([\d,\.]+)\s*(M|million|B|billion)?",
        r"([\d,\.]+)\s*(M|million)?\s+orders",
    ],

    # Third Party Seller %
    "third_party_seller_pct": [
        r"third.party\s+seller[s\s]*[:\s]+([\d\.]+)\s*%",
        r"3P\s+(?:seller\s+)?(?:percentage|%|mix)[:\s]+([\d\.]+)",
    ],

    # Fulfillment Cost
    "fulfillment_cost": [
        r"fulfillment\s+cost[s]?[:\s]+\$?([\d,\.]+)\s*(B|M|billion|million)?",
    ],
}


# ============== Fonctions d'extraction ==============

def normalize_number(value: str, unit: Optional[str] = None) -> Decimal:
    """
    Normalise une valeur numérique extraite.

    Args:
        value: Valeur brute (ex: "1,234.56")
        unit: Unité (B, M, T, billion, million, trillion)

    Returns:
        Valeur en Decimal (en millions par défaut pour les financiers)
    """
    # Nettoyer la valeur
    clean_value = value.replace(",", "").strip()
    number = Decimal(clean_value)

    # Appliquer le multiplicateur selon l'unité
    if unit:
        unit_lower = unit.lower()
        if unit_lower in ("t", "trillion"):
            number *= Decimal("1000000")  # En millions
        elif unit_lower in ("b", "billion"):
            number *= Decimal("1000")  # En millions
        elif unit_lower in ("m", "million"):
            pass  # Déjà en millions
        elif unit_lower in ("k", "thousand"):
            number /= Decimal("1000")  # En millions

    return number


def extract_metric(text: str, metric_name: str) -> Optional[Decimal]:
    """
    Extrait une métrique spécifique du texte.

    Args:
        text: Texte source
        metric_name: Nom de la métrique (clé dans METRIC_PATTERNS)

    Returns:
        Valeur extraite ou None
    """
    patterns = METRIC_PATTERNS.get(metric_name, [])

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1)
            unit = match.group(2) if len(match.groups()) > 1 else None
            try:
                return normalize_number(value, unit)
            except (ValueError, InvalidOperation):
                continue

    return None


def extract_all_metrics(text: str) -> dict[str, Optional[Decimal]]:
    """
    Extrait toutes les métriques connues du texte.

    Args:
        text: Texte source

    Returns:
        Dict avec toutes les métriques trouvées
    """
    results = {}
    for metric_name in METRIC_PATTERNS:
        value = extract_metric(text, metric_name)
        if value is not None:
            results[metric_name] = value
    return results


def find_metric_mentions(text: str, metric_name: str) -> list[dict]:
    """
    Trouve toutes les mentions d'une métrique dans le texte.

    Utile pour le debugging et la validation.

    Args:
        text: Texte source
        metric_name: Nom de la métrique

    Returns:
        Liste de dicts avec position, match, valeur
    """
    patterns = METRIC_PATTERNS.get(metric_name, [])
    mentions = []

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            mentions.append({
                "pattern": pattern,
                "match": match.group(0),
                "value": match.group(1),
                "unit": match.group(2) if len(match.groups()) > 1 else None,
                "start": match.start(),
                "end": match.end(),
            })

    return mentions


# ============== Aliases pour les noms de métriques ==============

METRIC_ALIASES = {
    # Revenue aliases
    "net sales": "revenue",
    "total revenue": "revenue",
    "total net revenue": "revenue",
    "sales": "revenue",

    # Profit aliases
    "earnings": "net_income",
    "profit": "net_income",
    "net profit": "net_income",

    # Margin aliases
    "gm": "gross_margin_pct",
    "gross margin": "gross_margin_pct",
    "operating margin": "operating_margin_pct",

    # Crypto aliases
    "auc": "assets_under_custody",
    "aop": "assets_on_platform",
    "aum": "assets_on_platform",
    "mtu": "monthly_transacting_users",
}


def resolve_metric_alias(name: str) -> str:
    """
    Résout un alias de métrique vers son nom canonique.

    Args:
        name: Nom ou alias de la métrique

    Returns:
        Nom canonique de la métrique
    """
    return METRIC_ALIASES.get(name.lower().strip(), name)
