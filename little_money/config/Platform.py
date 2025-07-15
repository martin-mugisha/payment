from finance.models import SystemEarnings, PlatformSettings

class PlatformEarnings:
    def __init__(self):
        self.platform_settings = PlatformSettings.objects.first()  # Get platform fee settings

    def calculate_platform_fee(self, amount):
        if not self.platform_settings:
            return 0
        # Calculate platform fee based on the percentage set in PlatformSettings
        base_amount = amount * (self.platform_settings.platform_fee_percent / 100 if self.platform_settings else 0.01)
        return base_amount

    def get_platform_earnings(self):
        return SystemEarnings.load()  