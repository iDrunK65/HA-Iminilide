# i-MINILide for Home Assistant

Integration Home Assistant pour les controleurs i-MINILide.

Ce depot contient une `custom integration`, pas un add-on Supervisor.

## Fonctionnalites

- configuration depuis l'UI Home Assistant avec IP ou hostname du controleur
- decouverte automatique du controleur via `GET /index?configuration_iminilide`
- decouverte automatique des voies via `GET /index?configuration_voie`
- lecture du detail de chaque voie via `GET /index?configuration_voieN`
- creation d'un appareil parent pour le controleur
- creation d'un sous-appareil par voie
- rafraichissement des mesures toutes les 30 secondes via `POST /` avec `action=refresh`
- creation des entites suivantes par voie:
  - `Mesure`
  - `Surveillance`
  - `Alarme` si la surveillance est active et qu'au moins un seuil est configure
  - `Seuil alarme haut` en diagnostic si configure
  - `Seuil alarme bas` en diagnostic si configure

## Compatibilite

- Home Assistant recent avec support des `custom_components`
- installation via HACS custom repository ou installation manuelle

## Installation via HACS

Cette integration peut etre ajoutee comme depot personnalise dans HACS.

1. Publier ce depot sur GitHub si ce n'est pas deja fait.
2. Dans Home Assistant, ouvrir `HACS`.
3. Aller dans `Integrations`.
4. Ouvrir le menu en haut a droite puis `Custom repositories`.
5. Ajouter l'URL du depot GitHub.
6. Choisir le type `Integration`.
7. Valider puis rechercher `i-MINILide` dans HACS.
8. Installer l'integration.
9. Redemarrer Home Assistant.

## Installation manuelle

1. Copier le dossier `custom_components/iminilide` dans le dossier `config/custom_components/` de Home Assistant.
2. Redemarrer Home Assistant.

Arborescence attendue:

```text
config/
  custom_components/
    iminilide/
      __init__.py
      manifest.json
      ...
```

## Ajout dans Home Assistant

1. Aller dans `Parametres` > `Appareils et services`.
2. Cliquer sur `Ajouter une integration`.
3. Rechercher `i-MINILide`.
4. Saisir l'IP ou le hostname du controleur.
5. Valider.

L'integration cree:

- 1 appareil controleur i-MINILide
- 1 sous-appareil par voie detectee

## Entites creees

Pour chaque voie, l'integration expose au minimum:

- un capteur `Mesure`
- un binaire `Surveillance` en diagnostic

Selon la configuration de la voie, elle expose aussi:

- un binaire `Alarme`
- un capteur diagnostic `Seuil alarme haut`
- un capteur diagnostic `Seuil alarme bas`

## Sources utilisees

- `GET /index?configuration_iminilide` pour le nom, le numero de serie et les versions
- `GET /index?configuration_voie` pour la liste des voies
- `GET /index?configuration_voieN` pour la configuration detaillee de chaque voie
- `POST /` avec `action=refresh` pour les valeurs instantanees

## Important

- ce projet n'est pas un add-on Supervisor
- pour HACS, le type du depot doit etre `Integration`
- si la configuration des voies change sur le controleur, il faut recharger l'integration depuis Home Assistant pour relire la configuration statique

## Developpement

Tests disponibles localement:

```bash
python3 -m compileall custom_components tests
python3 -m unittest tests/test_parser.py
```

## Structure du depot

```text
custom_components/iminilide/
tests/
README.md
```
