import uos


class Creds:
    CRED_FILE = "config/credentials.env"

    def __init__(
        self,
        ssid=None,
        password=None,
        ha_url=None,
        ha_token=None,
    ):
        self.ssid = ssid
        self.password = password
        self.ha_url = ha_url
        self.ha_token = ha_token

    def write(self):
        """Write credentials to CRED_FILE if valid input found."""
        if self.is_valid():
            print("writing credentials to {:s}".format(self.CRED_FILE))
            with open(self.CRED_FILE, "wb") as f:
                f.write(
                    b",".join(
                        [
                            self.ssid,
                            self.password,
                            self.ha_url,
                            self.ha_token,
                        ]
                    )
                )
            f.close()

    def load(self):
        try:
            with open(self.CRED_FILE, "rb") as f:
                contents = f.read().split(b",")
            print("Loaded WiFi credentials from {:s}".format(self.CRED_FILE))
            if len(contents) == 4:
                (
                    self.ssid,
                    self.password,
                    self.ha_url,
                    self.ha_token,
                ) = contents
            if not self.is_valid():
                self.remove()
        except OSError:
            pass

        return self

    def remove(self):
        """
        1. Delete credentials file from disk.
        2. Set ssid and password to None
        """
        print("Attempting to remove {}".format(self.CRED_FILE))
        try:
            uos.remove(self.CRED_FILE)
        except OSError:
            pass

        self.ssid = self.password = None
        self.ha_url = self.ha_token = None

    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.ssid, bytes):
            return False
        if not isinstance(self.password, bytes):
            return False
        if not isinstance(self.ha_url, bytes):
            return False
        if not isinstance(self.ha_token, bytes):
            return False

        print("validity OK")
        # Ensure credentials are not None or empty
        return all(
            (
                self.ssid,
                self.password,
                self.ha_url,
                self.ha_token,
            )
        )
