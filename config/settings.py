import os
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv:
    load_dotenv()

# LLM Configuration
FLASH_API_KEY = os.getenv("FLASH_API_KEY")
FLASH_BASE_URL = os.getenv("FLASH_BASE_URL", None)
FLASH_MODEL = os.getenv("FLASH_MODEL")

PRO_API_KEY = os.getenv("PRO_API_KEY")
PRO_BASE_URL = os.getenv("PRO_BASE_URL", None)
PRO_MODEL = os.getenv("PRO_MODEL")

EVALUATION_API_KEY = os.getenv("EVALUATION_API_KEY")
EVALUATION_BASE_URL = os.getenv("EVALUATION_BASE_URL", None)
EVALUATION_MODEL = os.getenv("EVALUATION_MODEL")

# LiteLLM Configuration
LITELLM_MAX_TOKENS = os.getenv("LITELLM_MAX_TOKENS")
LITELLM_TEMPERATURE = os.getenv("LITELLM_TEMPERATURE")
LITELLM_TOP_P = os.getenv("LITELLM_TOP_P")
LITELLM_TOP_K = os.getenv("LITELLM_TOP_K")

if not PRO_API_KEY:
    print("Warning: PRO_API_KEY not found in .env or environment. Using a NON-FUNCTIONAL placeholder. Please create a .env file with your valid API key.")
    PRO_API_KEY = "Your API key"

# Evolutionary Algorithm Settings
POPULATION_SIZE = 5
GENERATIONS = 2
ELITISM_COUNT = 1
MUTATION_RATE = 0.7
CROSSOVER_RATE = 0.2

# Island Model Settings
NUM_ISLANDS = 4  # Number of subpopulations
MIGRATION_INTERVAL = 4  # Number of generations between migrations
ISLAND_POPULATION_SIZE = POPULATION_SIZE // NUM_ISLANDS  # Programs per island
MIN_ISLAND_SIZE = 2  # Minimum number of programs per island
MIGRATION_RATE = 0.2  # Rate at which programs migrate between islands

# Debug Settings
DEBUG = os.getenv("DEBUG", False)
EVALUATION_TIMEOUT_SECONDS = 800

DATABASE_TYPE = "in_memory"
DATABASE_PATH = "program_database.json"

# Logging Configuration
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOG_FILE = "alpha_evolve.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

API_MAX_RETRIES = 5
API_RETRY_DELAY_SECONDS = 10

RL_TRAINING_INTERVAL_GENERATIONS = 50
RL_MODEL_PATH = "rl_finetuner_model.pth"

MONITORING_DASHBOARD_URL = "http://localhost:8080"

def get_setting(key, default=None):
    """
    Retrieves a setting value.
    For LLM models, it specifically checks if the primary choice is available,
    otherwise falls back to a secondary/default if defined.
    """
    return globals().get(key, default)

def get_llm_model(model_type="pro"):
    if model_type == "pro":
        return PRO_MODEL
    elif model_type == "flash":
        return FLASH_MODEL
    return FLASH_MODEL

                                 
