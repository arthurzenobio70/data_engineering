# Contributing to Finance Data Platform

Thank you for your interest in contributing to the Finance Data Platform! This document provides guidelines and best practices for contributing to this project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Requirements](#documentation-requirements)
- [Submitting Changes](#submitting-changes)

## 🤝 Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:

- Be respectful and constructive in discussions
- Focus on what is best for the community
- Show empathy towards other community members
- Accept constructive criticism gracefully

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Git
- Snowflake account access
- Basic understanding of dbt and SQL

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/finance-data-platform.git
   cd finance-data-platform
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   dbt deps
   ```

4. **Set Up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## 🔄 Development Process

### Branching Strategy

We use Git Flow with the following branch types:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features or enhancements
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical production fixes

### Workflow

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow code standards
   - Add appropriate tests
   - Update documentation

3. **Test Locally**
   ```bash
   dbt run --select state:modified+
   dbt test --select state:modified+
   pre-commit run --all-files
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: descriptive commit message"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Code Standards

### SQL Style Guidelines

We use SQLFluff for SQL formatting. Key rules:

- **Keywords**: UPPERCASE (`SELECT`, `FROM`, `WHERE`)
- **Identifiers**: lowercase (`customer_id`, `order_date`)
- **Indentation**: 4 spaces
- **Line Length**: Maximum 120 characters
- **Commas**: Trailing commas preferred

**Example:**
```sql
SELECT
    customer_id,
    customer_name,
    customer_email,
    created_at
FROM {{ source('raw_data', 'customers') }}
WHERE customer_id IS NOT NULL
```

### dbt Model Standards

#### Naming Conventions

| Layer | Prefix | Example |
|-------|--------|---------|
| Staging | `stg_` | `stg_customers` |
| Intermediate | `int_` | `int_customer_orders` |
| Facts | `fct_` | `fct_order_items` |
| Dimensions | `dim_` | `dim_customers` |

#### File Organization

```
models/
├── staging/
│   ├── _stg__sources.yml
│   ├── stg_customers.sql
│   └── stg_orders.sql
├── intermediate/
│   ├── _int__models.yml
│   └── int_order_enriched.sql
└── marts/
    ├── core/
    │   ├── _core__models.yml
    │   ├── dim_customers.sql
    │   └── fct_orders.sql
    └── finance/
        ├── _finance__models.yml
        └── fct_daily_revenue.sql
```

#### Model Configuration

All models must include:

```sql
{{
  config(
    materialized='table',  # or 'view', 'incremental'
    docs={'node_color': 'lightblue'},
    meta={
      'owner': 'data-engineering-team',
      'layer': 'staging'
    }
  )
}}
```

#### SQL Structure

Use the following CTE pattern:

```sql
with source_data as (
    select * from {{ source('raw_data', 'table_name') }}
),

renamed as (
    select
        -- Primary keys
        id as primary_key,
        
        -- Foreign keys
        customer_id,
        
        -- Attributes
        column_name,
        
        -- Metadata
        current_timestamp as dbt_loaded_at
        
    from source_data
),

final as (
    select
        -- All transformations here
        primary_key,
        customer_id,
        transformed_column
        
    from renamed
)

select * from final
```

## 🧪 Testing Guidelines

### Required Tests

Every model must have:

1. **Primary Key Tests**
   ```yaml
   - name: primary_key_column
     tests:
       - unique
       - not_null
   ```

2. **Foreign Key Tests**
   ```yaml
   - name: foreign_key_column
     tests:
       - relationships:
           to: ref('parent_model')
           field: primary_key
   ```

3. **Business Logic Tests**
   - Custom tests for domain-specific rules
   - Data quality expectations
   - Cross-model consistency checks

### Test Categories

Use tags to categorize tests:

```yaml
tests:
  - name: test_name
    config:
      tags: ['data_quality', 'critical']
```

Available tags:
- `critical` - Must pass for deployment
- `data_quality` - Data quality checks
- `data_integrity` - Referential integrity
- `business_logic` - Domain rules

## 📚 Documentation Requirements

### Model Documentation

All models require:

```yaml
models:
  - name: model_name
    description: "Clear description of model purpose"
    columns:
      - name: column_name
        description: "What this column represents"
        tests:
          - not_null
```

### Code Comments

- **Complex Logic**: Explain business rules
- **Performance**: Document optimization choices
- **Assumptions**: State data assumptions

Example:
```sql
-- Calculate customer lifetime value using completed orders only
-- Assumes order_status = 'COMPLETED' indicates successful transaction
sum(case when order_status = 'COMPLETED' then order_amount else 0 end) as lifetime_value
```

## 📤 Submitting Changes

### Pull Request Checklist

Before submitting:

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages are descriptive
- [ ] PR description explains changes
- [ ] Screenshots for UI changes (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Local tests pass
- [ ] CI pipeline passes
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. **Automated Checks**: CI pipeline must pass
2. **Code Review**: At least one team member approval
3. **Testing**: Verify in staging environment
4. **Merge**: Squash and merge to develop

## 🏷️ Commit Message Guidelines

Use conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Maintenance tasks

### Examples

```
feat(staging): add customer segmentation model
fix(marts): correct revenue calculation logic
docs(readme): update setup instructions
test(staging): add data quality tests for orders
```

## 🐛 Reporting Issues

### Bug Reports

Include:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Screenshots/logs if relevant

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

## 🤔 Questions?

- **Slack**: `#data-engineering` channel
- **Email**: data-engineering@company.com
- **Issues**: GitHub Issues for bugs/features
- **Discussions**: GitHub Discussions for questions

Thank you for contributing! 🎉
