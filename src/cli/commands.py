from __future__ import annotations
"""Interface CLI pour l'application de résultats trimestriels."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import get_settings
from ..database.models import (
    Company,
    CompanyType,
    ProcessingStatus,
    init_db,
)
from ..database import crud
from ..extractors.factory import ExtractorFactory, extract_file
from ..gdrive.sync import DriveSync, sync_from_drive
from ..parsers.normalizer import normalize_extraction

app = typer.Typer(
    name="qf",
    help="Quarterly Financials - Comparer les résultats trimestriels",
    add_completion=False,
)
console = Console()


@app.command()
def init():
    """Initialise la base de données."""
    settings = get_settings()

    # Créer les dossiers nécessaires
    settings.raw_data_path.mkdir(parents=True, exist_ok=True)
    settings.db_path.mkdir(parents=True, exist_ok=True)

    # Initialiser la DB
    Session = init_db(settings.database_url)

    console.print("[green]Base de données initialisée avec succès![/green]")
    console.print(f"  DB: {settings.db_path / 'financials.db'}")
    console.print(f"  Data: {settings.raw_data_path}")


@app.command()
def sync(
    folder_id: Optional[str] = typer.Option(
        None, "--folder", "-f", help="ID du dossier Google Drive"
    ),
):
    """Synchronise les fichiers depuis Google Drive."""
    try:
        console.print("[bold]Synchronisation depuis Google Drive...[/bold]")

        results = sync_from_drive(folder_id)

        # Afficher les résultats
        for quarter, companies in results.items():
            console.print(f"\n[bold blue]{quarter}[/bold blue]")

            for company, result in companies.items():
                downloaded = len(result.downloaded)
                skipped = len(result.skipped)
                errors = len(result.errors)

                status = "[green]OK[/green]"
                if errors:
                    status = f"[red]{errors} erreurs[/red]"

                console.print(
                    f"  {company}: {downloaded} téléchargés, "
                    f"{skipped} ignorés {status}"
                )

                for error in result.errors:
                    console.print(f"    [red]Erreur: {error}[/red]")

        console.print("\n[green]Synchronisation terminée![/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Erreur: {e}[/red]")
        console.print(
            "\nPour configurer Google Drive:\n"
            "1. Créez un projet sur console.cloud.google.com\n"
            "2. Activez l'API Google Drive\n"
            "3. Créez des credentials OAuth 2.0\n"
            "4. Téléchargez credentials.json dans le projet"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def extract(
    path: Path = typer.Argument(
        ..., help="Chemin vers un fichier ou dossier à extraire"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Affiche plus de détails"),
):
    """Extrait les données d'un fichier ou dossier."""
    path = Path(path)

    if not path.exists():
        console.print(f"[red]Fichier/dossier non trouvé: {path}[/red]")
        raise typer.Exit(1)

    files_to_process = []

    if path.is_file():
        files_to_process.append(path)
    else:
        # Récupérer tous les fichiers supportés
        for ext in ExtractorFactory.get_supported_extensions():
            files_to_process.extend(path.glob(f"**/*{ext}"))

    if not files_to_process:
        console.print("[yellow]Aucun fichier supporté trouvé.[/yellow]")
        raise typer.Exit(0)

    console.print(f"[bold]Extraction de {len(files_to_process)} fichier(s)...[/bold]\n")

    for file_path in files_to_process:
        console.print(f"[blue]{file_path.name}[/blue]")

        try:
            result = extract_file(file_path)

            if verbose:
                console.print(f"  Méthode: {result.extraction_method}")
                console.print(f"  Confiance: {result.confidence_score:.0%}")
                console.print(f"  Tableaux: {len(result.tables)}")
                console.print(f"  Texte: {len(result.raw_text)} caractères")

                if result.warnings:
                    for warning in result.warnings:
                        console.print(f"  [yellow]⚠ {warning}[/yellow]")
            else:
                status = "[green]OK[/green]" if result.confidence_score > 0.7 else "[yellow]Review[/yellow]"
                console.print(f"  {status} - {result.confidence_score:.0%} confiance")

        except Exception as e:
            console.print(f"  [red]Erreur: {e}[/red]")


@app.command()
def status():
    """Affiche le statut des données."""
    settings = get_settings()
    Session = init_db(settings.database_url)
    session = Session()

    try:
        # Compter les sociétés
        companies = crud.get_all_companies(session)
        quarters = crud.get_all_quarters(session)

        table = Table(title="Statut des données")
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="green")

        table.add_row("Sociétés", str(len(companies)))
        table.add_row("Trimestres", str(len(quarters)))

        # Fichiers locaux
        raw_files = list(settings.raw_data_path.glob("**/*"))
        file_count = len([f for f in raw_files if f.is_file()])
        table.add_row("Fichiers téléchargés", str(file_count))

        console.print(table)

        # Liste des sociétés
        if companies:
            console.print("\n[bold]Sociétés enregistrées:[/bold]")
            for company in companies:
                console.print(f"  • {company.name} ({company.company_type.value})")

    finally:
        session.close()


@app.command()
def add_company(
    name: str = typer.Argument(..., help="Nom de la société"),
    company_type: str = typer.Option(
        "crypto", "--type", "-t",
        help="Type: crypto, ecommerce, fintech"
    ),
    ticker: Optional[str] = typer.Option(None, "--ticker", help="Symbole boursier"),
):
    """Ajoute une nouvelle société."""
    settings = get_settings()
    Session = init_db(settings.database_url)
    session = Session()

    try:
        # Valider le type
        try:
            ctype = CompanyType(company_type.lower())
        except ValueError:
            console.print(f"[red]Type invalide: {company_type}[/red]")
            console.print("Types valides: crypto, ecommerce, fintech")
            raise typer.Exit(1)

        company = crud.get_or_create_company(
            session,
            name=name,
            company_type=ctype,
            ticker=ticker,
        )

        console.print(f"[green]Société ajoutée: {company.name}[/green]")

    finally:
        session.close()


@app.command()
def compare(
    companies: list[str] = typer.Argument(..., help="Noms des sociétés à comparer"),
    metric: str = typer.Option("revenue", "--metric", "-m", help="Métrique à comparer"),
):
    """Compare les métriques de plusieurs sociétés."""
    settings = get_settings()
    Session = init_db(settings.database_url)
    session = Session()

    try:
        results = crud.get_financials_comparison(session, companies)

        if not results:
            console.print("[yellow]Aucune donnée trouvée pour ces sociétés.[/yellow]")
            raise typer.Exit(0)

        # Créer le tableau de comparaison
        table = Table(title=f"Comparaison: {metric}")
        table.add_column("Société", style="cyan")
        table.add_column("Trimestre", style="blue")
        table.add_column(metric.replace("_", " ").title(), style="green")

        for row in results:
            value = "N/A"
            if row["core_financials"]:
                val = getattr(row["core_financials"], metric, None)
                if val is not None:
                    value = f"${val:,.2f}M" if "pct" not in metric else f"{val:.1f}%"

            table.add_row(
                row["company"],
                row["quarter"],
                value,
            )

        console.print(table)

    finally:
        session.close()


@app.command("list")
def list_files(
    path: Optional[Path] = typer.Argument(
        None, help="Dossier à lister (défaut: data/raw)"
    ),
):
    """Liste les fichiers téléchargés."""
    settings = get_settings()
    base_path = path or settings.raw_data_path

    if not base_path.exists():
        console.print(f"[yellow]Dossier non trouvé: {base_path}[/yellow]")
        raise typer.Exit(0)

    # Lister par structure trimestre/société
    quarters = sorted([d for d in base_path.iterdir() if d.is_dir()])

    if not quarters:
        console.print("[yellow]Aucun dossier trouvé.[/yellow]")
        raise typer.Exit(0)

    for quarter_dir in quarters:
        console.print(f"\n[bold blue]{quarter_dir.name}[/bold blue]")

        companies = sorted([d for d in quarter_dir.iterdir() if d.is_dir()])
        for company_dir in companies:
            files = list(company_dir.iterdir())
            console.print(f"  [cyan]{company_dir.name}[/cyan]: {len(files)} fichiers")

            for file in sorted(files):
                ext = file.suffix
                size = file.stat().st_size / 1024
                console.print(f"    • {file.name} ({size:.1f} KB)")


@app.command()
def export(
    output: Path = typer.Option(
        Path("export.csv"), "--output", "-o", help="Fichier de sortie"
    ),
    format: str = typer.Option("csv", "--format", "-f", help="Format: csv, json"),
):
    """Exporte les données vers CSV ou JSON."""
    import json
    import csv

    settings = get_settings()
    Session = init_db(settings.database_url)
    session = Session()

    try:
        companies = crud.get_all_companies(session)
        company_names = [c.name for c in companies]

        if not company_names:
            console.print("[yellow]Aucune donnée à exporter.[/yellow]")
            raise typer.Exit(0)

        results = crud.get_financials_comparison(session, company_names)

        if format.lower() == "json":
            # Export JSON
            export_data = []
            for row in results:
                data = {
                    "company": row["company"],
                    "ticker": row["ticker"],
                    "type": row["company_type"],
                    "quarter": row["quarter"],
                }

                if row["core_financials"]:
                    cf = row["core_financials"]
                    data.update({
                        "revenue": float(cf.revenue) if cf.revenue else None,
                        "net_income": float(cf.net_income) if cf.net_income else None,
                        "gross_margin_pct": float(cf.gross_margin_pct) if cf.gross_margin_pct else None,
                    })

                export_data.append(data)

            output = output.with_suffix(".json")
            with open(output, "w") as f:
                json.dump(export_data, f, indent=2)

        else:
            # Export CSV
            output = output.with_suffix(".csv")
            with open(output, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "company", "ticker", "type", "quarter",
                    "revenue", "net_income", "gross_margin_pct"
                ])

                for row in results:
                    cf = row["core_financials"]
                    writer.writerow([
                        row["company"],
                        row["ticker"],
                        row["company_type"],
                        row["quarter"],
                        float(cf.revenue) if cf and cf.revenue else "",
                        float(cf.net_income) if cf and cf.net_income else "",
                        float(cf.gross_margin_pct) if cf and cf.gross_margin_pct else "",
                    ])

        console.print(f"[green]Données exportées vers: {output}[/green]")

    finally:
        session.close()


if __name__ == "__main__":
    app()
