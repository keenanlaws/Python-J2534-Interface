import platform
import winreg


class ToolRegistryInfo:
    def __init__(self):
        if platform.architecture()[0] == "32bit":
            self.REG_PATH = r"Software\\PassThruSupport.04.04\\"
        else:
            self.REG_PATH = r"Software\\Wow6432Node\\PassThruSupport.04.04\\"

        # This protocol search list is only for j2534-1
        self.protocol_list = [
            "CAN",
            "CAN channel",
            "ISO14230",
            "ISO15765",
            "ISO9141",
            "J1850PWM",
            "J1850VPW",
            "SCI_A_ENGINE",
            "SCI_A_TRANS",
            "SCI_B_ENGINE",
            "SCI_B_TRANS",
        ]

        self.tool_info = []

        self.base_key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, self.REG_PATH)
        self.count = winreg.QueryInfoKey(self.base_key)[0]

        self.tool_list = []
        self.j2534_registry_info = []

        for i in range(self.count):
            device_key = winreg.OpenKeyEx(self.base_key, winreg.EnumKey(self.base_key, i))
            name = winreg.QueryValueEx(device_key, "Name")[0]
            function_library = winreg.QueryValueEx(device_key, "FunctionLibrary")[0]
            vendor = winreg.QueryValueEx(device_key, "Vendor")[0]
            self.tool_list.append([name, function_library])
            self.tool_info.append([i, vendor, name, function_library])

            self.tool_info.extend(item for item in self.protocol_list if self.search_registry(item, device_key))

            self.j2534_registry_info.append(self.tool_info)

    @staticmethod
    def search_registry(name, key):
        try:
            value, regtype = winreg.QueryValueEx(key, name)
            return value
        except WindowsError:
            return None

    def protocol_list(self):
        for n in self.j2534_registry_info:
            print(f'Registry info = {n}')

    def dll_path(self, index_of_tool):
        try:
            return self.j2534_registry_info[index_of_tool][0][3]
        except IndexError:
            return False

    def vendor(self, index_of_tool):
        try:
            return self.j2534_registry_info[index_of_tool][0][1]
        except IndexError:
            return False

    def name(self, index_of_tool):
        try:
            return self.j2534_registry_info[index_of_tool][0][2]
        except IndexError:
            return False

    def supported_protocols(self, index_of_tool):
        try:
            return self.j2534_registry_info[index_of_tool][1:]
        except IndexError:
            return False
