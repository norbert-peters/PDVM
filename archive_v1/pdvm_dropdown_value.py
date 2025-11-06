# pdvm_dropdown_value.py

class PdvmDropdownValue:
    def __init__(self, key: str = ""):
        self.key = key

    @property
    def SelectedKey(self) -> str:
        return self.key

    @SelectedKey.setter
    def SelectedKey(self, new_key: str):
        self.key = new_key
