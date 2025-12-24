# WP-Gen - Générateur de Modules WordPress

CLI Python pour générer des modules WordPress complets avec Custom Post Types, champs ACF, templates et shortcodes.

## Installation

```bash
# Cloner le repo
git clone <repo-url>
cd G-n-rateur-wordpress

# Installer les dépendances
pip install -r requirements.txt

# Ou installer en mode développement
pip install -e .
```

## Utilisation

### Commande principale

```bash
wp-gen module NomModule champ1:type champ2:type ...
```

### Exemple

```bash
wp-gen module Produit titre:text description:wysiwyg prix:number image:image date_sortie:date
```

Génère un module WordPress complet dans `output/produit/` avec :
- Custom Post Type avec toutes les capacités
- Fichiers ACF JSON pour les champs
- Template `single-produit.php`
- Template `archive-produit.php`
- Shortcodes `[produit_list]` et `[produit_single id="123"]`
- README.md avec instructions d'installation

### Types de champs supportés

| Type | Description |
|------|-------------|
| `text` | Champ texte simple |
| `textarea` | Zone de texte multiligne |
| `image` | Sélecteur d'image |
| `number` | Champ numérique |
| `wysiwyg` | Éditeur WYSIWYG |
| `select` | Liste déroulante |
| `date` | Sélecteur de date |

### Options

```bash
wp-gen module --help

Options:
  -o, --output PATH  Répertoire de sortie (défaut: ./output)
```

### Lister les types disponibles

```bash
wp-gen list-types
```

## Structure générée

```
output/nom-module/
├── nom-module.php              # Plugin principal
├── README.md                   # Instructions d'installation
├── acf-json/
│   └── group_*.json            # Définition des champs ACF
├── includes/
│   ├── cpt-nom-module.php      # Custom Post Type
│   └── shortcode-nom-module.php # Shortcodes
└── templates/
    ├── single-nom-module.php   # Template single
    └── archive-nom-module.php  # Template archive
```

## Prérequis

- Python 3.10+
- WordPress 5.8+
- [Advanced Custom Fields](https://www.advancedcustomfields.com/) (gratuit ou PRO)

## Licence

MIT
