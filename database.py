# Database setup
DATABASE_URL = config.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
