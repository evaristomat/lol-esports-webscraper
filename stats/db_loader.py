import pandas as pd

class DatabaseLoader:   
    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._load_data()

    def _load_data(self) -> None:
        try:
            self._teams_data = pd.read_csv(self._filename)
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self._filename} does not exist")
        except pd.errors.EmptyDataError:
            raise ValueError(f"The file {self._filename} is empty")
        
        required_columns = {'t1', 't2', 'total_towers', 'total_dragons', 'total_barons', 'total_kills', 'league', 'year'}
        if not required_columns.issubset(self._teams_data.columns):
            missing_columns = required_columns - set(self._teams_data.columns)
            raise ValueError(f"The CSV file does not have the expected columns. Missing columns: {', '.join(missing_columns)}")

    def get_data(self) -> pd.DataFrame:
        return self._teams_data
