from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SUPABASE_URL: str  # இப்போ கரெக்டா URL-னு மாத்தியாச்சு மச்சா!
    SUPABASE_KEY: str

    # .env ஃபைலை ஆட்டோமேட்டிக்கா ரீட் பண்ண வைக்கும் லாஜிக்
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()