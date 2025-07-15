from django.http import JsonResponse
from .models import Merchant, AggregatorCredentials

class MerchantAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return JsonResponse({"error": "Missing API key"}, status=401)

        # Find merchant by API key (assuming api_key is unique across merchants)
        try:
            merchant = Merchant.objects.get(api_key=api_key, is_active=True)
        except Merchant.DoesNotExist:
            return JsonResponse({"error": "Invalid API key"}, status=403)

        # Determine mode
        # Option 1: from subdomain (e.g., sandbox.example.com, live.example.com)
        host = request.get_host()
        if host.startswith("sandbox."):
            mode = "sandbox"
        elif host.startswith("live."):
            mode = "live"
        else:
            # fallback to merchant default
            mode = merchant.default_mode

        # Check merchant allowed modes
        if mode not in merchant.allowed_modes:
            return JsonResponse({"error": f"Access to {mode} mode not allowed for this merchant"}, status=403)

        # Attach merchant and mode to request
        request.merchant = merchant
        request.mode = mode

        # Optionally attach aggregator credentials for this mode
        try:
            creds = AggregatorCredentials.objects.get(merchant=merchant, mode=mode)
            request.aggregator_credentials = creds
        except AggregatorCredentials.DoesNotExist:
            return JsonResponse({"error": f"No aggregator credentials configured for {mode} mode"}, status=500)

        return self.get_response(request)
