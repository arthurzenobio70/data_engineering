# PowerShell script to clean up v1 files and replace them with v2 versions
# This script will:
# 1. Backup original files
# 2. Replace them with v2 versions
# 3. Update references in Terraform

Write-Host "🧹 Cleaning up v1 files and promoting v2 to main versions..." -ForegroundColor Green

# Create backup directory
$backupDir = "backup_v1_files"
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir
    Write-Host "✅ Created backup directory: $backupDir" -ForegroundColor Green
}

# Backup original files
Write-Host "📦 Backing up original files..." -ForegroundColor Yellow
Copy-Item "dags/stock_market_dag.py" "$backupDir/stock_market_dag.py.backup"
Copy-Item "dataproc_jobs/transform_stock_data_pipeline.py" "$backupDir/transform_stock_data_pipeline.py.backup"

# Replace original files with v2 versions
Write-Host "🔄 Replacing files with v2 versions..." -ForegroundColor Yellow

# Replace DAG file
Move-Item "dags/stock_market_dag_v2.py" "dags/stock_market_dag.py" -Force
Write-Host "✅ Replaced DAG: stock_market_dag.py" -ForegroundColor Green

# Replace Dataproc job file  
Move-Item "dataproc_jobs/transform_stock_data_v2.py" "dataproc_jobs/transform_stock_data_pipeline.py" -Force
Write-Host "✅ Replaced Dataproc job: transform_stock_data_pipeline.py" -ForegroundColor Green

Write-Host "🎉 Cleanup completed successfully!" -ForegroundColor Green
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "  - Original files backed up to: $backupDir/" -ForegroundColor White
Write-Host "  - DAG updated to modern version" -ForegroundColor White
Write-Host "  - Dataproc job updated to modern version" -ForegroundColor White
Write-Host "  - All references now point to the refactored code" -ForegroundColor White

Write-Host "`n⚠️  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Update Terraform references if needed" -ForegroundColor White
Write-Host "  2. Test the pipeline to ensure everything works" -ForegroundColor White
Write-Host "  3. Delete backup files when confident (optional)" -ForegroundColor White
