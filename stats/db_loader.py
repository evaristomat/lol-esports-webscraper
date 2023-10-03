import pandas as pd

class DatabaseLoader:
    """
    A class to load and validate data from a CSV file.
    
    Attributes
    ----------
    _filename : str
        The name of the file from which to load the data.
    _teams_data : pd.DataFrame
        A DataFrame holding the loaded teams' data.
    
    Methods
    -------
    get_data() -> pd.DataFrame:
        Returns the loaded teams' data as a DataFrame.
    
    Note
    ----
    The class checks if the file exists, if the file is not empty and if 
    the required columns ('t1', 't2', 'total_towers', 'total_dragons', 
    'total_barons', 'total_kills', 'league', 'year') are present in the file.
    If any of these conditions are not met, an appropriate error is raised.
    """
    
    def __init__(self, filename: str) -> None:
        """
        Initializes the DataLoader object with the provided filename and loads
        the data from the file.
        
        Parameters
        ----------
        filename : str
            The name of the file from which to load the data.
        
        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the file is empty or missing required columns.
        """
        self._filename = filename
        self._load_data()

    def _load_data(self) -> None:
        """
        Loads the data from the file and validates it.
        
        The method reads the data from the file into a DataFrame and checks if 
        the file is not empty and contains the required columns. If any of 
        these conditions are not met, an appropriate error is raised.
        
        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the file is empty or missing required columns.
        """
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
        """
        Returns the loaded teams' data.
        
        Returns
        -------
        pd.DataFrame
            A DataFrame holding the loaded teams' data.
        """
        return self._teams_data
