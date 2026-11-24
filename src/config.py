"""
Configurações do projeto 2: Analista × Cientista × Engenheiro de Dados.

Os padrões (regex) são aplicados em texto normalizado: minúsculo e SEM acentos.
Por isso escrevemos "cientista" e não "cientísta", "engenharia" e não "engenhária".
"""

# ---------------------------------------------------------------------------
# Coleta
# ---------------------------------------------------------------------------
# Termos por cargo. As variações de nível (júnior, pleno, sênior) entram no termo
# principal em português de cada cargo, para não multiplicar demais as buscas.
TERMOS_POR_CARGO = {
    "Analista": ["analista de dados", "data analyst", "analista de BI", "business intelligence"],
    "Cientista": ["cientista de dados", "data scientist"],
    "Engenheiro": ["engenheiro de dados", "engenheira de dados", "data engineer"],
}
TERMO_PRINCIPAL = {"Analista": "analista de dados", "Cientista": "cientista de dados",
                   "Engenheiro": "engenheiro de dados"}
NIVEIS_BUSCA = ["junior", "pleno", "senior"]

PAIS_INDEED = "Brazil"
LOCAL = "Brazil"
VAGAS_POR_TERMO = 1000      # máximo que o Indeed devolve por busca
DIAS_ATRAS = 180            # pedimos 6 meses; o Indeed só devolve vagas ativas (ver README)
PAUSA_ENTRE_BUSCAS = 20     # segundos

# Dados brutos do projeto 1 (mesma fonte e mesma ferramenta). Deles, só aproveitamos
# vagas classificadas como ANALISTA: Cientista e Engenheiro vieram de buscas por
# "analista", então seriam uma amostra enviesada.
PASTA_RAW_PROJETO1 = "../skills-analista-dados/data/raw"

# Janela de análise: "auto" usa o período coberto pelos três cargos ao mesmo tempo
# (a maior entre as datas mais antigas de cada cargo). Ou fixe, ex.: "2026-08-01".
JANELA_INICIO = "auto"

# ---------------------------------------------------------------------------
# Classificação do cargo pelo TÍTULO (ordem de prioridade)
# 1. O título NOMEIA o cargo (engenheiro/a de dados, data engineer, cientista de dados,
#    data scientist) -> esse cargo. Ex.: "Cientista de Dados Sr | MLOps" -> Cientista.
# 2. Híbridos (excluídos): Analytics/ML/AI Engineer, MLOps, Arquiteto de Dados.
# 3. O título cita a ÁREA (engenharia de dados, ciência de dados) -> esse cargo.
#    A área vale mais que a palavra "Analista":
#    "Analista de Engenharia de Dados" -> Engenheiro; "Analista de Ciência de Dados" -> Cientista
# 4. Analista (regras do projeto 1)   5. Outra área
# Se o título nomeia os dois cargos, Engenheiro vem antes de Cientista.
# ---------------------------------------------------------------------------
TITULO_HIBRIDO = {
    "Analytics Engineer": r"analytics engineer|engenheir[oa]\S*(?:\s*\(a\))? de analytics|engenharia de analytics",
    "Machine Learning Engineer": r"(machine learning|\bml\b) engineer|engenheir[oa]\S*(?:\s*\(a\))? (de )?(machine learning|aprendizado de maquina|\bml\b)",
    "MLOps": r"\bmlops\b|\bml ops\b",
    "Arquiteto de Dados": r"arquitet[oa]\S* de dados|data architect|arquitetura de dados",
    "AI Engineer": r"\bai engineer|engenheir[oa]\S*(?:\s*\(a\))? de (ia|inteligencia artificial)\b",
}
TITULO_ENGENHEIRO_NOME = r"engenheir[oa]\S*(?:\s*\(a\))? (de )?dados|\beng\.? (de )?dados|data engineer|big data engineer|engenheir[oa]\S* de big data"
TITULO_CIENTISTA_NOME = r"cientista (de )?dados|data scientist"
TITULO_ENGENHEIRO_AREA = r"engenh?[ae]ria de dados|data engineering"
TITULO_CIENTISTA_AREA = r"ciencias? de dados|data science"
# Analista: mesmas regras do projeto 1
TITULO_ANALISTA_INCLUIR = r"analista|analyst|analytics|analise de dados|estagi|\bbi\b|business intel|inteligencia de negocios"
TITULO_ANALISTA_TEMA = r"dado|data|\bbi\b|business intel|analytics|inteligencia de negocios|power bi"
TITULO_OUTRA_AREA = r"desenvolvedor|developer|dba\b|arquitet|architect|engenheir|engineer|cientista|scientist"

CARGOS = ["Analista", "Cientista", "Engenheiro"]

# ---------------------------------------------------------------------------
# Senioridade (título), igual ao projeto 1
# ---------------------------------------------------------------------------
SENIORIDADE = [
    ("Estágio", r"estagi|intern\b|internship"),
    ("Júnior", r"junior|\bjr\b|\bi\b$|\bi\s*[-|(]|trainee|entry level"),
    ("Pleno", r"pleno|\bpl\b|\bii\b|mid[- ]level"),
    ("Sênior", r"senior|\bsr\b|\biii\b|especialista|specialist|lead\b|lider"),
]
SEM_SENIORIDADE = "Não informado"
MIN_VAGAS_SENIORIDADE = 50   # júnior × sênior só entra se os DOIS grupos tiverem isso

# ---------------------------------------------------------------------------
# Skills: nome -> (categoria, regex)
# As 29 primeiras vêm do projeto 1 (só "Data Warehouse" mudou, ver abaixo). Sobreposições
# conhecidas: "AWS" inclui Redshift/Athena; "GCP / BigQuery" inclui BigQuery;
# "Python" conta menções a pandas.
# ---------------------------------------------------------------------------
SKILLS = {
    # --- projeto 1 ---
    "SQL":            ("Linguagem", r"\bsql\b|t-sql|pl/sql|\bmysql\b|postgres|sql server|\boracle\b"),
    "Python":         ("Linguagem", r"\bpython\b|\bpandas\b"),
    "R":              ("Linguagem", r"\blinguagem r\b|\bpython\s*(?:e|ou|/|,)\s*r\b|\br\s*(?:e|ou|/|,)\s*python\b|\brstudio\b|\btidyverse\b"),
    "DAX":            ("Linguagem", r"\bdax\b"),
    "VBA / Macros":   ("Linguagem", r"\bvba\b|\bmacros?\b"),
    "Excel":          ("Planilha", r"\bexcel\b|planilhas? eletronicas?"),
    "Google Sheets":  ("Planilha", r"google sheets|planilhas? (?:do )?google"),
    "Power BI":       ("Visualização", r"power ?bi|\bpbi\b"),
    "Tableau":        ("Visualização", r"\btableau\b"),
    "Looker":         ("Visualização", r"\blooker\b|data studio"),
    "Qlik":           ("Visualização", r"\bqlik"),
    "AWS":            ("Cloud", r"\baws\b|amazon web services|redshift|\bathena\b"),
    "Azure":          ("Cloud", r"\bazure\b|synapse|data factory|microsoft fabric"),
    "GCP / BigQuery": ("Cloud", r"\bgcp\b|google cloud|bigquery"),
    "ETL":            ("Engenharia de dados", r"\betl\b|\belt\b"),
    # Mudança em relação ao projeto 1: lá, "Data Warehouse" também contava "data lake".
    # Aqui, data lake/lakehouse tem padrão próprio (abaixo), para não contar o mesmo conceito duas vezes.
    "Data Warehouse": ("Engenharia de dados", r"data ?warehouse|\bdw\b|\bedw\b"),
    "Modelagem de dados": ("Engenharia de dados", r"modelagem de dados|data model|modelo dimensional|star schema|modelagem dimensional"),
    "Databricks":     ("Engenharia de dados", r"databricks"),
    "Spark":          ("Engenharia de dados", r"\bspark\b|pyspark"),
    "Airflow":        ("Engenharia de dados", r"airflow"),
    "dbt":            ("Engenharia de dados", r"\bdbt\b"),
    "Git":            ("Engenharia de dados", r"\bgit\b|github|gitlab"),
    "Estatística":    ("Conceito", r"estatistic|statistic"),
    "Machine Learning": ("Ciência de dados", r"machine learning|aprendizado de maquina|\bml\b"),
    "IA Generativa":  ("Ciência de dados", r"ia generativa|genai|generative ai|\bllms?\b|chatgpt|engenharia de prompt"),
    "KPIs / Indicadores": ("Conceito", r"\bkpis?\b|indicadores"),
    "Storytelling":   ("Conceito", r"storytelling"),
    "Comunicação":    ("Comportamental", r"comunicacao|comunicativ|communication"),
    "Inglês":         ("Idioma", r"\bingles\b|\benglish\b"),
    # --- novas: engenharia ---
    "Kafka":          ("Engenharia de dados", r"\bkafka\b"),
    # Validação: "star/snowflake schema" é modelagem, não a plataforma
    "Snowflake":      ("Engenharia de dados", r"(?<!star/)(?<!star )(?<!schema, )\bsnowflake\b(?!\s*schema)"),
    "BigQuery":       ("Cloud", r"\bbig ?query\b"),
    "Redshift":       ("Cloud", r"\bredshift\b"),
    "Data Lake / Lakehouse": ("Engenharia de dados", r"data ?lake|lakehouse|delta lake"),
    "Docker":         ("DevOps", r"\bdocker\b"),
    "Kubernetes":     ("DevOps", r"\bkubernetes\b|\bk8s\b"),
    # Validação: "Azure DevOps" aparecia como ferramenta de gestão de projetos; saiu do padrão
    "CI/CD":          ("DevOps", r"\bci ?/ ?cd\b|integracao continua|entrega continua|github actions|gitlab ci|\bjenkins\b"),
    "Terraform":      ("DevOps", r"\bterraform\b"),
    "Linux":          ("DevOps", r"\blinux\b|\bunix\b|\bshell script|\bbash\b"),
    "Scala":          ("Linguagem", r"\bscala\b"),
    "Java":           ("Linguagem", r"\bjava\b(?!\s*script)"),
    # --- novas: ciência ---
    "Deep Learning":  ("Ciência de dados", r"deep learning|aprendizado profundo|redes neurais|neural networks?"),
    "scikit-learn":   ("Ciência de dados", r"scikit|sklearn"),
    "TensorFlow / PyTorch": ("Ciência de dados", r"tensorflow|pytorch|\bkeras\b"),
    "NLP":            ("Ciência de dados", r"\bnlp\b|\bpln\b|processamento de linguagem natural|natural language processing"),
    "Testes A/B":     ("Ciência de dados", r"\btestes? (?:a ?/ ?b|ab)\b|\ba ?/ ?b test|\bab test"),
    "Pandas":         ("Linguagem", r"\bpandas\b"),
}

# Regras herdadas do projeto 1
FORA_DO_GRAFICO = ["KPIs / Indicadores"]
IGNORAR_EM_FORMACAO = ["Estatística"]
PADRAO_FORMACAO = (r"ensino superior|graduacao|graduado|formacao|formado|cursando|bacharel"
                   r"|superior completo|superior em|areas? correlatas|areas? afins")

# ---------------------------------------------------------------------------
# Análises
# ---------------------------------------------------------------------------
LIMIAR_BASE_COMUM = 40      # % mínimo nos três cargos para ser "base comum"
TOP_N_PERFIL = 10
TOP_N_PONTES = 5
N_SKILLS_HEATMAP = 15

# Modelo de trabalho (lido no título, local e descrição). Na descrição inteira usamos
# padrões mais específicos, na ordem abaixo: "home office" sozinho costuma ser benefício.
MODELO_DESCRICAO = [
    ("Híbrido", r"hibrid|hybrid"),
    ("Remoto", r"100% remot|totalmente remot|trabalho remoto|modelo remoto|vaga remota|full remote|fully remote|remote first|remote-first"),
    ("Presencial", r"\bpresencial\b|on-?site"),
]
# Modelo de trabalho no título e no local
MODELO_TRABALHO = [
    ("Híbrido", r"hibrid|hybrid"),
    ("Remoto", r"remot|home ?office|anywhere|100% online|trabalho a distancia"),
    ("Presencial", r"presencial|on-?site|in loco"),
]

# Gráficos
AUTOR = "Gabriel Leonardelli"
FONTE = "Indeed Brasil"
