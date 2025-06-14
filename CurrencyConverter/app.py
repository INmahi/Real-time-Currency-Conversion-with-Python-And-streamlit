import streamlit as st
import os
from currency_converter import CurrencyConverter
from cache_manager import CacheManager

# Initialize the currency converter and cache manager
@st.cache_resource
def get_converter():
    """Initialize and return the currency converter instance."""
    api_key = os.getenv("EXCHANGE_API_KEY", "")
    return CurrencyConverter(api_key)

@st.cache_resource
def get_cache_manager():
    """Initialize and return the cache manager instance."""
    return CacheManager()

def main():
    st.set_page_config(
        page_title="Currency Converter",
        page_icon="💱",
        layout="wide"
    )
    
    st.title("💱 Real-Time Currency Converter")
    st.markdown("Convert currencies with real-time exchange rates")
    
    # Initialize components
    converter = get_converter()
    cache_manager = get_cache_manager()
    
    # Create columns for better layout
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.subheader("From")
        
        # Get available currencies
        currencies = converter.get_supported_currencies()
        
        if not currencies:
            st.error("Unable to load currencies. Please check your internet connection.")
            return
        
        # Handle currency swapping
        default_from = "USD"
        default_to = "EUR"
        
        if st.session_state.get('swap_requested', False):
            # Swap the defaults
            if 'last_from' in st.session_state and 'last_to' in st.session_state:
                default_from = st.session_state.last_to
                default_to = st.session_state.last_from
            st.session_state.swap_requested = False
        
        # Source currency selection
        from_currency = st.selectbox(
            "Select source currency:",
            currencies,
            index=currencies.index(default_from) if default_from in currencies else 0,
            key="from_currency"
        )
        
        # Store current selection
        st.session_state.last_from = from_currency
        
        # Amount input
        amount = st.number_input(
            "Enter amount:",
            min_value=0.01,
            value=1.00,
            step=0.01,
            format="%.2f",
            key="amount"
        )
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄", help="Swap currencies", key="swap_button"):
            # Initialize swap state if not exists
            if 'swap_requested' not in st.session_state:
                st.session_state.swap_requested = False
            
            # Toggle swap state
            st.session_state.swap_requested = not st.session_state.swap_requested
            st.rerun()
    
    with col3:
        st.subheader("To")
        
        # Target currency selection
        to_currency = st.selectbox(
            "Select target currency:",
            currencies,
            index=currencies.index(default_to) if default_to in currencies else 1,
            key="to_currency"
        )
        
        # Store current selection
        st.session_state.last_to = to_currency
    
    # Conversion section
    st.markdown("---")
    
    if from_currency and to_currency and amount > 0:
        if from_currency == to_currency:
            st.info(f"{amount:.2f} {from_currency} = {amount:.2f} {to_currency}")
        else:
            # Show loading spinner during conversion
            with st.spinner("Converting..."):
                result = converter.convert(from_currency, to_currency, amount)
            
            if result["success"]:
                converted_amount = result["converted_amount"]
                exchange_rate = result["exchange_rate"]
                
                # Display conversion result
                st.success(f"**{amount:.2f} {from_currency} = {converted_amount:.2f} {to_currency}**")
                
                # Display exchange rate info
                st.info(f"Exchange Rate: 1 {from_currency} = {exchange_rate:.6f} {to_currency}")
                
                # Display additional information
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    if result.get("last_updated"):
                        st.caption(f"Last Updated: {result['last_updated']}")
                
                with col_info2:
                    if result.get("data_source"):
                        st.caption(f"Source: {result['data_source']}")
                
                # Cache the successful conversion
                cache_manager.cache_rate(from_currency, to_currency, exchange_rate)
                
            else:
                st.error(f"Conversion failed: {result['error']}")
                
                # Try to use cached data as fallback
                cached_rate = cache_manager.get_cached_rate(from_currency, to_currency)
                if cached_rate:
                    converted_amount = amount * cached_rate
                    st.warning(f"Using cached data: {amount:.2f} {from_currency} ≈ {converted_amount:.2f} {to_currency}")
                    st.caption("⚠️ This rate may not be current due to API issues")
    
    # Historical rates section (if available)
    if st.expander("📊 Historical Information", expanded=False):
        if from_currency and to_currency and from_currency != to_currency:
            historical_data = converter.get_historical_rates(from_currency, to_currency)
            
            if historical_data.get("success") and historical_data.get("rates"):
                st.subheader(f"Recent Exchange Rates: {from_currency} → {to_currency}")
                
                # Display historical rates in a simple format
                st.subheader("Historical Rates:")
                for date, rate in sorted(historical_data["rates"].items(), reverse=True):
                    st.write(f"**{date}**: {rate:.6f} {to_currency}")
                
                # Alternative: Simple table without pandas complications
                if len(historical_data["rates"]) > 0:
                    import pandas as pd
                    rates_dict = historical_data["rates"]
                    df_data = {"Date": list(rates_dict.keys()), "Rate": list(rates_dict.values())}
                    df = pd.DataFrame(df_data)
                    df["Date"] = pd.to_datetime(df["Date"])
                    df = df.sort_values("Date", ascending=False)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Historical data not available at the moment.")
    
    # Footer with cache status
    st.markdown("---")
    cache_info = cache_manager.get_cache_info()
    st.caption(f"Cached rates: {cache_info['count']} | Last cache update: {cache_info['last_update']}")

if __name__ == "__main__":
    main()
