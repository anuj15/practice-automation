import os

import pandas as pd

from features.utils.config_manager import ConfigManager


class ExcelManager:
    def __init__(self, file_name: str):
        config = ConfigManager()
        self.file = os.path.join(config.test_data_path, file_name)

    def read(self, sheet_name):
        try:
            data_frame = pd.read_excel(self.file, sheet_name=sheet_name)
            return data_frame.to_dict(orient="records")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {e}") from e

    def write(self, sheet, column, row, value):
        try:
            with pd.ExcelFile(self.file) as excel_file:
                sheets = {s: excel_file.parse(s) for s in excel_file.sheet_names}
            sheets[sheet][column] = sheets[sheet][column].astype(object)
            sheets[sheet].at[row, column] = value
            with pd.ExcelWriter(self.file, engine='openpyxl') as writer:
                for s, df in sheets.items():
                    df.to_excel(writer, sheet_name=s, float_format="%2f", index=False)
            return True
        except Exception as e:
            raise Exception(f"Error writing to Excel file: {e}") from e


if __name__ == "__main__":
    excel_manager = ExcelManager("creds.xlsx")
    data = excel_manager.read("Sheet1")
    print(data)
    excel_manager.write("Sheet1", "STATUS", 1, "Passed")
