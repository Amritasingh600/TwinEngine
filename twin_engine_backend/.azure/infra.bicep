// ==============================================================
// TwinEngine Backend — Azure Bicep Infrastructure-as-Code
// Deploys: App Service Plan + Web App + PostgreSQL + Redis + Container Registry
// ==============================================================
// Usage:
//   az deployment group create \
//     --resource-group twinengine-rg \
//     --template-file infra.bicep \
//     --parameters appName=twinengine dbPassword=<STRONG_PASSWORD>
// ==============================================================

@description('Base name for all resources')
param appName string = 'twinengine'

@description('Azure region')
param location string = resourceGroup().location

@description('App Service Plan SKU')
@allowed(['B1', 'B2', 'S1', 'S2', 'P1v3', 'P2v3'])
param appServiceSku string = 'B1'

@description('PostgreSQL admin password')
@secure()
param dbPassword string

@description('PostgreSQL SKU')
param dbSku string = 'Standard_B1ms'

@description('Docker image tag')
param imageTag string = 'latest'

// ── Variables ────────────────────────────────────────────────
var uniqueSuffix = uniqueString(resourceGroup().id)
var webAppName = '${appName}-api-${uniqueSuffix}'
var planName = '${appName}-plan'
var dbServerName = '${appName}-db-${uniqueSuffix}'
var redisName = '${appName}-cache-${uniqueSuffix}'
var registryName = '${appName}acr${uniqueSuffix}'
var dbName = 'twinengine'
var dbUser = 'twinengineadmin'

// ── Container Registry ──────────────────────────────────────
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// ── App Service Plan (Linux) ────────────────────────────────
resource plan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: planName
  location: location
  kind: 'linux'
  properties: {
    reserved: true
  }
  sku: {
    name: appServiceSku
  }
}

// ── Web App (Container) ─────────────────────────────────────
resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${acr.properties.loginServer}/${appName}:${imageTag}'
      alwaysOn: appServiceSku != 'B1'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      webSocketsEnabled: true
      healthCheckPath: '/api/health/'
      appSettings: [
        { name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE', value: 'false' }
        { name: 'DOCKER_REGISTRY_SERVER_URL', value: 'https://${acr.properties.loginServer}' }
        { name: 'DOCKER_REGISTRY_SERVER_USERNAME', value: acr.listCredentials().username }
        { name: 'DOCKER_REGISTRY_SERVER_PASSWORD', value: acr.listCredentials().passwords[0].value }
        { name: 'WEBSITES_PORT', value: '8000' }
        { name: 'DEBUG', value: 'False' }
        { name: 'ALLOWED_HOSTS', value: '${webAppName}.azurewebsites.net' }
        { name: 'DATABASE_URL', value: 'postgresql://${dbUser}:${dbPassword}@${dbServer.properties.fullyQualifiedDomainName}:5432/${dbName}?sslmode=require' }
        { name: 'REDIS_URL', value: 'rediss://:${redis.listKeys().primaryKey}@${redis.properties.hostName}:${redis.properties.sslPort}/0' }
        { name: 'DJANGO_SETTINGS_MODULE', value: 'twinengine_core.settings' }
        { name: 'CSRF_TRUSTED_ORIGINS', value: 'https://${webAppName}.azurewebsites.net' }
        { name: 'CORS_ALLOWED_ORIGINS', value: 'https://${webAppName}.azurewebsites.net' }
      ]
    }
  }
}

// ── PostgreSQL Flexible Server ──────────────────────────────
resource dbServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: dbServerName
  location: location
  sku: {
    name: dbSku
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: dbUser
    administratorLoginPassword: dbPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

// PostgreSQL Database
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: dbServer
  name: dbName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// PostgreSQL Firewall — allow Azure services
resource dbFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: dbServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ── Redis Cache ─────────────────────────────────────────────
resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: redisName
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

// ── Outputs ─────────────────────────────────────────────────
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output webAppName string = webApp.name
output acrLoginServer string = acr.properties.loginServer
output acrName string = acr.name
output dbHost string = dbServer.properties.fullyQualifiedDomainName
output redisHost string = redis.properties.hostName
