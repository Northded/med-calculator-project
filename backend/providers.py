from database.repository import CalculatorRepository
from deps import SessionDep


def get_repository(session: SessionDep):
    return CalculatorRepository(session=session)
