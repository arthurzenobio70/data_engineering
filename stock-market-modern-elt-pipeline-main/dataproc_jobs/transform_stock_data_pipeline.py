"""
Stock Market Data Transformation Pipeline
==========================================

This script processes raw data from Yahoo Finance and ERP files,
transforming them into a dimensional model for analysis.
"""

import argparse
import logging
import sys
from typing import Optional

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, to_date, count, when, isnan, isnull
from pyspark.sql.types import StructType, StructField, StringType, FloatType, LongType, DateType


def setup_logging() -> logging.Logger:
    """Configure the logging system."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def create_spark_session(app_name: str) -> SparkSession:
    """
    Create an optimized Spark session with appropriate configurations.
    
    Args:
        app_name: Spark application name
        
    Returns:
        Configured SparkSession
    """
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.parquet.compression.codec", "snappy") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .getOrCreate()


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate input arguments.
    
    Args:
        args: Parsed arguments
        
    Raises:
        ValueError: If invalid arguments
    """
    if not args.bucket:
        raise ValueError("Bucket name is required")
    if not args.previous_day:
        raise ValueError("Previous day is required")


def validate_dataframe(df: DataFrame, df_name: str, logger: logging.Logger) -> bool:
    """
    Valida se o DataFrame não está vazio e registra estatísticas básicas.
    
    Args:
        df: DataFrame para validar
        df_name: Nome do DataFrame para logging
        logger: Logger para registrar mensagens
        
    Returns:
        True se válido, False caso contrário
    """
    count_rows = df.count()
    
    if count_rows == 0:
        logger.error(f"DataFrame {df_name} está vazio")
        return False
    
    logger.info(f"DataFrame {df_name}: {count_rows} linhas carregadas")
    return True


def check_data_quality(df: DataFrame, df_name: str, logger: logging.Logger) -> None:
    """
    Verifica a qualidade dos dados e registra estatísticas.
    
    Args:
        df: DataFrame para verificar
        df_name: Nome do DataFrame
        logger: Logger para mensagens
    """
    total_rows = df.count()
    
    # Verificar valores nulos em todas as colunas
    null_counts = df.select([
        count(when(isnan(c) | isnull(c), c)).alias(c) 
        for c in df.columns
    ]).collect()[0]
    
    logger.info(f"Qualidade de dados para {df_name}:")
    logger.info(f"  Total de linhas: {total_rows}")
    
    for col_name, null_count in null_counts.asDict().items():
        if null_count > 0:
            percentage = (null_count / total_rows) * 100
            logger.warning(f"  Coluna '{col_name}': {null_count} valores nulos ({percentage:.2f}%)")


def read_json_data(spark: SparkSession, input_path: str, logger: logging.Logger) -> Optional[DataFrame]:
    """
    Lê dados JSON do Yahoo Finance com tratamento de erro.
    
    Args:
        spark: Sessão Spark
        input_path: Caminho dos arquivos JSON
        logger: Logger para mensagens
        
    Returns:
        DataFrame ou None se erro
    """
    try:
        logger.info(f"Lendo dados JSON de: {input_path}")
        df = spark.read.option("multiline", "true").json(input_path)
        
        if not validate_dataframe(df, "API Yahoo Finance", logger):
            return None
            
        return df
        
    except Exception as e:
        logger.error(f"Erro ao ler dados JSON: {str(e)}")
        return None


def read_csv_data(spark: SparkSession, input_path: str, logger: logging.Logger) -> Optional[DataFrame]:
    """
    Lê dados CSV do ERP com tratamento de erro.
    
    Args:
        spark: Sessão Spark
        input_path: Caminho do arquivo CSV
        logger: Logger para mensagens
        
    Returns:
        DataFrame ou None se erro
    """
    try:
        logger.info(f"Lendo dados CSV de: {input_path}")
        df = spark.read.option("header", "true").option("inferSchema", "true").csv(input_path)
        
        if not validate_dataframe(df, "ERP", logger):
            return None
            
        return df
        
    except Exception as e:
        logger.error(f"Erro ao ler dados CSV: {str(e)}")
        return None


def transform_stock_data(df_api: DataFrame, logger: logging.Logger) -> DataFrame:
    """
    Transforma dados de ações do Yahoo Finance.
    
    Args:
        df_api: DataFrame com dados da API
        logger: Logger para mensagens
        
    Returns:
        DataFrame transformado
    """
    logger.info("Iniciando transformação dos dados de ações")
    
    # Extrair dados do formato Yahoo Finance
    df_stock_price = df_api.selectExpr(
        "ticker as Ticker",
        "open as Open",
        "high as High",
        "low as Low",
        "close as Close",
        "volume as Volume",
        "date as DateKey"
    )
    
    # Converter string DateKey para formato de data
    df_stock_price = df_stock_price.withColumn(
        "DateKey", 
        to_date(col("DateKey"), "yyyy-MM-dd")
    )
    
    # Garantir tipos de dados e ordenar colunas
    df_stock_price = df_stock_price.select(
        col("DateKey").cast(DateType()),
        col("Ticker").cast(StringType()),
        col("Open").cast(FloatType()),
        col("High").cast(FloatType()),
        col("Low").cast(FloatType()),
        col("Close").cast(FloatType()),
        col("Volume").cast(LongType())
    )
    
    # Filtrar registros com valores obrigatórios
    df_stock_price = df_stock_price.filter(
        col("DateKey").isNotNull() & 
        col("Ticker").isNotNull() &
        col("Open").isNotNull() &
        col("Close").isNotNull()
    )
    
    # Remover duplicatas
    df_stock_price = df_stock_price.dropDuplicates(["DateKey", "Ticker"])
    
    # Cache para performance (será usado no write)
    df_stock_price.cache()
    
    logger.info(f"Transformação concluída: {df_stock_price.count()} registros processados")
    return df_stock_price


def create_company_dimension(df_erp: DataFrame, logger: logging.Logger) -> DataFrame:
    """
    Cria dimensão de empresas.
    
    Args:
        df_erp: DataFrame ERP
        logger: Logger para mensagens
        
    Returns:
        DataFrame da dimensão
    """
    logger.info("Criando dimensão de empresas")
    
    df_dim_company = df_erp.selectExpr(
        "Symbol as Symbol",
        "CompanyName as CompanyName"
    ).filter(
        col("Symbol").isNotNull() & 
        col("CompanyName").isNotNull()
    ).distinct()
    
    logger.info(f"Dimensão empresa criada: {df_dim_company.count()} registros")
    return df_dim_company


def create_exchange_dimension(df_erp: DataFrame, logger: logging.Logger) -> DataFrame:
    """
    Cria dimensão de bolsas.
    
    Args:
        df_erp: DataFrame ERP
        logger: Logger para mensagens
        
    Returns:
        DataFrame da dimensão
    """
    logger.info("Criando dimensão de bolsas")
    
    df_dim_exchange = df_erp.selectExpr(
        "Exchange as ExchangeCode",
        "ExchangeName as ExchangeName"
    ).filter(
        col("Exchange").isNotNull() & 
        col("ExchangeName").isNotNull()
    ).distinct()
    
    logger.info(f"Dimensão bolsa criada: {df_dim_exchange.count()} registros")
    return df_dim_exchange


def write_parquet_data(df: DataFrame, output_path: str, df_name: str, logger: logging.Logger) -> bool:
    """
    Escreve DataFrame em formato Parquet com tratamento de erro.
    
    Args:
        df: DataFrame para escrever
        output_path: Caminho de saída
        df_name: Nome do DataFrame para logging
        logger: Logger para mensagens
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        logger.info(f"Escrevendo {df_name} em: {output_path}")
        
        df.write \
          .mode("overwrite") \
          .option("compression", "snappy") \
          .parquet(output_path)
          
        logger.info(f"{df_name} escrito com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao escrever {df_name}: {str(e)}")
        return False


def main():
    """Função principal do pipeline."""
    # Configurar logging
    logger = setup_logging()
    logger.info("Iniciando pipeline de transformação de dados")
    
    # Analisar argumentos
    parser = argparse.ArgumentParser(description="Pipeline de transformação de dados do mercado de ações")
    parser.add_argument("--bucket", required=True, help="Nome do bucket GCS")
    parser.add_argument("--previous_day", required=True, help="Data anterior no formato YYYY-MM-DD")
    args = parser.parse_args()
    
    try:
        # Validar argumentos
        validate_arguments(args)
        
        # Definir caminhos
        input_api_path = f"gs://{args.bucket}/raw/yahoo/*_{args.previous_day}.json"
        input_erp_path = f"gs://{args.bucket}/raw/ERP/erp_companies.csv"
        output_fact_path = f"gs://{args.bucket}/processed/fact_stock_price.parquet"
        output_dim_company_path = f"gs://{args.bucket}/processed/dim_company.parquet"
        output_dim_exchange_path = f"gs://{args.bucket}/processed/dim_exchange.parquet"
        
        # Criar sessão Spark
        spark = create_spark_session('transform-stock-market-data-pipeline')
        logger.info("Sessão Spark criada com sucesso")
        
        # Ler dados
        df_api = read_json_data(spark, input_api_path, logger)
        df_erp = read_csv_data(spark, input_erp_path, logger)
        
        if df_api is None or df_erp is None:
            logger.error("Falha ao carregar dados de entrada")
            sys.exit(1)
        
        # Verificar qualidade dos dados
        check_data_quality(df_api, "Yahoo Finance API", logger)
        check_data_quality(df_erp, "ERP", logger)
        
        # Transformar dados
        df_stock_price = transform_stock_data(df_api, logger)
        df_dim_company = create_company_dimension(df_erp, logger)
        df_dim_exchange = create_exchange_dimension(df_erp, logger)
        
        # Escrever dados
        success = True
        success &= write_parquet_data(df_stock_price, output_fact_path, "Tabela Fato Stock Price", logger)
        success &= write_parquet_data(df_dim_company, output_dim_company_path, "Dimensão Company", logger)
        success &= write_parquet_data(df_dim_exchange, output_dim_exchange_path, "Dimensão Exchange", logger)
        
        if success:
            logger.info("Pipeline de transformação concluído com sucesso!")
        else:
            logger.error("Pipeline concluído com erros")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Erro crítico no pipeline: {str(e)}")
        sys.exit(1)
        
    finally:
        # Limpar recursos
        if 'spark' in locals():
            spark.stop()
            logger.info("Sessão Spark finalizada")


if __name__ == "__main__":
    main()
