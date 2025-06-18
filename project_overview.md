# Project Overview: Little Money

## Introduction

The "little_money" project is a Django-based web application consisting of multiple apps that handle different aspects of the system. This document provides an overview of the project structure, the apps included, and the key files within each app.

---

## Apps and Their Files

### 1. api

This app handles the API endpoints and related logic for the project.

- `__init__.py`: Python package marker.
- `admin.py`: Admin interface configurations for the API models.
- `apps.py`: App configuration for the API app.
- `models.py`: Database models related to the API.
- `tests.py`: Test cases for the API app.
- `views.py`: Views and API endpoint handlers.
  - `TransactionSerializer` (class): Serializes the Transaction model for API responses.
  - `initiate_transaction` (function): API endpoint to initiate a payment transaction, calculates fees, creates a transaction record, and interacts with payment aggregator.
  - `TransactionHistoryView` (class): API view to list transaction history for the authenticated user.
- `migrations/`: Database migration files.

---

### 2. core

This app contains core business logic and shared components.

- `__init__.py`: Python package marker.
- `admin.py`: Admin interface configurations for core models.
- `apps.py`: App configuration for the core app.
- `models.py`: Core database models.
- `tests.py`: Test cases for the core app.
- `views.py`: Views related to core functionality (currently empty).
- `migrations/`: Database migration files.

---

### 3. dashboard

This app manages the administrative dashboard and user interface.

- `__init__.py`: Python package marker.
- `admin.py`: Admin interface configurations for dashboard models.
- `apps.py`: App configuration for the dashboard app.
- `models.py`: Database models for dashboard.
- `tests.py`: Test cases for the dashboard app.
- `views.py`: Views for dashboard pages.
  - `admin_dashboard` (function): Displays all transactions and total platform earnings for admin users.
  - `platform_settings` (function): Allows admin users to view and update platform fee settings.
  - `export_transactions_csv` (function): Exports all transactions as a CSV file for admin users.
  - `staff_dashboard` (function): Displays transactions for the logged-in staff user.
  - `staff_users` (function): Allows admin to manage staff user accounts.
  - `user_login` (function): Handles user login authentication.
  - `user_logout` (function): Logs out the user and redirects to login page.
- `migrations/`: Database migration files.
- `templates/dashboard/`: HTML templates for dashboard pages.

---

### 4. payment

This app handles payment processing and related services.

- `__init__.py`: Python package marker.
- `admin.py`: Admin interface configurations for payment models.
- `apps.py`: App configuration for the payment app.
- `models.py`: Database models related to payments.
  - `PlatformSettings` (class): Stores platform fee percentage and update timestamp.
  - `Transaction` (class): Represents a payment transaction with user, amounts, status, and timestamps.
- `services.py`: Payment service logic.
- `tests.py`: Test cases for the payment app.
- `views.py`: Views related to payment processing.
- `migrations/`: Database migration files.

---

### 5. webhooks

This app manages webhook endpoints and processing.

- `__init__.py`: Python package marker.
- `admin.py`: Admin interface configurations for webhook models.
- `apps.py`: App configuration for the webhooks app.
- `models.py`: Database models for webhooks.
- `tests.py`: Test cases for the webhooks app.
- `views.py`: Views handling webhook requests.
- `migrations/`: Database migration files.

---

## Additional Project Structure

- `little_money/little_money/`: Main project folder containing settings, URLs, WSGI, and ASGI configurations.
- `staticfiles/`: Static assets used by the project.
- `db.sqlite3`: SQLite database file.
- `manage.py`: Django management script.

---

This overview provides a high-level understanding of the project structure and the roles of each app and their key files.
