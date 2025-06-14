import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class CurrencyConverter:
    """A class to handle currency conversion using external APIs."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.currencies_url = "https://api.exchangerate-api.com/v4/latest/USD"
        
        # Fallback API if the primary one fails
        self.fallback_url = "https://api.fixer.io/latest"
        
        # Common currencies if API fails to load full list
        self.default_currencies = [
            "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SEK", "NZD",
            "MXN", "SGD", "HKD", "NOK", "KRW", "TRY", "RUB", "INR", "BRL", "ZAR"
        ]
        
        self._supported_currencies = None
        self._last_currency_fetch = None
    
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies."""
        # Cache currencies for 1 hour
        if (self._supported_currencies is None or 
            self._last_currency_fetch is None or 
            datetime.now() - self._last_currency_fetch > timedelta(hours=1)):
            
            try:
                response = requests.get(self.currencies_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if "rates" in data:
                    # Include base currency (USD) and all available rates
                    currencies = ["USD"] + list(data["rates"].keys())
                    self._supported_currencies = sorted(currencies)
                    self._last_currency_fetch = datetime.now()
                else:
                    self._supported_currencies = self.default_currencies
                    
            except Exception as e:
                print(f"Error fetching currencies: {e}")
                self._supported_currencies = self.default_currencies
        
        return self._supported_currencies
    
    def convert(self, from_currency: str, to_currency: str, amount: float) -> Dict:
        """
        Convert currency from one to another.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            amount: Amount to convert
            
        Returns:
            Dictionary with conversion result and metadata
        """
        if amount <= 0:
            return {
                "success": False,
                "error": "Amount must be greater than zero"
            }
        
        if from_currency == to_currency:
            return {
                "success": True,
                "converted_amount": amount,
                "exchange_rate": 1.0,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "data_source": "Direct (same currency)"
            }
        
        # Try primary API
        result = self._convert_with_exchangerate_api(from_currency, to_currency, amount)
        if result["success"]:
            return result
        
        # Try fallback API
        result = self._convert_with_fallback_api(from_currency, to_currency, amount)
        return result
    
    def _convert_with_exchangerate_api(self, from_currency: str, to_currency: str, amount: float) -> Dict:
        """Convert using exchangerate-api.com"""
        try:
            url = f"{self.base_url}/{from_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "rates" not in data or to_currency not in data["rates"]:
                return {
                    "success": False,
                    "error": f"Exchange rate not available for {from_currency} to {to_currency}"
                }
            
            exchange_rate = data["rates"][to_currency]
            converted_amount = amount * exchange_rate
            
            return {
                "success": True,
                "converted_amount": converted_amount,
                "exchange_rate": exchange_rate,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "last_updated": data.get("date", "Unknown"),
                "data_source": "ExchangeRate-API"
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out. Please try again."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Unable to connect to currency service. Please check your internet connection."
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"API error: {e.response.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _convert_with_fallback_api(self, from_currency: str, to_currency: str, amount: float) -> Dict:
        """Convert using fallback API (fixer.io)"""
        try:
            # Note: Fixer.io requires API key for HTTPS, using HTTP for fallback
            url = f"http://data.fixer.io/api/latest?access_key={self.api_key}&base={from_currency}&symbols={to_currency}"
            
            if not self.api_key:
                # Try without API key using EUR as base (free tier limitation)
                url = "http://data.fixer.io/api/latest"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success", False):
                return {
                    "success": False,
                    "error": "Fallback API also failed"
                }
            
            rates = data.get("rates", {})
            
            # Handle conversion through EUR base
            if from_currency == "EUR":
                if to_currency not in rates:
                    return {"success": False, "error": f"Currency {to_currency} not supported"}
                exchange_rate = rates[to_currency]
            elif to_currency == "EUR":
                if from_currency not in rates:
                    return {"success": False, "error": f"Currency {from_currency} not supported"}
                exchange_rate = 1.0 / rates[from_currency]
            else:
                # Convert through EUR
                if from_currency not in rates or to_currency not in rates:
                    return {"success": False, "error": "Currency pair not supported"}
                exchange_rate = rates[to_currency] / rates[from_currency]
            
            converted_amount = amount * exchange_rate
            
            return {
                "success": True,
                "converted_amount": converted_amount,
                "exchange_rate": exchange_rate,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "last_updated": data.get("date", "Unknown"),
                "data_source": "Fixer.io (Fallback)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"All currency services are currently unavailable: {str(e)}"
            }
    
    def get_historical_rates(self, from_currency: str, to_currency: str, days: int = 7) -> Dict:
        """
        Get historical exchange rates for the past few days.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            days: Number of days to fetch (default: 7)
            
        Returns:
            Dictionary with historical rates
        """
        try:
            historical_rates = {}
            
            # Get rates for the past 'days' days
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Note: Historical data requires paid API in most services
                # This is a simplified implementation
                url = f"https://api.exchangerate-api.com/v4/history/{from_currency}/{date}"
                
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if "rates" in data and to_currency in data["rates"]:
                            historical_rates[date] = data["rates"][to_currency]
                except:
                    continue  # Skip failed requests
            
            if historical_rates:
                return {
                    "success": True,
                    "rates": historical_rates,
                    "from_currency": from_currency,
                    "to_currency": to_currency
                }
            else:
                return {
                    "success": False,
                    "error": "Historical data not available"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching historical data: {str(e)}"
            }
