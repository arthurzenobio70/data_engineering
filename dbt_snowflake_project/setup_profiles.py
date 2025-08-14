#!/usr/bin/env python3
"""
Setup script for dbt profiles.yml with data lineage support
This script creates a properly configured profiles.yml file for the Finance Data Platform
"""

import os
import sys
from pathlib import Path

def get_user_input():
    """Get Snowflake credentials from user"""
    print("🔧 Setting up dbt profiles.yml for Finance Data Platform")
    print("This will enable data lineage visualization and advanced features\n")
    
    # Get Snowflake account
    account = input("Enter your Snowflake account (e.g., abc123): ").strip()
    if not account.endswith('.snowflakecomputing.com'):
        account = f"{account}.snowflakecomputing.com"
    
    # Get credentials
    username = input("Enter your Snowflake username: ").strip()
    password = input("Enter your Snowflake password: ").strip()
    role = input("Enter your Snowflake role [ACCOUNTADMIN]: ").strip() or "ACCOUNTADMIN"
    warehouse = input("Enter your warehouse name [COMPUTE_WH]: ").strip() or "COMPUTE_WH"
    
    return {
        'account': account,
        'username': username,
        'password': password,
        'role': role,
        'warehouse': warehouse
    }

def create_profiles_content(credentials):
    """Create the profiles.yml content with lineage support"""
    return f"""# dbt profiles.yml for Finance Data Platform
# Auto-generated with data lineage support enabled

finance_data_platform:
  outputs:
    
    # Development environment
    dev:
      type: snowflake
      account: {credentials['account']}
      user: {credentials['username']}
      password: {credentials['password']}
      role: {credentials['role']}
      database: FINANCE_DB_DEV
      warehouse: {credentials['warehouse']}
      schema: raw
      threads: 4
      
      # Enable data lineage and monitoring
      client_session_keep_alive: False
      query_tag: "dbt-{{{{ invocation_id }}}}-{{{{ model.unique_id }}}}"
      retry_on_database_errors: True
      retry_all: True
      
    # Staging environment (after Terraform setup)
    staging:
      type: snowflake
      account: {credentials['account']}
      user: {credentials['username']}
      password: {credentials['password']}
      role: {credentials['role']}
      database: FINANCE_DB_STAGING
      warehouse: FINANCE_WH_STAGING
      schema: raw
      threads: 8
      client_session_keep_alive: False
      query_tag: "dbt-staging-{{{{ invocation_id }}}}-{{{{ model.unique_id }}}}"
      retry_on_database_errors: True
      retry_all: True
      
  # Default to development
  target: dev

# Data Lineage Features Enabled:
# 1. Model-to-model lineage visualization
# 2. Column-level lineage tracking  
# 3. Source-to-model relationships
# 4. Query performance tracking
# 5. Cost monitoring via query tags
#
# To view lineage:
# 1. Run: dbt docs generate
# 2. Run: dbt docs serve
# 3. Open: http://localhost:8080
# 4. Click on any model to see the lineage graph
"""

def setup_profiles():
    """Main setup function"""
    try:
        # Determine profiles directory
        home_dir = Path.home()
        dbt_dir = home_dir / '.dbt'
        profiles_file = dbt_dir / 'profiles.yml'
        
        print(f"📁 Profiles will be created at: {profiles_file}")
        
        # Create .dbt directory if it doesn't exist
        dbt_dir.mkdir(exist_ok=True)
        print(f"✅ Created directory: {dbt_dir}")
        
        # Check if profiles.yml already exists
        if profiles_file.exists():
            overwrite = input(f"\n⚠️  profiles.yml already exists at {profiles_file}\nOverwrite? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("❌ Setup cancelled")
                return False
        
        # Get user credentials
        credentials = get_user_input()
        
        # Create profiles content
        content = create_profiles_content(credentials)
        
        # Write profiles.yml
        with open(profiles_file, 'w') as f:
            f.write(content)
        
        print(f"\n✅ Successfully created {profiles_file}")
        print("\n🎯 Next steps:")
        print("1. Test connection: dbt debug")
        print("2. Run models: dbt run") 
        print("3. Generate docs: dbt docs generate")
        print("4. View lineage: dbt docs serve")
        print("5. Open browser: http://localhost:8080")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up profiles: {e}")
        return False

if __name__ == "__main__":
    success = setup_profiles()
    sys.exit(0 if success else 1)
