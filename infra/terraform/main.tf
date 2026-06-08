terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "environment" {
  default = "dev"
}

variable "location" {
  default = "East US"
}

variable "project_name" {
  default = "agentthat"
}

# ─── Resource Group ────────────────────────────────────────────────────────────

resource "azurerm_resource_group" "agentthat" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
}

# ─── PostgreSQL Flexible Server ────────────────────────────────────────────────

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.project_name}-pg-${var.environment}"
  resource_group_name    = azurerm_resource_group.agentthat.name
  location               = azurerm_resource_group.agentthat.location
  version                = "16"
  administrator_login    = "pgadmin"
  administrator_password = "CHANGE_ME_IN_KEYVAULT"
  sku_name               = "B_Standard_B1ms"
  storage_mb             = 32768
  zone                   = "1"

  high_availability {
    mode = "ZoneRedundant"
  }
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = var.project_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "utf8"
  collation = "en_US.utf8"
}

# ─── Redis Cache ───────────────────────────────────────────────────────────────

resource "azurerm_redis_cache" "main" {
  name                = "${var.project_name}-redis-${var.environment}"
  location            = azurerm_resource_group.agentthat.location
  resource_group_name = azurerm_resource_group.agentthat.name
  capacity            = 1
  family              = "C"
  sku_name            = "Standard"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {}
}

# ─── Azure Key Vault ───────────────────────────────────────────────────────────

resource "azurerm_key_vault" "main" {
  name                = "${var.project_name}-kv-${var.environment}"
  location            = azurerm_resource_group.agentthat.location
  resource_group_name = azurerm_resource_group.agentthat.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  soft_delete_retention_days = 90
  purge_protection_enabled   = true
}

data "azurerm_client_config" "current" {}

# ─── Container Registry ───────────────────────────────────────────────────────

resource "azurerm_container_registry" "main" {
  name                = "${var.project_name}cr${var.environment}"
  resource_group_name = azurerm_resource_group.agentthat.name
  location            = azurerm_resource_group.agentthat.location
  sku                 = "Basic"
  admin_enabled       = true
}

# ─── AKS Cluster ──────────────────────────────────────────────────────────────

resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.project_name}-aks-${var.environment}"
  location            = azurerm_resource_group.agentthat.location
  resource_group_name = azurerm_resource_group.agentthat.name
  dns_prefix          = "${var.project_name}-${var.environment}"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_B2s"
  }

  identity {
    type = "SystemAssigned"
  }
}

# ─── Outputs ──────────────────────────────────────────────────────────────────

output "resource_group_name" {
  value = azurerm_resource_group.agentthat.name
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.main.hostname
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}
