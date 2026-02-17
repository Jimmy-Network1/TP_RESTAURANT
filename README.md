# 🍽️ Restaurant Web - Système de Gestion de Restaurant

Application Django complète pour la gestion d'un restaurant : commandes, cuisine, stock, réservations, rapports, rôles et authentification.

## 📋 Structure du projet

```
TP_RESTAURANT/
├── accounts/           # Authentification et rôles
├── menu/              # Carte et plats
├── sales/             # Commandes, tables, paiements
├── kitchen/           # Gestion cuisine
├── inventory/         # Stock et fournisseurs
├── reports/           # Rapports et statistiques
├── reservations/      # Réservations de tables
├── templates/         # Templates globaux
├── static/           # CSS, JS, images
├── media/            # Fichiers uploadés
└── restaurant_web/   # Configuration Django
```

## 🚀 Installation

### 1. Activer l'environnement virtuel
```bash
source venv/bin/activate
```

### 2. Créer la base de données PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE restaurant_db;
\q
```

### 3. Appliquer les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Créer un superuser
```bash
python manage.py createsuperuser
```

### 5. Lancer le serveur
```bash
python manage.py runserver
```

Accéder à : http://localhost:8000

## ✅ État actuel (V1)

- CRUD Menu (catégories, plats, variantes)
- CRUD Sales (tables, commandes, paiements)
- CRUD Inventory (ingrédients, fournisseurs, mouvements, bons de commande)
- CRUD Kitchen (postes, tickets, recettes)
- CRUD Reservations (réservations)
- Dashboard Reports (CA du jour, commandes, top plats)
- Authentification + profils rôles (admin/chef/serveur/caissier/livreur)

## 📊 Fonctionnalités

- **7 modules intégrés** : Accounts, Menu, Sales, Kitchen, Inventory, Reports, Reservations
- **Multi-rôles** : Admin, Chef, Serveur, Caissier, Livreur
- **PostgreSQL** : Base de données robuste
- **FCFA** : Devise locale
- **Français** : Interface en français

## 📦 Technologies

- Django 5.1.15
- PostgreSQL
- Python 3.11+
- Pillow (gestion images)

## 📝 Configuration

Les variables d'environnement sont dans `.env`:
- SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

Voir `.env.example` pour un template.

## ▶️ Démarrage rapide

```bash
source venv/bin/activate
./venv/bin/python manage.py migrate
./venv/bin/python manage.py createsuperuser
./venv/bin/python manage.py runserver
```

Accéder à : http://127.0.0.1:8000  
Admin : http://127.0.0.1:8000/admin
