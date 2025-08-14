output "account_locator" {
  description = "Snowflake account locator"
  value       = data.snowflake_current_account.this.account_locator
}

output "account_url" {
  description = "Snowflake account URL"
  value       = data.snowflake_current_account.this.url
}

output "warehouses" {
  description = "Created warehouses"
  value = {
    for k, v in snowflake_warehouse.warehouses : k => {
      name = v.name
      size = v.warehouse_size
    }
  }
}

output "databases" {
  description = "Created databases"
  value = {
    for k, v in snowflake_database.databases : k => {
      name = v.name
    }
  }
}

output "schemas" {
  description = "Created schemas"
  value = {
    for k, v in snowflake_schema.schemas : k => {
      database = v.database
      name     = v.name
    }
  }
}

output "roles" {
  description = "Created roles"
  value = {
    for k, v in snowflake_role.roles : k => {
      name = v.name
    }
  }
}

output "users" {
  description = "Created users"
  value = {
    for k, v in snowflake_user.users : k => {
      name              = v.name
      default_warehouse = v.default_warehouse
      default_role      = v.default_role
    }
  }
  sensitive = true
}

output "resource_monitors" {
  description = "Created resource monitors"
  value = {
    for k, v in snowflake_resource_monitor.monitors : k => {
      name         = v.name
      credit_quota = v.credit_quota
    }
  }
}

output "file_formats" {
  description = "Created file formats"
  value = {
    csv_format = {
      name     = snowflake_file_format.csv_format.name
      database = snowflake_file_format.csv_format.database
      schema   = snowflake_file_format.csv_format.schema
    }
    json_format = {
      name     = snowflake_file_format.json_format.name
      database = snowflake_file_format.json_format.database
      schema   = snowflake_file_format.json_format.schema
    }
  }
}
