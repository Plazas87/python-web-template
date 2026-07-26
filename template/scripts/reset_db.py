from sqlalchemy import create_engine

from {{ package_name }}.adapters.outbound.persistence.models import Base
from {{ package_name }}.config import settings


def main() -> None:
    engine = create_engine(settings.database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
