from sqlalchemy.orm import declarative_base


Base = declarative_base()

# Import all models so that Alembic's autogenerate feature can discover them
# via Base.metadata. These imports should remain at the bottom of this module.
from app.models.user import User  # noqa: F401,E402
from app.models.specialization import Specialization  # noqa: F401,E402
from app.models.doctor import Doctor  # noqa: F401,E402
from app.models.slot import Slot  # noqa: F401,E402
from app.models.appointment import Appointment  # noqa: F401,E402
from app.models.refresh_token import RefreshToken  # noqa: F401,E402


