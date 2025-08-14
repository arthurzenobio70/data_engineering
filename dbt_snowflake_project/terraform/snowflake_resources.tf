# Resource Monitors
resource "snowflake_resource_monitor" "monitors" {
  for_each = { for monitor in var.resource_monitors : monitor.name => monitor }

  name         = each.value.name
  credit_quota = each.value.credit_quota
  frequency    = each.value.frequency
  
  start_timestamp = each.value.start_timestamp
  end_timestamp   = each.value.end_timestamp
  
  notify_triggers            = each.value.notify_triggers
  suspend_triggers           = each.value.suspend_triggers
  suspend_immediate_triggers = each.value.suspend_immediate_triggers

  set_for_account = false
}

# Warehouses
resource "snowflake_warehouse" "warehouses" {
  for_each = { for warehouse in var.warehouses : warehouse.name => warehouse }

  name                         = each.value.name
  comment                      = each.value.comment
  warehouse_size               = each.value.warehouse_size
  auto_suspend                 = each.value.auto_suspend
  auto_resume                  = each.value.auto_resume
  initially_suspended          = each.value.initially_suspended
  resource_monitor             = each.value.resource_monitor != null ? each.value.resource_monitor : try(snowflake_resource_monitor.monitors[keys(snowflake_resource_monitor.monitors)[0]].name, null)
  max_cluster_count            = each.value.max_cluster_count
  min_cluster_count            = each.value.min_cluster_count
  scaling_policy               = each.value.scaling_policy

  depends_on = [snowflake_resource_monitor.monitors]
}

# Databases
resource "snowflake_database" "databases" {
  for_each = { for db in var.databases : db.name => db }

  name    = each.value.name
  comment = each.value.comment
  
  data_retention_time_in_days = var.environment == "prod" ? 7 : 1
}

# Schemas
resource "snowflake_schema" "schemas" {
  for_each = { for schema in var.schemas : "${schema.database}.${schema.name}" => schema }

  database = snowflake_database.databases[each.value.database].name
  name     = each.value.name
  comment  = each.value.comment
  
  data_retention_time_in_days = var.environment == "prod" ? 7 : 1
  
  depends_on = [snowflake_database.databases]
}

# Roles
resource "snowflake_role" "roles" {
  for_each = { for role in var.roles : role.name => role }

  name    = each.value.name
  comment = each.value.comment
}

# Users
resource "snowflake_user" "users" {
  for_each = { for user in var.users : user.name => user }

  name              = each.value.name
  comment           = each.value.comment
  default_warehouse = snowflake_warehouse.warehouses[each.value.default_warehouse].name
  default_role      = snowflake_role.roles[each.value.default_role].name
  default_namespace = "${snowflake_database.databases[split(".", each.value.default_namespace)[0]].name}.${snowflake_schema.schemas[each.value.default_namespace].name}"
  
  email      = each.value.email
  first_name = each.value.first_name
  last_name  = each.value.last_name
  
  depends_on = [
    snowflake_warehouse.warehouses,
    snowflake_role.roles,
    snowflake_database.databases,
    snowflake_schema.schemas
  ]
}

# Role Grants - Database Level
resource "snowflake_database_grant" "dbt_database_grants" {
  for_each = toset(keys(snowflake_database.databases))
  
  database_name = snowflake_database.databases[each.key].name
  privilege     = "USAGE"
  roles         = [snowflake_role.roles["DBT_ROLE"].name]
  
  depends_on = [snowflake_database.databases, snowflake_role.roles]
}

resource "snowflake_database_grant" "analyst_database_grants" {
  for_each = toset(keys(snowflake_database.databases))
  
  database_name = snowflake_database.databases[each.key].name
  privilege     = "USAGE"
  roles         = [snowflake_role.roles["ANALYST_ROLE"].name]
  
  depends_on = [snowflake_database.databases, snowflake_role.roles]
}

# Role Grants - Schema Level
resource "snowflake_schema_grant" "dbt_schema_grants_usage" {
  for_each = { for schema in var.schemas : "${schema.database}.${schema.name}" => schema }
  
  database_name = snowflake_database.databases[each.value.database].name
  schema_name   = snowflake_schema.schemas[each.key].name
  privilege     = "USAGE"
  roles         = [snowflake_role.roles["DBT_ROLE"].name]
  
  depends_on = [snowflake_schema.schemas, snowflake_role.roles]
}

resource "snowflake_schema_grant" "dbt_schema_grants_create" {
  for_each = { for schema in var.schemas : "${schema.database}.${schema.name}" => schema }
  
  database_name = snowflake_database.databases[each.value.database].name
  schema_name   = snowflake_schema.schemas[each.key].name
  privilege     = "CREATE TABLE"
  roles         = [snowflake_role.roles["DBT_ROLE"].name]
  
  depends_on = [snowflake_schema.schemas, snowflake_role.roles]
}

resource "snowflake_schema_grant" "analyst_schema_grants" {
  for_each = { 
    for schema in var.schemas : "${schema.database}.${schema.name}" => schema 
    if schema.name == "MARTS"
  }
  
  database_name = snowflake_database.databases[each.value.database].name
  schema_name   = snowflake_schema.schemas[each.key].name
  privilege     = "USAGE"
  roles         = [snowflake_role.roles["ANALYST_ROLE"].name]
  
  depends_on = [snowflake_schema.schemas, snowflake_role.roles]
}

# Warehouse Grants
resource "snowflake_warehouse_grant" "dbt_warehouse_grants" {
  for_each = { for warehouse in var.warehouses : warehouse.name => warehouse }
  
  warehouse_name = snowflake_warehouse.warehouses[each.key].name
  privilege      = "USAGE"
  roles          = [snowflake_role.roles["DBT_ROLE"].name]
  
  depends_on = [snowflake_warehouse.warehouses, snowflake_role.roles]
}

resource "snowflake_warehouse_grant" "analyst_warehouse_grants" {
  for_each = { for warehouse in var.warehouses : warehouse.name => warehouse }
  
  warehouse_name = snowflake_warehouse.warehouses[each.key].name
  privilege      = "USAGE"
  roles          = [snowflake_role.roles["ANALYST_ROLE"].name]
  
  depends_on = [snowflake_warehouse.warehouses, snowflake_role.roles]
}

# Role Hierarchy
resource "snowflake_role_grants" "dbt_role_grants" {
  role_name = snowflake_role.roles["DBT_ROLE"].name
  users     = [snowflake_user.users["DBT_USER"].name]
  
  depends_on = [snowflake_role.roles, snowflake_user.users]
}

resource "snowflake_role_grants" "airflow_role_grants" {
  role_name = snowflake_role.roles["AIRFLOW_ROLE"].name
  users     = [snowflake_user.users["AIRFLOW_USER"].name]
  
  depends_on = [snowflake_role.roles, snowflake_user.users]
}

# File Formats for data loading
resource "snowflake_file_format" "csv_format" {
  name     = "CSV_FORMAT"
  database = snowflake_database.databases["FINANCE_DB"].name
  schema   = snowflake_schema.schemas["FINANCE_DB.RAW"].name
  
  format_type             = "CSV"
  field_delimiter         = ","
  record_delimiter        = "\n"
  skip_header             = 1
  field_optionally_enclosed_by = "\""
  null_if                 = ["NULL", "null", ""]
  error_on_column_count_mismatch = false
  
  depends_on = [snowflake_database.databases, snowflake_schema.schemas]
}

resource "snowflake_file_format" "json_format" {
  name     = "JSON_FORMAT"
  database = snowflake_database.databases["FINANCE_DB"].name
  schema   = snowflake_schema.schemas["FINANCE_DB.RAW"].name
  
  format_type = "JSON"
  strip_outer_array = true
  
  depends_on = [snowflake_database.databases, snowflake_schema.schemas]
}
