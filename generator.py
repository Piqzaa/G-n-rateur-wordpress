#!/usr/bin/env python3
"""
WordPress Module Generator CLI
Génère des modules WordPress complets avec CPT, ACF, templates et shortcodes.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import click
from jinja2 import Environment, FileSystemLoader

# Types de champs supportés
SUPPORTED_TYPES = {
    "text": {"type": "text", "label": "Texte"},
    "textarea": {"type": "textarea", "label": "Zone de texte"},
    "image": {"type": "image", "label": "Image", "return_format": "array", "preview_size": "medium"},
    "number": {"type": "number", "label": "Nombre"},
    "wysiwyg": {"type": "wysiwyg", "label": "Éditeur WYSIWYG", "tabs": "all", "toolbar": "full"},
    "select": {"type": "select", "label": "Liste déroulante", "choices": {"option1": "Option 1", "option2": "Option 2"}},
    "date": {"type": "date_picker", "label": "Date", "display_format": "d/m/Y", "return_format": "Y-m-d"},
}


class Field(NamedTuple):
    """Représente un champ ACF."""
    name: str
    field_type: str
    label: str


def slugify(text: str) -> str:
    """Convertit un texte en slug WordPress."""
    text = text.lower()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def to_snake_case(text: str) -> str:
    """Convertit un texte en snake_case."""
    text = slugify(text)
    return text.replace('-', '_')


def to_label(text: str) -> str:
    """Convertit un slug en label lisible."""
    return text.replace('-', ' ').replace('_', ' ').title()


def parse_field(field_str: str) -> Field:
    """Parse une définition de champ 'nom:type'."""
    if ':' not in field_str:
        raise click.BadParameter(f"Format invalide: {field_str}. Utilisez 'nom:type'")

    name, field_type = field_str.split(':', 1)

    if field_type not in SUPPORTED_TYPES:
        raise click.BadParameter(
            f"Type '{field_type}' non supporté. Types valides: {', '.join(SUPPORTED_TYPES.keys())}"
        )

    return Field(
        name=to_snake_case(name),
        field_type=field_type,
        label=to_label(name)
    )


def generate_field_key(module_name: str, field_name: str) -> str:
    """Génère une clé unique pour un champ ACF."""
    import hashlib
    unique_str = f"{module_name}_{field_name}"
    hash_suffix = hashlib.md5(unique_str.encode()).hexdigest()[:8]
    return f"field_{hash_suffix}"


def generate_group_key(module_name: str) -> str:
    """Génère une clé unique pour un groupe ACF."""
    import hashlib
    hash_suffix = hashlib.md5(module_name.encode()).hexdigest()[:8]
    return f"group_{hash_suffix}"


def build_acf_field(field: Field, module_name: str, order: int) -> dict:
    """Construit la configuration ACF pour un champ."""
    type_config = SUPPORTED_TYPES[field.field_type].copy()
    field_type = type_config.pop("type")
    type_config.pop("label", None)

    acf_field = {
        "key": generate_field_key(module_name, field.name),
        "label": field.label,
        "name": field.name,
        "type": field_type,
        "instructions": "",
        "required": 0,
        "conditional_logic": 0,
        "wrapper": {
            "width": "",
            "class": "",
            "id": ""
        },
        **type_config
    }

    return acf_field


def build_acf_json(module_name: str, slug: str, fields: list[Field]) -> dict:
    """Construit le fichier JSON ACF complet."""
    acf_fields = [
        build_acf_field(field, module_name, i)
        for i, field in enumerate(fields)
    ]

    return {
        "key": generate_group_key(module_name),
        "title": f"Champs {module_name}",
        "fields": acf_fields,
        "location": [
            [
                {
                    "param": "post_type",
                    "operator": "==",
                    "value": slug
                }
            ]
        ],
        "menu_order": 0,
        "position": "normal",
        "style": "default",
        "label_placement": "top",
        "instruction_placement": "label",
        "hide_on_screen": "",
        "active": True,
        "description": f"Groupe de champs pour le module {module_name}",
        "show_in_rest": 1,
        "modified": int(datetime.now().timestamp())
    }


class WordPressModuleGenerator:
    """Générateur de modules WordPress."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.template_dir = Path(__file__).parent / "templates" / "wordpress"
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate(self, module_name: str, fields: list[Field]) -> Path:
        """Génère un module WordPress complet."""
        slug = slugify(module_name)
        snake_name = to_snake_case(module_name)
        module_dir = self.output_dir / slug

        # Créer les répertoires
        module_dir.mkdir(parents=True, exist_ok=True)
        (module_dir / "acf-json").mkdir(exist_ok=True)

        # Contexte pour les templates
        context = {
            "module_name": module_name,
            "slug": slug,
            "snake_name": snake_name,
            "prefix": snake_name[:3],
            "fields": fields,
            "field_types": SUPPORTED_TYPES,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Générer les fichiers
        self._generate_cpt(module_dir, context)
        self._generate_acf_json(module_dir, context, fields)
        self._generate_single_template(module_dir, context)
        self._generate_archive_template(module_dir, context)
        self._generate_shortcode(module_dir, context)
        self._generate_main_plugin(module_dir, context)
        self._generate_readme(module_dir, context)

        return module_dir

    def _generate_cpt(self, module_dir: Path, context: dict) -> None:
        """Génère le fichier Custom Post Type."""
        template = self.env.get_template("cpt.php.j2")
        content = template.render(**context)
        (module_dir / "includes" ).mkdir(exist_ok=True)
        (module_dir / "includes" / f"cpt-{context['slug']}.php").write_text(content)

    def _generate_acf_json(self, module_dir: Path, context: dict, fields: list[Field]) -> None:
        """Génère le fichier ACF JSON."""
        acf_data = build_acf_json(context["module_name"], context["slug"], fields)
        acf_file = module_dir / "acf-json" / f"{acf_data['key']}.json"
        acf_file.write_text(json.dumps(acf_data, indent=2, ensure_ascii=False))

    def _generate_single_template(self, module_dir: Path, context: dict) -> None:
        """Génère le template single."""
        template = self.env.get_template("single.php.j2")
        content = template.render(**context)
        (module_dir / "templates").mkdir(exist_ok=True)
        (module_dir / "templates" / f"single-{context['slug']}.php").write_text(content)

    def _generate_archive_template(self, module_dir: Path, context: dict) -> None:
        """Génère le template archive."""
        template = self.env.get_template("archive.php.j2")
        content = template.render(**context)
        (module_dir / "templates").mkdir(exist_ok=True)
        (module_dir / "templates" / f"archive-{context['slug']}.php").write_text(content)

    def _generate_shortcode(self, module_dir: Path, context: dict) -> None:
        """Génère le fichier shortcode."""
        template = self.env.get_template("shortcode.php.j2")
        content = template.render(**context)
        (module_dir / "includes").mkdir(exist_ok=True)
        (module_dir / "includes" / f"shortcode-{context['slug']}.php").write_text(content)

    def _generate_main_plugin(self, module_dir: Path, context: dict) -> None:
        """Génère le fichier principal du plugin."""
        template = self.env.get_template("plugin.php.j2")
        content = template.render(**context)
        (module_dir / f"{context['slug']}.php").write_text(content)

    def _generate_readme(self, module_dir: Path, context: dict) -> None:
        """Génère le README avec instructions d'installation."""
        template = self.env.get_template("README.md.j2")
        content = template.render(**context)
        (module_dir / "README.md").write_text(content)


@click.group()
@click.version_option(version="1.0.0", prog_name="wp-gen")
def cli():
    """WordPress Module Generator - Génère des modules WordPress complets."""
    pass


@cli.command()
@click.argument("name")
@click.argument("fields", nargs=-1, required=True)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="output",
    help="Répertoire de sortie (défaut: ./output)"
)
def module(name: str, fields: tuple[str, ...], output: str) -> None:
    """
    Génère un module WordPress complet.

    NAME: Nom du module (ex: Produit, Témoignage)

    FIELDS: Liste des champs au format nom:type

    Types supportés: text, textarea, image, number, wysiwyg, select, date

    Exemple:
        wp-gen module Produit titre:text description:wysiwyg prix:number image:image
    """
    click.echo(f"🚀 Génération du module '{name}'...")

    # Parser les champs
    parsed_fields = []
    for field_str in fields:
        try:
            parsed_fields.append(parse_field(field_str))
        except click.BadParameter as e:
            click.echo(f"❌ Erreur: {e}", err=True)
            raise SystemExit(1)

    click.echo(f"📋 {len(parsed_fields)} champ(s) détecté(s):")
    for field in parsed_fields:
        click.echo(f"   - {field.name} ({field.field_type})")

    # Générer le module
    output_path = Path(output).resolve()
    generator = WordPressModuleGenerator(output_path)

    try:
        module_dir = generator.generate(name, parsed_fields)
        click.echo(f"\n✅ Module généré avec succès!")
        click.echo(f"📁 Emplacement: {module_dir}")
        click.echo(f"\n📦 Fichiers générés:")
        for file in sorted(module_dir.rglob("*")):
            if file.is_file():
                rel_path = file.relative_to(module_dir)
                click.echo(f"   - {rel_path}")
    except Exception as e:
        click.echo(f"❌ Erreur lors de la génération: {e}", err=True)
        raise SystemExit(1)


@cli.command("list-types")
def list_types() -> None:
    """Affiche la liste des types de champs supportés."""
    click.echo("📋 Types de champs supportés:\n")
    for type_name, config in SUPPORTED_TYPES.items():
        click.echo(f"  {type_name:12} - {config['label']}")
    click.echo("\n💡 Utilisation: wp-gen module NomModule champ:type")


if __name__ == "__main__":
    cli()
